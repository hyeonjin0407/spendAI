# api_server.py — EZ MODE (no TF/no sklearn/no pandas)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import json, csv, os, math
from datetime import datetime

app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/*": {"origins": "*"}})

THIS_FILE = Path(__file__).resolve()

# 데이터 디렉터리(없으면 생성)
DATA_DIR = (THIS_FILE.parent / "spendAI" / "xpend" / "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = DATA_DIR / "purchase_data.csv"
PREF_FILE = DATA_DIR / "user_preferences.json"

# (선택) 정적 웹 폴더가 있으면 서빙
WEB_DIR_CANDIDATES = [
    THIS_FILE.parent / "web",
    THIS_FILE.parent.parent / "my_consume_app" / "build" / "web",
    THIS_FILE.parent / "build" / "web",
]
WEB_ROOT = next((p for p in WEB_DIR_CANDIDATES if p.exists()), None)

def _sigmoid(x):
    try: return 1.0/(1.0+math.exp(-x))
    except OverflowError: return 0.0 if x < 0 else 1.0

def _heuristic_regret(payload: dict) -> float:
    price = float(payload.get("금액(원)", 0))
    mood = float(payload.get("당시 기분", 3))  # 1~5
    reason = str(payload.get("구매 이유", ""))
    category = str(payload.get("항목", ""))
    day = str(payload.get("요일", ""))
    month = int(payload.get("월", 1))
    user_type = str(payload.get("user_type", "") or "")

    z = 0.0
    z += (price - 100000.0)/100000.0 * 0.9
    z += (3.0 - mood) * 0.35
    if reason in {"즉흥 구매","스트레스 해소용","온라인 광고 보고"}: z += 0.5
    if reason in {"필요","계획된 지출","기념일 선물로"}:          z -= 0.3
    if category in {"전자제품","전자기기","의류"}:                 z += 0.2
    if category in {"식료품","생활용품"}:                          z -= 0.15
    if day in {"금요일","토요일"}:                                  z += 0.1
    if month in {11,12}:                                           z += 0.1
    if user_type == "planned_spending":                            z -= 0.1
    elif user_type in {"hobby_spender","electronics_lover"}:       z += 0.1
    return max(0.02, min(0.98, _sigmoid(z)))

def _count_rows_csv(path: Path) -> int:
    if not path.exists(): return 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return max(0, sum(1 for _ in f) - 1)

def _file_mtime_iso(path: Path):
    return datetime.utcfromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "mode": "heuristic",
        "model_loaded": True,
        "tf_available": False,
        "data_rows": _count_rows_csv(DATA_FILE),
        "data_last_write": _file_mtime_iso(DATA_FILE),
        "build": "heuristic-init"
    })

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True, silent=True) or {}
    required = ['금액(원)', '당시 기분', '항목', '구매 이유', '요일', '월']
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({'error': f"Missing field(s): {', '.join(missing)}"}), 400
    p = _heuristic_regret(data)
    return jsonify({
        "regret_probability": float(p),
        "user_type": data.get("user_type", None),
        "note": "heuristic (no-ML) result"
    })

@app.route("/save_data", methods=["POST"])
def save_data():
    data = request.get_json(force=True, silent=True) or {}
    required = ['금액(원)', '제품명', '당시 기분', '후회 여부', '구매 이유']
    extras = ['항목','요일','월','user_type']
    fieldnames = required + extras + ["timestamp"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({'error': f"Missing field(s): {', '.join(missing)}"}), 400
    is_new = not DATA_FILE.exists()
    with DATA_FILE.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if is_new: w.writeheader()
        row = {k: data.get(k) for k in fieldnames if k != "timestamp"}
        row["timestamp"] = datetime.utcnow().isoformat()
        w.writerow(row)
    return jsonify({"status": "success"})

@app.route("/get_preferences", methods=["GET"])
def get_preferences():
    if PREF_FILE.exists():
        return jsonify(json.loads(PREF_FILE.read_text(encoding="utf-8")))
    return jsonify({"계획 지출 선호":0.5,"음식 선호":0.5,"즉흥 구매 성향":0.5,"저가 선호":0.5})

@app.route("/set_preferences", methods=["POST"])
def set_preferences():
    prefs = request.get_json(force=True, silent=True) or {}
    PREF_FILE.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify({"status": "success"})

def _serve_index():
    if not WEB_ROOT:
        return jsonify({"error": "Flutter web build folder not found."}), 500
    return send_from_directory(WEB_ROOT, "index.html")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    if not WEB_ROOT:
        return jsonify({"error": "Flutter web build folder not found."}), 500
    target = (WEB_ROOT / path).resolve()
    if path and target.exists() and target.is_file() and WEB_ROOT in target.parents:
        return send_from_directory(WEB_ROOT, path)
    return _serve_index()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 61006))
    app.run(host="0.0.0.0", port=port)

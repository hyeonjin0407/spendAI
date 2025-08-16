# api_server.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import pandas as pd
import os
import json
from pathlib import Path

# ---- (옵션) TensorFlow 임포트: 실패해도 서버는 뜨도록 ----
TF_AVAILABLE = True
try:
    from tensorflow.keras.models import load_model
except Exception as _tf_err:
    TF_AVAILABLE = False

app = Flask(__name__, static_folder=None)  # static_folder는 직접 라우팅
CORS(app, resources={r"/*": {"origins": "*"}})

# -----------------------------------------
# 데이터 저장 경로: spendAI/xpend/data
# -----------------------------------------
THIS_FILE = Path(__file__).resolve()

DATA_DIR_CANDIDATES = [
    THIS_FILE.parent / "spendAI" / "xpend" / "data",
    THIS_FILE.parent.parent / "spendAI" / "xpend" / "data",
    THIS_FILE.parent.parent.parent / "spendAI" / "xpend" / "data",
]
DATA_DIR = next((p for p in DATA_DIR_CANDIDATES if p.exists()), DATA_DIR_CANDIDATES[-1])
DATA_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = (THIS_FILE.parent / "model" / "regret_model.keras").resolve()
PREP_PATH  = (THIS_FILE.parent / "model" / "preprocessor.pkl").resolve()


DATA_FILE = DATA_DIR / "purchase_data.csv"
PREF_FILE = DATA_DIR / "user_preferences.json"

# -----------------------------------------
# Flutter 웹 빌드 결과 경로(web root)
# (Render에선 보통 프론트는 따로 서빙하지만, 로컬겸용 유지)
# -----------------------------------------
WEB_DIR_CANDIDATES = [
    THIS_FILE.parent / "web",
    THIS_FILE.parent.parent / "my_consume_app" / "build" / "web",
    THIS_FILE.parent / "build" / "web",
]
WEB_ROOT = next((p for p in WEB_DIR_CANDIDATES if p.exists()), None)
if WEB_ROOT is None:
    print("[WARN] Flutter 웹 빌드 폴더를 찾지 못했습니다. (web/, ../my_consume_app/build/web, build/web 중 하나 필요)")
else:
    print(f"[INFO] Serving Flutter web from: {WEB_ROOT}")

# -----------------------------------------
# 모델 로드 (실패해도 서버는 계속 뜸)
# -----------------------------------------
model = None
preprocessor = None
try:
    if TF_AVAILABLE and MODEL_PATH.exists() and PREP_PATH.exists():
        model = load_model(str(MODEL_PATH))
        preprocessor = joblib.load(str(PREP_PATH))
        print("[INFO] Model & Preprocessor loaded.")
    else:
        if not TF_AVAILABLE:
            print("[WARN] TensorFlow not available; predict will return dummy values.")
        if not MODEL_PATH.exists():
            print(f"[WARN] MODEL_PATH not found: {MODEL_PATH}")
        if not PREP_PATH.exists():
            print(f"[WARN] PREP_PATH not found: {PREP_PATH}")
except Exception as e:
    print(f"[WARN] Failed to load model/preprocessor: {e}")

# -----------------------------------------
# Health
# -----------------------------------------
@app.route('/health', methods=['GET'])
def health():
    ok = model is not None and preprocessor is not None
    return jsonify({
        "status": "ok" if ok else "model_not_loaded",
        "model_loaded": ok,
        "tf_available": TF_AVAILABLE
    })

# -----------------------------------------
# API
# -----------------------------------------
@app.route('/predict', methods=['POST'])
def predict():
    """
    - 모델/전처리기가 없으면 더미값으로 200 응답을 반환 (배포/고정주소 확인용)
    - 나중에 실제 모델 배포 시, 아래 dummy 로직을 제거/주석처리하면 됨
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        required_fields = ['금액(원)', '당시 기분', '항목', '구매 이유', '요일', '월']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({'error': f"Missing field(s): {', '.join(missing)}"}), 400

        # ---- 모델이 준비되지 않은 경우: 더미 응답 ----
        if model is None or preprocessor is None:
            return jsonify({
                'regret_probability': 0.42,                # 임시 더미값
                'user_type': data.get('user_type', None),
                'note': 'dummy response (model not loaded on server)'
            }), 200

        # ---- 실제 추론 ----
        input_df = pd.DataFrame({k: [data[k]] for k in required_fields})
        input_processed = preprocessor.transform(input_df)
        pred_prob = model.predict(input_processed)[0][0]

        return jsonify({
            'regret_probability': float(pred_prob),
            'user_type': data.get('user_type')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/save_data', methods=['POST'])
def save_data():
    try:
        data = request.get_json(force=True, silent=True) or {}
        required_fields = ['금액(원)', '제품명', '당시 기분', '후회 여부', '구매 이유']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({'error': f"Missing field(s): {', '.join(missing)}"}), 400

        try:
            price = int(data['금액(원)'])
        except Exception:
            return jsonify({'error': '금액(원)은 정수여야 합니다.'}), 400

        record = {
            '금액(원)': price,
            '제품명': str(data['제품명']).strip(),
            '당시 기분': str(data['당시 기분']).strip(),
            '후회 여부': str(data['후회 여부']).strip(),  # '예'/'아니오'
            '구매 이유': str(data['구매 이유']).strip(),
        }

        df_new = pd.DataFrame([record])

        if DATA_FILE.exists():
            df_new.to_csv(DATA_FILE, mode='a', index=False, header=False, encoding='utf-8-sig')
        else:
            df_new.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

        return jsonify({'status': 'success', 'message': 'Data saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/get_preferences', methods=['GET'])
def get_preferences():
    try:
        if PREF_FILE.exists():
            with open(PREF_FILE, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        else:
            prefs = {
                "계획 지출 선호": 0.5,
                "음식 선호": 0.5,
                "즉흥 구매 성향": 0.5,
                "저가 선호": 0.5
            }
        return jsonify(prefs)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/set_preferences', methods=['POST'])
def set_preferences():
    try:
        prefs = request.get_json(force=True, silent=True) or {}
        with open(PREF_FILE, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# -----------------------------------------
# Flutter 정적 파일 서빙 (SPA)
# -----------------------------------------
def _serve_index():
    if WEB_ROOT is None:
        return jsonify({"error": "Flutter web build folder not found."}), 500
    return send_from_directory(WEB_ROOT, 'index.html')

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    """
    - /, /index.html → index.html
    - /assets/... 등 실제 파일 경로 존재 → 해당 파일
    - 그 외 SPA 라우팅 → index.html
    """
    if WEB_ROOT is None:
        return jsonify({"error": "Flutter web build folder not found."}), 500

    target = (WEB_ROOT / path).resolve()
    if path and target.exists() and target.is_file() and WEB_ROOT in target.parents:
        return send_from_directory(WEB_ROOT, path)

    return _serve_index()

# -----------------------------------------
# Render 배포용: PORT 환경변수 지원
# -----------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 61006))
    app.run(host='0.0.0.0', port=port)

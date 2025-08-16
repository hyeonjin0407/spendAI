import sqlite3
import os

# data 폴더 절대경로 또는 상대경로 지정
db_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(db_dir, exist_ok=True)  # data 폴더 없으면 생성

db_path = os.path.join(db_dir, 'samsung_reviews.db')

# 1. DB 연결 (없으면 생성)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 2. 테이블 생성
cursor.execute('''
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT,
    review_text TEXT,
    rating INTEGER,
    is_used INTEGER,
    is_regret INTEGER
)
''')

# 3. 샘플 데이터 삽입
sample_data = [
    ('갤럭시 S25', '제품 정말 좋아요', 5, 0, 0),
    ('갤럭시 S25', '배터리가 너무 빨리 닳아서 후회합니다', 2, 0, 1),
    ('갤럭시 S24 중고', '중고지만 상태 괜찮아요', 4, 1, 0),
]

cursor.executemany('''
INSERT INTO reviews (product_name, review_text, rating, is_used, is_regret)
VALUES (?, ?, ?, ?, ?)
''', sample_data)

conn.commit()

# 4. 데이터 조회해서 출력해보기
cursor.execute('SELECT * FROM reviews')
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()

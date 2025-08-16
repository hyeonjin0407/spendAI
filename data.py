import pandas as pd
import random
from datetime import datetime, timedelta

items = {
    '가전': [
        ('커피머신', 100000, 200000), ('헤어드라이기', 30000, 70000), ('노트북', 800000, 1500000),
        ('스마트폰', 500000, 1200000), ('블루투스 이어폰', 50000, 150000), ('전기밥솥', 40000, 120000),
        ('에어프라이어', 30000, 100000), ('TV', 700000, 2500000), ('냉장고', 1000000, 3000000)
    ],
    '식료품': [
        ('쌀', 20000, 40000), ('과일세트', 15000, 30000), ('커피원두', 10000, 25000),
        ('채소', 5000, 15000), ('간편식', 8000, 20000), ('고기', 20000, 50000),
        ('빵', 3000, 7000), ('유제품', 3000, 15000), ('음료수', 1000, 5000)
    ],
    '의류': [
        ('티셔츠', 10000, 30000), ('운동화', 50000, 120000), ('청바지', 40000, 80000),
        ('자켓', 60000, 150000), ('모자', 10000, 30000), ('양말', 2000, 8000),
        ('코트', 100000, 300000), ('스웨터', 30000, 70000)
    ],
    '취미': [
        ('책', 10000, 30000), ('게임', 30000, 70000), ('캠핑용품', 50000, 150000),
        ('악기', 100000, 500000), ('퍼즐', 15000, 40000), ('보드게임', 20000, 60000),
        ('그림도구', 10000, 50000)
    ],
    '외식': [
        ('커피', 4000, 7000), ('점심식사', 7000, 15000), ('저녁식사', 15000, 40000),
        ('디저트', 3000, 10000), ('술', 8000, 25000), ('패스트푸드', 5000, 12000)
    ],
    '교통': [
        ('택시', 5000, 20000), ('지하철', 1250, 2000), ('버스', 1200, 2000),
        ('기차', 10000, 50000), ('비행기', 50000, 300000)
    ],
    '생활용품': [
        ('세제', 5000, 15000), ('화장지', 3000, 10000), ('칫솔', 1000, 5000),
        ('샴푸', 7000, 20000), ('바디워시', 7000, 20000), ('청소도구', 10000, 40000)
    ],
    '전자기기': [
        ('USB 케이블', 5000, 20000), ('외장하드', 50000, 150000), ('모니터', 150000, 400000),
        ('키보드', 30000, 100000), ('마우스', 20000, 70000)
    ]
}

purchase_reasons = [
    "필요해서", "기념일 선물로", "스트레스 해소용", "친구 추천으로", "가격이 좋아서",
    "평소에 사고 싶었음", "새로운 취미 시작해서", "계획된 지출", "즉흥 구매", "온라인 광고 보고",
    "리뷰가 좋아서", "한정판이라서", "무료 배송 이벤트", "한동안 고민하다가", "친구와 함께 구매"
]

memos = [
    "", "사이즈가 조금 작음", "품질에 만족", "다음에는 다른 브랜드 구매 예정",
    "배송이 늦었음", "재구매 의사 있음", "가격 대비 만족도 높음", "생각보다 무거움",
    "포장이 깔끔했음", "사용법이 어려움", "내구성이 약함", "디자인이 마음에 듦"
]

def generate_random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def generate_data(num_records=10000):
    data = []
    start_date = datetime.now() - timedelta(days=365 * 2)  # 최근 2년 데이터
    end_date = datetime.now()

    for _ in range(num_records):
        category = random.choice(list(items.keys()))
        item, price_min, price_max = random.choice(items[category])
        price = random.randint(price_min, price_max)

        purchase_reason = random.choice(purchase_reasons)
        memo = random.choice(memos)

        date = generate_random_date(start_date, end_date).strftime('%Y-%m-%d')

        # 당시 기분 1~5 (평균 3, 정규분포 유사)
        mood = max(1, min(5, int(random.gauss(3, 1))))

        # 후회 확률 계산 (기분 낮고 고가일수록 후회 확률 증가, 구매 이유별 가중치 적용)
        base_regret_prob = 0.1
        if mood <= 2:
            base_regret_prob += 0.3
        if price > (price_min + price_max) / 2:
            base_regret_prob += 0.3
        
        reason_weights = {
            "필요해서": -0.05,
            "기념일 선물로": 0.05,
            "스트레스 해소용": 0.1,
            "친구 추천으로": 0,
            "가격이 좋아서": -0.02,
            "평소에 사고 싶었음": 0.05,
            "새로운 취미 시작해서": 0.1,
            "계획된 지출": -0.1,
            "즉흥 구매": 0.15,
            "온라인 광고 보고": 0.1,
            "리뷰가 좋아서": -0.02,
            "한정판이라서": 0.05,
            "무료 배송 이벤트": -0.05,
            "한동안 고민하다가": -0.1,
            "친구와 함께 구매": 0
        }
        base_regret_prob += reason_weights.get(purchase_reason, 0)

        regret_prob = min(max(base_regret_prob, 0), 1)
        regret = 1 if random.random() < regret_prob else 0

        data.append({
            '날짜': date,
            '항목': item,
            '금액(원)': price,
            '구매 이유': purchase_reason,
            '당시 기분': mood,
            '현재 후회 여부': regret,
            '메모': memo
        })

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df = generate_data(10000)
    df.to_csv('../data/virtual_purchase_data.csv', index=False, encoding='utf-8-sig')
    print("가상 데이터 10,000건 생성 완료 - ../data/virtual_purchase_data.csv 저장됨")

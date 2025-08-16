import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.metrics import accuracy_score, f1_score, classification_report
import joblib

# 1. 데이터 불러오기
csv_path = '../data/virtual_purchase_data.csv'
df = pd.read_csv(csv_path, encoding='utf-8-sig')

# 2. 데이터 전처리 준비
df['날짜'] = pd.to_datetime(df['날짜'])
df['요일'] = df['날짜'].dt.day_name()
df['월'] = df['날짜'].dt.month

# 특성 컬럼 분리
feature_cols = ['금액(원)', '당시 기분', '항목', '구매 이유', '요일', '월']
X = df[feature_cols]
y = df['현재 후회 여부']

# 수치형과 범주형 컬럼 분리
numeric_features = ['금액(원)', '월']
categorical_features = ['당시 기분', '항목', '구매 이유', '요일']

# 3. 전처리 파이프라인 구성
numeric_transformer = StandardScaler()
categorical_transformer = OneHotEncoder(drop='first', handle_unknown='ignore')

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# 4. 데이터 분리 및 전처리 적용
X_train_raw, X_val_raw, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

X_train = preprocessor.fit_transform(X_train_raw)
X_val = preprocessor.transform(X_val_raw)

# 5. 모델 정의
model = Sequential([
    Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    Dropout(0.3),
    Dense(64, activation='relu'),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

# 6. 학습
model.fit(
    X_train, y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

# 7. 평가
y_pred_prob = model.predict(X_val).flatten()
y_pred = (y_pred_prob >= 0.5).astype(int)

acc = accuracy_score(y_val, y_pred)
f1 = f1_score(y_val, y_pred)
report = classification_report(y_val, y_pred)

print(f"검증 정확도: {acc:.4f}")
print(f"검증 F1-score: {f1:.4f}")
print("분류 보고서:")
print(report)

# 8. 모델과 전처리기 저장
model.save('../model/regret_model.keras')
joblib.dump(preprocessor, '../model/preprocessor.pkl')

print("모델과 전처리기가 저장되었습니다.")

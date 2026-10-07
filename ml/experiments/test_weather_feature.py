"""
Thu nghiem: so sanh do chinh xac model du bao gia lua gao KHI CO va KHONG
CO feature thoi tiet (nhiet do, luong mua vung DBSCL), de xem them thoi
tiet co thuc su cai thien du bao hay khong.

Day la script THU NGHIEM, khong thay the ml/models/train_baseline.py -
neu ket qua tot thi moi tinh chuyen tich hop chinh thuc vao pipeline.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))
sys.path.append(str(BASE_DIR / "backend"))

from build_features import load_price_data, build_features
from app.db.session import SessionLocal
from app.models.tables import WeatherData

BASE_FEATURES = ["lag_1", "rolling_mean_3", "day_of_week"]
WEATHER_FEATURES = ["rainfall_mm", "temperature_avg"]
TARGET_COLUMN = "target"
TEST_SIZE_RATIO = 0.2

MODELS = {
    "Linear Regression": lambda: LinearRegression(),
    "Random Forest": lambda: RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost": lambda: XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
}


def load_weather_data(region: str = "Dong bang song Cuu Long") -> pd.DataFrame:
    session = SessionLocal()
    try:
        rows = (
            session.query(
                WeatherData.weather_date,
                WeatherData.rainfall_mm,
                WeatherData.temperature_avg,
            )
            .filter(WeatherData.region == region)
            .order_by(WeatherData.weather_date)
            .all()
        )
    finally:
        session.close()

    df = pd.DataFrame(rows, columns=["weather_date", "rainfall_mm", "temperature_avg"])
    if df.empty:
        return df
    df["weather_date"] = pd.to_datetime(df["weather_date"])
    df["rainfall_mm"] = df["rainfall_mm"].astype(float)
    df["temperature_avg"] = df["temperature_avg"].astype(float)
    return df


def add_weather_features(df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """Gan them cot thoi tiet theo dung ngay. Ngay nao thieu du lieu thoi
    tiet (do NASA xu ly tre) thi lay tam gia tri gan nhat truoc do (ffill)."""
    merged = df.merge(weather_df, left_on="price_date", right_on="weather_date", how="left")
    merged = merged.drop(columns=["weather_date"])
    merged[WEATHER_FEATURES] = merged.groupby("category")[WEATHER_FEATURES].transform(
        lambda s: s.ffill().bfill()
    )
    return merged


def train_test_split_by_time(df: pd.DataFrame, test_ratio: float):
    train_frames, test_frames = [], []
    for category, group in df.groupby("category"):
        group = group.sort_values("price_date").reset_index(drop=True)
        n_test = max(1, int(len(group) * test_ratio))
        if len(group) <= n_test:
            train_frames.append(group)
            continue
        train_frames.append(group.iloc[:-n_test])
        test_frames.append(group.iloc[-n_test:])

    train_df = pd.concat(train_frames, ignore_index=True) if train_frames else pd.DataFrame()
    test_df = pd.concat(test_frames, ignore_index=True) if test_frames else pd.DataFrame()
    return train_df, test_df


def compute_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape}


def run_experiment(df: pd.DataFrame, feature_columns: list[str], label: str):
    train_df, test_df = train_test_split_by_time(df, TEST_SIZE_RATIO)
    if train_df.empty or test_df.empty:
        print(f"  [{label}] Khong du du lieu de chia train/test, bo qua.")
        return

    X_train, y_train = train_df[feature_columns], train_df[TARGET_COLUMN]
    X_test, y_test = test_df[feature_columns], test_df[TARGET_COLUMN]

    print(f"\n--- {label} (feature: {feature_columns}) ---")
    for name, build_model in MODELS.items():
        model = build_model()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        m = compute_metrics(y_test, preds)
        print(f"  {name:<18} MAE={m['MAE']:.2f}  RMSE={m['RMSE']:.2f}  MAPE={m['MAPE']:.2f}%")


def main():
    print("Dang lay du lieu gia lua gao...")
    price_df = load_price_data(crop_type="rice")
    if price_df.empty:
        print("Khong co du lieu gia lua gao.")
        return

    features = build_features(price_df)
    print(f"So dong feature (sau khi bo dong dau thieu lag_1): {len(features)}")

    print("\nDang lay du lieu thoi tiet...")
    weather_df = load_weather_data()
    if weather_df.empty:
        print("Chua co du lieu thoi tiet trong CSDL - chay fetch_weather_data.py truoc.")
        return
    print(f"So ngay co du lieu thoi tiet: {len(weather_df)}")

    features_with_weather = add_weather_features(features, weather_df)
    rows_before = len(features_with_weather)
    features_with_weather = features_with_weather.dropna(subset=WEATHER_FEATURES)
    rows_after = len(features_with_weather)
    if rows_after < rows_before:
        print(f"Luu y: bo {rows_before - rows_after} dong khong co du lieu thoi tiet du dung (ngay qua xa khong noi suy duoc).")

    print("\n================ SO SANH KET QUA ================")
    run_experiment(features, BASE_FEATURES, "KHONG co thoi tiet (baseline hien tai)")
    run_experiment(features_with_weather, BASE_FEATURES + WEATHER_FEATURES, "CO them thoi tiet")


if __name__ == "__main__":
    main()
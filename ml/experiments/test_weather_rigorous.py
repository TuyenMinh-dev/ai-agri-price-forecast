"""
Test thoi tiet CHUAN HON bang walk-forward backtest (nhieu luot kiem tra noi
tiep nhau theo thoi gian), thay vi chi cat 1 lan duy nhat nhu truoc - giam
nhieu do du lieu it/an may gay ra, cho ket qua dang tin cay hon.

Cach lam: voi moi loai gao, chia thanh nhieu "fold" lien tiep - fold sau
luon dung nhieu du lieu hon fold truoc de train (expanding window), moi
fold du doan truc tiep (khong de quy nhieu buoc) vai ngay ke tiep da biet
truoc dap an that, de tap trung danh gia dung cau hoi "them thoi tiet co
giup khong", khong tron voi yeu to "du bao xa bao nhieu ngay".

Chay o cung thu muc voi build_features.py (qua ml/features) va can
fetch_weather_data.py da chay truoc do de co du lieu trong bang weather_data.
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
ALL_FEATURES = BASE_FEATURES + WEATHER_FEATURES
TARGET_COLUMN = "target"

MIN_FOLDS = 3          # it nhat 3 fold moi coi la du tin cay de ket luan
MAX_STALE_DAYS = 3     # loai gao nao du lieu khong co ngay nao trong N ngay
                        # gan nhat (so voi ngay cuoi cua chinh no) thi coi la
                        # con bi dut quang nhieu, van test nhung se canh bao

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
    merged = df.merge(weather_df, left_on="price_date", right_on="weather_date", how="left")
    merged = merged.drop(columns=["weather_date"])
    merged[WEATHER_FEATURES] = merged[WEATHER_FEATURES].ffill().bfill()
    return merged


def make_folds(n_rows: int):
    """Chia thanh cac fold kieu 'expanding window': fold sau luon dung
    nhieu du lieu train hon fold truoc. Tra ve list (train_end, test_end)."""
    fold_size = max(2, n_rows // 7)
    min_train = max(5, fold_size)

    folds = []
    cutoff = min_train
    while cutoff + fold_size <= n_rows:
        folds.append((cutoff, cutoff + fold_size))
        cutoff += fold_size
    return folds


def run_category(category: str, group: pd.DataFrame, weather_df: pd.DataFrame):
    group = group.sort_values("price_date").reset_index(drop=True)
    merged = add_weather_features(group, weather_df)

    features = build_features(merged)
    if features[WEATHER_FEATURES].isna().any().any():
        print(f"\n=== {category} ===\n  Thieu du lieu thoi tiet mot so ngay, bo qua de tranh so sanh sai lech.")
        return

    n = len(features)
    folds = make_folds(n)
    if len(folds) < MIN_FOLDS:
        print(
            f"\n=== {category} ===\n  Chua du du lieu de chay walk-forward chuan "
            f"(co {n} dong, chi chia duoc {len(folds)} fold, can it nhat {MIN_FOLDS}). Bo qua."
        )
        return

    print(f"\n=== {category} ({n} dong, chay {len(folds)} fold walk-forward) ===")

    for name, build_model in MODELS.items():
        mae_plain_list = []
        mae_weather_list = []
        wins_weather = 0

        for train_end, test_end in folds:
            train = features.iloc[:train_end]
            test = features.iloc[train_end:test_end]

            model_plain = build_model()
            model_plain.fit(train[BASE_FEATURES], train[TARGET_COLUMN])
            pred_plain = model_plain.predict(test[BASE_FEATURES])
            mae_plain = np.mean(np.abs(pred_plain - test[TARGET_COLUMN].to_numpy()))

            model_weather = build_model()
            model_weather.fit(train[ALL_FEATURES], train[TARGET_COLUMN])
            pred_weather = model_weather.predict(test[ALL_FEATURES])
            mae_weather = np.mean(np.abs(pred_weather - test[TARGET_COLUMN].to_numpy()))

            mae_plain_list.append(mae_plain)
            mae_weather_list.append(mae_weather)
            if mae_weather < mae_plain:
                wins_weather += 1

        avg_plain = np.mean(mae_plain_list)
        avg_weather = np.mean(mae_weather_list)
        change_pct = (avg_weather - avg_plain) / avg_plain * 100 if avg_plain else float("nan")
        verdict = "THOI TIET TOT HON" if avg_weather < avg_plain else "KHONG thoi tiet tot hon"

        print(f"  {name}:")
        print(f"    MAE trung binh KHONG thoi tiet : {avg_plain:,.2f}")
        print(f"    MAE trung binh CO thoi tiet     : {avg_weather:,.2f}  ({change_pct:+.1f}%)")
        print(f"    So fold thoi tiet thang         : {wins_weather}/{len(folds)}")
        print(f"    => {verdict}")


def main():
    print("Dang lay du lieu gia lua gao va thoi tiet...")
    df = load_price_data(crop_type="rice")
    weather_df = load_weather_data()
    if df.empty or weather_df.empty:
        print("Thieu du lieu gia hoac thoi tiet, kiem tra lai CSDL.")
        return

    print("Chay walk-forward backtest (nhieu fold) de so sanh CO vs KHONG thoi tiet.")
    print(f"(Fold = 1 lan train-roi-test, cang nhieu fold cang do tin cay, toi thieu {MIN_FOLDS} fold moi ket luan)")

    for category, group in df.groupby("category"):
        run_category(category, group, weather_df)


if __name__ == "__main__":
    main()
"""
Thu nghiem: mo rong tam du bao tu 1 NGAY len 7 NGAY toi (1 tuan), dung
cach du bao de quy (recursive forecasting) - lay ket qua du doan ngay
truoc lam input de du doan ngay sau, lap lai 7 lan.

Co backtest: giau di 7 ngay cuoi cung THAT, train bang du lieu con lai,
du doan de quy 7 ngay, roi so sanh voi 7 ngay that da giau - de thay ro
sai so tang dan qua tung ngay xa dan, khong chi mot con so mo ho.

Day la script THU NGHIEM, khong thay the ml/models/generate_forecast.py -
neu ket qua on thi moi tinh chuyen tich hop chinh thuc.
"""

import sys
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))
sys.path.append(str(BASE_DIR / "backend"))

from build_features import load_price_data, build_features

FEATURE_COLUMNS = ["lag_1", "rolling_mean_3", "day_of_week"]
TARGET_COLUMN = "target"
HORIZON_DAYS = 7  # doi so nay neu muon thu tam xa khac (vd 3, 14)
MIN_ROWS_NEEDED = HORIZON_DAYS + 5  # can it nhat vai dong de train truoc khi test

MODELS = {
    "Linear Regression": lambda: LinearRegression(),
    "Random Forest": lambda: RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost": lambda: XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
}


def recursive_forecast(model, history_prices: list, history_dates: list, horizon: int) -> list:
    """Du bao de quy: moi buoc dung chinh gia du doan truoc do lam input."""
    prices = list(history_prices)
    dates = list(history_dates)
    preds = []
    for _ in range(horizon):
        next_date = dates[-1] + pd.Timedelta(days=1)
        last3 = prices[-3:]
        row = pd.DataFrame(
            [
                {
                    "lag_1": prices[-1],
                    "rolling_mean_3": sum(last3) / len(last3),
                    "day_of_week": next_date.dayofweek,
                }
            ]
        )
        pred = float(model.predict(row[FEATURE_COLUMNS])[0])
        preds.append(pred)
        prices.append(pred)
        dates.append(next_date)
    return preds


def evaluate_category(category: str, group: pd.DataFrame, horizon: int):
    group = group.sort_values("price_date").reset_index(drop=True)
    if len(group) < MIN_ROWS_NEEDED:
        print(
            f"\n=== {category} ===\n"
            f"  Chua du du lieu de kiem chung du bao {horizon} ngay "
            f"(co {len(group)} dong, can it nhat {MIN_ROWS_NEEDED}), bo qua."
        )
        return

    cutoff = len(group) - horizon
    train_part = group.iloc[:cutoff]
    actual_future = group.iloc[cutoff:]["price_avg"].tolist()
    actual_dates = group.iloc[cutoff:]["price_date"].tolist()

    train_features = build_features(train_part)
    if train_features.empty:
        print(f"\n=== {category} ===\n  Khong du du lieu de train sau khi tao feature, bo qua.")
        return

    X_train = train_features[FEATURE_COLUMNS]
    y_train = train_features[TARGET_COLUMN]
    history_prices = train_part["price_avg"].tolist()
    history_dates = list(train_part["price_date"])

    print(f"\n=== {category} (train {len(train_part)} dong, kiem chung {horizon} ngay cuoi) ===")
    for name, build_model in MODELS.items():
        model = build_model()
        model.fit(X_train, y_train)
        preds = recursive_forecast(model, history_prices, history_dates, horizon)

        print(f"  {name}:")
        for h, (d, p, a) in enumerate(zip(actual_dates, preds, actual_future), start=1):
            err = abs(p - a)
            err_pct = (err / a * 100) if a else 0
            print(
                f"    Ngay +{h} ({d.date()}): du doan={p:,.2f}  thuc te={a:,.2f}  "
                f"sai so={err:,.2f} ({err_pct:.1f}%)"
            )


def main():
    print("Dang lay du lieu gia lua gao...")
    df = load_price_data(crop_type="rice")
    if df.empty:
        print("Khong co du lieu gia lua gao.")
        return

    print(f"Thu nghiem du bao de quy {HORIZON_DAYS} ngay toi, co kiem chung bang du lieu that da giau di.")
    for category, group in df.groupby("category"):
        evaluate_category(category, group, HORIZON_DAYS)


if __name__ == "__main__":
    main()
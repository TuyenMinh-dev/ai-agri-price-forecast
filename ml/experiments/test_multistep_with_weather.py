"""
Thu nghiem GOP: du bao de quy 7 ngay toi, so sanh truc tiep CO va KHONG CO
feature thoi tiet, tren cung 1 lan backtest (giau 7 ngay cuoi that, dung
dung thoi tiet THAT cua 7 ngay do - vi la backtest nen da biet thoi tiet
that su da xay ra, khong phai du bao thoi tiet).

Co hien thi them KHOANG GIA THAT (price_min - price_max) canh ket qua du
doan, de de danh gia hon la chi nhin 1 con so trung binh don le.

QUAN TRONG: cach lam nay chi dung cho MUC DICH SO SANH/BACKTEST. Neu sau
nay muon ap dung that cho du bao 7 ngay TUONG LAI (chua biet), se can
them 1 nguon DU BAO thoi tiet rieng (NASA POWER chi co du lieu da xay ra,
khong du bao).

Chay o cung thu muc voi test_multistep_forecast.py va test_weather_feature.py
(tai su dung ham tu 2 file do, khong viet lai).
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))

from test_multistep_forecast import (
    load_price_data,
    build_features,
    FEATURE_COLUMNS,
    HORIZON_DAYS,
    MIN_ROWS_NEEDED,
    MODELS,
)
from test_weather_feature import load_weather_data, add_weather_features, WEATHER_FEATURES

# Tai su dung ket noi CSDL da co san (qua test_multistep_forecast -> build_features
# da tu dong them backend/ vao sys.path roi, nen import duoc thang nhu sau)
from app.db.session import SessionLocal
from app.models.tables import Product, MarketPrice

ALL_FEATURE_COLUMNS = FEATURE_COLUMNS + WEATHER_FEATURES


def load_price_range(crop_type: str = "rice") -> pd.DataFrame:
    """Lay khoang gia THAT (min-max) theo tung ngay, dung de hien thi canh
    ket qua du doan - khong dung de train, chi de doi chieu truc quan hon."""
    session = SessionLocal()
    try:
        rows = (
            session.query(
                Product.category,
                MarketPrice.price_date,
                MarketPrice.price_min,
                MarketPrice.price_max,
            )
            .join(Product, Product.id == MarketPrice.product_id)
            .filter(Product.crop_type == crop_type)
            .all()
        )
    finally:
        session.close()

    df = pd.DataFrame(rows, columns=["category", "price_date", "price_min", "price_max"])
    if df.empty:
        return df
    df["price_date"] = pd.to_datetime(df["price_date"])
    df["price_min"] = df["price_min"].astype(float)
    df["price_max"] = df["price_max"].astype(float)
    return df


def recursive_forecast_plain(model, history_prices, history_dates, horizon):
    prices, dates, preds = list(history_prices), list(history_dates), []
    for _ in range(horizon):
        next_date = dates[-1] + pd.Timedelta(days=1)
        last3 = prices[-3:]
        row = pd.DataFrame(
            [{"lag_1": prices[-1], "rolling_mean_3": sum(last3) / len(last3), "day_of_week": next_date.dayofweek}]
        )
        pred = float(model.predict(row[FEATURE_COLUMNS])[0])
        preds.append(pred)
        prices.append(pred)
        dates.append(next_date)
    return preds


def recursive_forecast_weather(model, history_prices, history_dates, future_weather_rows, horizon):
    prices, dates, preds = list(history_prices), list(history_dates), []
    for i in range(horizon):
        next_date = dates[-1] + pd.Timedelta(days=1)
        last3 = prices[-3:]
        w = future_weather_rows[i]
        row = pd.DataFrame(
            [
                {
                    "lag_1": prices[-1],
                    "rolling_mean_3": sum(last3) / len(last3),
                    "day_of_week": next_date.dayofweek,
                    "rainfall_mm": w["rainfall_mm"],
                    "temperature_avg": w["temperature_avg"],
                }
            ]
        )
        pred = float(model.predict(row[ALL_FEATURE_COLUMNS])[0])
        preds.append(pred)
        prices.append(pred)
        dates.append(next_date)
    return preds


def evaluate_category(category: str, group: pd.DataFrame, weather_df: pd.DataFrame, price_range_df: pd.DataFrame, horizon: int):
    group = group.sort_values("price_date").reset_index(drop=True)
    if len(group) < MIN_ROWS_NEEDED:
        print(f"\n=== {category} ===\n  Chua du du lieu (co {len(group)} dong, can it nhat {MIN_ROWS_NEEDED}), bo qua.")
        return

    group_weather = add_weather_features(group, weather_df)
    if group_weather[WEATHER_FEATURES].isna().any().any():
        print(f"\n=== {category} ===\n  Thieu du lieu thoi tiet cho mot so ngay, bo qua de tranh so sanh sai lech.")
        return

    cutoff = len(group) - horizon
    train_part = group_weather.iloc[:cutoff]
    test_part = group_weather.iloc[cutoff:]
    actual_future = test_part["price_avg"].tolist()
    actual_dates = test_part["price_date"].tolist()
    future_weather_rows = test_part[WEATHER_FEATURES].to_dict("records")

    # Lay khoang gia that (min-max) cho dung cac ngay dang kiem chung
    range_lookup = {}
    if not price_range_df.empty:
        cat_range = price_range_df[price_range_df["category"] == category]
        for _, r in cat_range.iterrows():
            range_lookup[r["price_date"]] = (r["price_min"], r["price_max"])

    train_features = build_features(train_part)
    if train_features.empty:
        print(f"\n=== {category} ===\n  Khong du du lieu de train, bo qua.")
        return

    history_prices = train_part["price_avg"].tolist()
    history_dates = list(train_part["price_date"])

    print(f"\n=== {category} (train {len(train_part)} dong, kiem chung {horizon} ngay cuoi) ===")
    for name, build_model in MODELS.items():
        model_plain = build_model()
        model_plain.fit(train_features[FEATURE_COLUMNS], train_features["target"])
        preds_plain = recursive_forecast_plain(model_plain, history_prices, history_dates, horizon)

        model_weather = build_model()
        model_weather.fit(train_features[ALL_FEATURE_COLUMNS], train_features["target"])
        preds_weather = recursive_forecast_weather(model_weather, history_prices, history_dates, future_weather_rows, horizon)

        print(f"  {name}:")
        for h, (d, a, p1, p2) in enumerate(zip(actual_dates, actual_future, preds_plain, preds_weather), start=1):
            err1 = abs(p1 - a)
            err2 = abs(p2 - a)
            better = "co thoi tiet TOT HON" if err2 < err1 else ("KHONG thoi tiet TOT HON" if err1 < err2 else "bang nhau")

            range_str = ""
            rng = range_lookup.get(d)
            if rng:
                pmin, pmax = rng
                in_range_plain = "trong khoang" if pmin <= p1 <= pmax else "NGOAI khoang"
                in_range_weather = "trong khoang" if pmin <= p2 <= pmax else "NGOAI khoang"
                range_str = f" | khoang that=[{pmin:,.0f}-{pmax:,.0f}] (khong-TT {in_range_plain}, co-TT {in_range_weather})"

            print(
                f"    +{h} ({d.date()}): thuc te(tb)={a:,.2f} | "
                f"khong-TT={p1:,.2f} (sai {err1:,.2f}) | "
                f"co-TT={p2:,.2f} (sai {err2:,.2f}) -> {better}{range_str}"
            )


def main():
    print("Dang lay du lieu gia lua gao, khoang gia that va thoi tiet...")
    df = load_price_data(crop_type="rice")
    price_range_df = load_price_range(crop_type="rice")
    weather_df = load_weather_data()
    if df.empty or weather_df.empty:
        print("Thieu du lieu gia hoac thoi tiet, kiem tra lai CSDL.")
        return

    print(f"So sanh du bao de quy {HORIZON_DAYS} ngay: CO vs KHONG thoi tiet, co doi chieu khoang gia that.")
    for category, group in df.groupby("category"):
        evaluate_category(category, group, weather_df, price_range_df, HORIZON_DAYS)


if __name__ == "__main__":
    main()
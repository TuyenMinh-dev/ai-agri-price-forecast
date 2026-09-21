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
from app.db.session import SessionLocal
from app.models.tables import Forecast

FEATURE_COLUMNS = ["lag_1", "rolling_mean_3", "day_of_week"]
TARGET_COLUMN = "target"

# Moi lan chay tao model moi (khong luu .pkl) - du du lieu con it, train lai
# vai giay la xong, chua can toi uu luu/load model luc nay.
MODEL_BUILDERS = {
    "Linear Regression": lambda: LinearRegression(),
    "Random Forest": lambda: RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost": lambda: XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
}


def build_next_day_row(group: pd.DataFrame) -> dict:
    """Tao 1 dong feature de du doan gia ngay ke tiep, dua tren toi da 3 gia gan nhat."""
    group = group.sort_values("price_date")
    last_prices = group["price_avg"].tail(3).tolist()
    forecast_date = group["price_date"].max() + pd.Timedelta(days=1)

    return {
        "lag_1": last_prices[-1],
        "rolling_mean_3": sum(last_prices) / len(last_prices),
        "day_of_week": forecast_date.dayofweek,
        "forecast_date": forecast_date.date(),
    }


def forecast_category(product_id: int, group: pd.DataFrame, features: pd.DataFrame) -> list[dict]:
    """Train 3 model bang TOAN BO du lieu cua 1 category, du doan gia ngay mai."""
    cat_features = features[features["product_id"] == product_id]
    if cat_features.empty:
        return []

    X_train = cat_features[FEATURE_COLUMNS]
    y_train = cat_features[TARGET_COLUMN]

    next_row = build_next_day_row(group)
    X_pred = pd.DataFrame([{k: next_row[k] for k in FEATURE_COLUMNS}])

    results = []
    for model_name, build_model in MODEL_BUILDERS.items():
        model = build_model()
        model.fit(X_train, y_train)
        predicted_price = float(model.predict(X_pred)[0])
        results.append(
            {
                "product_id": product_id,
                "forecast_date": next_row["forecast_date"],
                "predicted_price": round(predicted_price, 2),
                "model_name": model_name,
            }
        )
    return results


def save_forecasts(session, forecasts: list[dict]) -> int:
    """Luu vao bang forecasts - neu da co du bao cung ngay + cung model cho
    product do thi cap nhat lai gia, khong tao ban ghi trung."""
    for f in forecasts:
        existing = (
            session.query(Forecast)
            .filter_by(
                product_id=f["product_id"],
                forecast_date=f["forecast_date"],
                model_name=f["model_name"],
            )
            .first()
        )
        if existing:
            existing.predicted_price = f["predicted_price"]
        else:
            session.add(Forecast(**f))
    return len(forecasts)


def main():
    print("Dang lay du lieu gia lua gao tu CSDL...")
    df = load_price_data(crop_type="rice")
    if df.empty:
        print("Khong co du lieu gia lua gao trong CSDL. Hay chay crawler va "
              "load_crawler_data.py truoc.")
        return

    features = build_features(df)

    session = SessionLocal()
    try:
        all_forecasts = []
        for product_id, group in df.groupby("product_id"):
            category = group["category"].iloc[0]
            cat_forecasts = forecast_category(product_id, group, features)

            if not cat_forecasts:
                print(f"  Bo qua {category}: chua du du lieu de train (can >= 2 dong sau khi tao feature).")
                continue

            for f in cat_forecasts:
                print(
                    f"  {category:<12} | {f['model_name']:<18} | "
                    f"{f['forecast_date']} -> {f['predicted_price']:.2f} VND/kg"
                )
            all_forecasts.extend(cat_forecasts)

        saved = save_forecasts(session, all_forecasts)
        session.commit()
        print(f"\nHoan tat. Da luu/cap nhat {saved} dong du bao vao bang forecasts.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
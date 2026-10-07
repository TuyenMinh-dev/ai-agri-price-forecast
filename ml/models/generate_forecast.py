import sys
from datetime import date, timedelta
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


def steps_needed_to_reach_tomorrow(last_known_date) -> int:
    """Tinh so buoc du bao can thiet de 'bat kip' dung ngay mai THAT (theo
    dong ho may), khong chi dua vao ngay du lieu moi nhat dang co.

    """
    last_date = last_known_date.date() if hasattr(last_known_date, "date") else last_known_date
    target_date = date.today() + timedelta(days=1)
    steps = (target_date - last_date).days
    return max(steps, 1)


def forecast_category(product_id: int, group: pd.DataFrame, features: pd.DataFrame) -> list[dict]:
    """Train 3 model bang TOAN BO du lieu cua 1 category, du doan gia cho
    DUNG ngay mai that - neu du lieu dang bi thieu vai ngay thi tu dong du
    bao de quy nhieu buoc de bu lai, khong con bi 'dung' o ngay cu."""
    cat_features = features[features["product_id"] == product_id]
    if cat_features.empty:
        return []

    X_train = cat_features[FEATURE_COLUMNS]
    y_train = cat_features[TARGET_COLUMN]

    group = group.sort_values("price_date")
    steps = steps_needed_to_reach_tomorrow(group["price_date"].max())

    results = []
    for model_name, build_model in MODEL_BUILDERS.items():
        model = build_model()
        model.fit(X_train, y_train)

        # Du bao de quy: moi buoc dung chinh ket qua buoc truoc lam input -
        # neu steps == 1 (truong hop binh thuong) thi chi chay dung 1 lan,
        # ket qua y het cach lam cu.
        step_prices = group["price_avg"].tolist()
        step_dates = list(group["price_date"])
        predicted_price = None
        for _ in range(steps):
            next_date = step_dates[-1] + pd.Timedelta(days=1)
            last3 = step_prices[-3:]
            row = pd.DataFrame(
                [
                    {
                        "lag_1": step_prices[-1],
                        "rolling_mean_3": sum(last3) / len(last3),
                        "day_of_week": next_date.dayofweek,
                    }
                ]
            )
            predicted_price = float(model.predict(row[FEATURE_COLUMNS])[0])
            step_prices.append(predicted_price)
            step_dates.append(next_date)

        results.append(
            {
                "product_id": product_id,
                "forecast_date": step_dates[-1].date(),
                "predicted_price": round(predicted_price, 2),
                "model_name": model_name,
                "steps_used": steps,
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
        payload = {k: v for k, v in f.items() if k != "steps_used"}
        if existing:
            existing.predicted_price = payload["predicted_price"]
        else:
            session.add(Forecast(**payload))
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

            steps = cat_forecasts[0]["steps_used"]
            if steps > 1:
                print(
                    f"  CANH BAO [{category}]: Hiện đang thiếu dữ liệu thực tế {steps - 1} ngày "
                    f"-> Độ chính xác có thể thấp hơn bình thường"
                )

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
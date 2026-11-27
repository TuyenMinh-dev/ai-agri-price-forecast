import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
import numpy as np
import torch
from sklearn.preprocessing import MinMaxScaler
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))
sys.path.append(str(BASE_DIR / "backend"))

from build_features import load_price_data, build_features
from train_baseline import (
    PriceLSTM,
    set_seed,
    LSTM_WINDOW,
    LSTM_EPOCHS,
    LSTM_HIDDEN,
    LSTM_LR,
)
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

def forecast_lstm(product_id, group, steps):
    """
    Huấn luyện mô hình LSTM từ dữ liệu giá lịch sử
    và dự đoán giá trong tương lai.
    """

    # 1. Sắp xếp dữ liệu theo ngày
    group = group.sort_values("price_date")

    prices = group["price_avg"].to_numpy(dtype=float)

    # 2. Kiểm tra dữ liệu đủ để huấn luyện
    if not np.isfinite(prices).all():
        print(f"Product {product_id}: Có giá trị giá không hợp lệ (NaN/inf)")
        return None

    if np.any(prices <= 0):
        print(f"Product {product_id}: Có giá không hợp lệ (<= 0)")
        return None

    if len(prices) <= LSTM_WINDOW:
        print(f"Product {product_id}: Không đủ dữ liệu cho LSTM")
        return None

    # 3. Chuẩn hóa giá về khoảng 0 đến 1
    scaler = MinMaxScaler()

    scaled_prices = scaler.fit_transform(
        prices.reshape(-1, 1)
    ).flatten()

    # 4. Tạo dữ liệu huấn luyện theo cửa sổ thời gian
    X_train = []
    y_train = []

    for i in range(len(scaled_prices) - LSTM_WINDOW):
        X_train.append(
            scaled_prices[i:i + LSTM_WINDOW]
        )
        y_train.append(
            scaled_prices[i + LSTM_WINDOW]
        )

    X_train = np.array(X_train, dtype=np.float32)
    y_train = np.array(y_train, dtype=np.float32)

    X_tensor = torch.tensor(X_train).unsqueeze(-1)
    y_tensor = torch.tensor(y_train)

    # 5. Khởi tạo mô hình LSTM
    set_seed()

    model = PriceLSTM(
        input_size=1,
        hidden_size=LSTM_HIDDEN
    )

    criterion = torch.nn.MSELoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LSTM_LR
    )

    # 6. Huấn luyện mô hình
    model.train()

    for epoch in range(LSTM_EPOCHS):
        optimizer.zero_grad()

        predictions = model(X_tensor)

        loss = criterion(predictions, y_tensor)

        loss.backward()
        optimizer.step()

    # 7. Dự đoán đệ quy các ngày tiếp theo
    model.eval()

    sequence = scaled_prices[-LSTM_WINDOW:].copy()

    with torch.no_grad():
        for _ in range(steps):

            input_tensor = torch.tensor(
                sequence,
                dtype=torch.float32
            ).reshape(1, LSTM_WINDOW, 1)

            predicted_scaled = model(input_tensor).item()

            sequence = np.append(
                sequence[1:],
                predicted_scaled
            )

    # 8. Chuyển kết quả về giá ban đầu
    predicted_price = scaler.inverse_transform(
        np.array([[predicted_scaled]])
    )[0, 0]

    last_date = group["price_date"].max()

    forecast_date = (
        pd.Timestamp(last_date) + pd.Timedelta(days=steps)
    ).date()

    return {
        "product_id": product_id,
        "forecast_date": forecast_date,
        "predicted_price": round(float(predicted_price), 2),
        "model_name": "LSTM",
        "steps_used": steps
    }

def forecast_category(product_id: int, group: pd.DataFrame, features: pd.DataFrame) -> list[dict]:
    """Train 3 model cu va LSTM, du doan gia cho ngay mai."""

    cat_features = features[features["product_id"] == product_id]

    if cat_features.empty:
        return []

    X_train = cat_features[FEATURE_COLUMNS]
    y_train = cat_features[TARGET_COLUMN]

    group = group.sort_values("price_date")
    steps = steps_needed_to_reach_tomorrow(group["price_date"].max())

    results = []

    # 1. Chay 3 mo hinh Machine Learning
    for model_name, build_model in MODEL_BUILDERS.items():
        model = build_model()
        model.fit(X_train, y_train)

        step_prices = group["price_avg"].tolist()
        step_dates = list(group["price_date"])
        predicted_price = None

        for _ in range(steps):
            next_date = step_dates[-1] + pd.Timedelta(days=1)
            last3 = step_prices[-3:]

            row = pd.DataFrame([
                {
                    "lag_1": step_prices[-1],
                    "rolling_mean_3": sum(last3) / len(last3),
                    "day_of_week": next_date.dayofweek,
                }
            ])

            predicted_price = float(
                model.predict(row[FEATURE_COLUMNS])[0]
            )

            step_prices.append(predicted_price)
            step_dates.append(next_date)

        results.append({
            "product_id": product_id,
            "forecast_date": step_dates[-1].date(),
            "predicted_price": round(predicted_price, 2),
            "model_name": model_name,
            "steps_used": steps,
        })

    # 2. Chay mo hinh LSTM
    lstm_result = forecast_lstm(product_id, group, steps)

    if lstm_result is not None:
        results.append(lstm_result)

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
        latest_system_date = df["price_date"].max()
        print(f"Ngay cap nhat gia moi nhat cua he thong: {latest_system_date.date()}")

        for product_id, group in df.groupby("product_id"):
            category = group["category"].iloc[0]
            cat_latest_date = group["price_date"].max()

            # 1. Chi du bao cho loai gao con dang duoc niem yet o dot moi nhat
            if cat_latest_date < latest_system_date:
                days_inactive = (latest_system_date - cat_latest_date).days
                print(
                    f"  [Bo qua] {category:<12}: Da ngung cap nhat tren web tu {cat_latest_date.date()} "
                    f"({days_inactive} ngay truoc) -> Khong du bao."
                )
                continue

            # 2. Chi du bao khi da co du du lieu toi thieu (>= 5 ngay)
            if len(group) < 5:
                print(
                    f"  [Bo qua] {category:<12}: Loai moi xuat hien, chua du du lieu train "
                    f"({len(group)} ngay < 5 ngay) -> Khong du bao."
                )
                continue

            cat_forecasts = forecast_category(product_id, group, features)

            if not cat_forecasts:
                print(f"  [Bo qua] {category}: chua du du lieu de train (can >= 2 dong sau khi tao feature).")
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
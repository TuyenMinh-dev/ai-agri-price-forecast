
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))
from build_features import load_price_data, build_features

FEATURE_COLUMNS = ["lag_1", "rolling_mean_3", "day_of_week"]
TARGET_COLUMN = "target"
TEST_SIZE_RATIO = 0.2


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
    nonzero = y_true != 0
    mape = (
        np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100
        if nonzero.any()
        else float("nan")
    )

    return {"MAE": mae, "RMSE": rmse, "MAPE (%)": mape}


def main():
    print("Đang lấy dữ liệu giá lúa gạo từ CSDL...")
    df = load_price_data(crop_type="rice")

    if df.empty:
        print("Không có dữ liệu giá lúa gạo trong CSDL. Hãy chạy crawler và "
              "load_crawler_data.py trước.")
        return

    features = build_features(df)
    print(f"Số dòng dữ liệu đủ điều kiện để train/test: {len(features)}")

    if len(features) < 4:
        print(
            "\nCẢNH BÁO: dữ liệu quá ít (< 4 dòng) để chia train/test có ý "
            "nghĩa. Kết quả dưới đây CHỈ để kiểm tra pipeline chạy được, "
            "không phản ánh độ chính xác thật. Chạy lại script này sau khi "
            "crawler tích luỹ thêm vài tuần dữ liệu."
        )

    train_df, test_df = train_test_split_by_time(features, TEST_SIZE_RATIO)

    if test_df.empty:
        print(
            "\nKhông đủ dữ liệu để tạo tập test riêng. Dùng tạm toàn bộ dữ "
            "liệu để xem thử model học được gì, KHÔNG dùng để đánh giá độ "
            "chính xác."
        )
        test_df = train_df.copy()

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]

    naive_pred = X_test["lag_1"]
    naive_metrics = compute_metrics(y_test, naive_pred)

    model = LinearRegression()
    model.fit(X_train, y_train)
    lr_pred = model.predict(X_test)
    lr_metrics = compute_metrics(y_test, lr_pred)

    print("\n" + "=" * 50)
    print("SO SÁNH KẾT QUẢ")
    print("=" * 50)
    print(f"{'Mô hình':<25} {'MAE':>10} {'RMSE':>10} {'MAPE (%)':>10}")
    print(
        f"{'Naive (giá lần trước)':<25} "
        f"{naive_metrics['MAE']:>10.2f} {naive_metrics['RMSE']:>10.2f} "
        f"{naive_metrics['MAPE (%)']:>10.2f}"
    )
    print(
        f"{'Linear Regression':<25} "
        f"{lr_metrics['MAE']:>10.2f} {lr_metrics['RMSE']:>10.2f} "
        f"{lr_metrics['MAPE (%)']:>10.2f}"
    )
    print("=" * 50)

    if lr_metrics["MAE"] < naive_metrics["MAE"]:
        print("=> Linear Regression đang tốt hơn naive baseline.")
    else:
        print(
            "=> Linear Regression CHƯA tốt hơn naive baseline - bình thường "
            "khi dữ liệu còn ít, sẽ cải thiện khi có thêm dữ liệu và thêm "
            "các mô hình khác (Random Forest/XGBoost)."
        )


if __name__ == "__main__":
    main()
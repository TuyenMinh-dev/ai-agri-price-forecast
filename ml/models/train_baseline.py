"""Train va so sanh 3 mo hinh du doan gia lua gao: Linear Regression, Random Forest, XGBoost - cung naive baseline."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

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


def print_detail_table(test_df: pd.DataFrame, naive_pred, lr_pred, rf_pred, xgb_pred):
    has_range = "price_min" in test_df.columns and "price_max" in test_df.columns

    print("=" * 90)
    print("CHI TIET: KHOANG GIA THAT vs GIA TUNG MO HINH DU DOAN (don vi: VND/kg)")
    print("=" * 90)
    header = f"{'Loai gao':<12} | {'Ngay':<10} | "
    header += f"{'Khoang that':>15} | " if has_range else f"{'Gia THAT(tb)':>12} | "
    header += f"{'Linear R.':>9} | {'Random F.':>9} | {'XGBoost':>9}"
    print(header)
    print("-" * 90)

    for i, (_, row) in enumerate(test_df.iterrows()):
        line = f"{row['category']:<12} | {str(row['price_date'].date()):<10} | "
        if has_range:
            pmin, pmax = row.get("price_min"), row.get("price_max")
            range_str = (
                f"[{pmin:,.0f}-{pmax:,.0f}]"
                if pd.notna(pmin) and pd.notna(pmax)
                else "N/A"
            )
            line += f"{range_str:>15} | "
        else:
            line += f"{row['target']:>12.2f} | "
        line += f"{lr_pred[i]:>9.2f} | {rf_pred[i]:>9.2f} | {xgb_pred[i]:>9.2f}"
        print(line)

    print("=" * 90)

    if has_range:
        print("Ghi chu: 'Khoang that' la [gia thap nhat - gia cao nhat] thuc te trong")
        print("ngay do - du doan nam trong khoang nay co the coi la chap nhan duoc, du")
        print("khong trung khop tuyet doi 1 con so.")
        print("=" * 90)


def print_summary_table(results: dict, best_model: str):
    print()
    print("TONG HOP: MUC DO SAI LECH TRUNG BINH CUA TUNG MO HINH")
    print("=" * 78)
    print(f"{'Mo hinh':<20} | {'Sai so TB':>12} | {'Sai so RMSE':>12} | {'Sai so %':>9}")
    print(f"{'':<20} | {'(VND/kg)':>12} | {'(VND/kg)':>12} | {'':>9}")
    print("-" * 78)
    for name, m in results.items():
        marker = "  <-- TOT NHAT" if name == best_model else ""
        print(
            f"{name:<20} | {m['MAE']:>12.2f} | {m['RMSE']:>12.2f} | "
            f"{m['MAPE (%)']:>8.2f}%{marker}"
        )
    print("=" * 78)
    print("Giai thich cac chi so:")
    print("  - Sai so TB (MAE)   : trung binh moi lan doan lech bao nhieu VND/kg")
    print("  - Sai so RMSE       : giong MAE nhung 'phat nang' neu co lan doan sai rat xa")
    print("  - Sai so % (MAPE)   : sai lech tinh theo % so voi gia that")
    print("=" * 78)
    print(f"\n=> Mo hinh tot nhat (sai so thap nhat): {best_model}")


def main():
    print("Dang lay du lieu gia lua gao tu CSDL...")
    df = load_price_data(crop_type="rice")

    if df.empty:
        print("Khong co du lieu gia lua gao trong CSDL. Hay chay crawler va "
              "load_crawler_data.py truoc.")
        return

    features = build_features(df)
    print(f"So dong du lieu du dieu kien de train/test: {len(features)}\n")

    train_df, test_df = train_test_split_by_time(features, TEST_SIZE_RATIO)

    if test_df.empty:
        test_df = train_df.copy()

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN]

    naive_pred = X_test["lag_1"].to_numpy()

    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)

    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    xgb_model = XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)

    print_detail_table(test_df, naive_pred, lr_pred, rf_pred, xgb_pred)

    results = {
        "Naive": compute_metrics(y_test, naive_pred),
        "Linear Regression": compute_metrics(y_test, lr_pred),
        "Random Forest": compute_metrics(y_test, rf_pred),
        "XGBoost": compute_metrics(y_test, xgb_pred),
    }
    best_model = min(
        (name for name in results if name != "Naive"),
        key=lambda n: results[n]["MAE"],
    )
    print_summary_table(results, best_model)


if __name__ == "__main__":
    main()
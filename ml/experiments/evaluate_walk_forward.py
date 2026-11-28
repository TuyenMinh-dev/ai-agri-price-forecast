"""
Tham dinh mo hinh chuoi thoi gian bang Walk-Forward Validation (Expanding Window).

Muc tieu:
- Danh gia do on dinh va kha nang tong quat hoa cua 4 mo hinh:
  Naive, Linear Regression, Random Forest, XGBoost.
- Triet tieu hoan toan Data Leakage: moi fold chi fit tren tap qua khu
  (expanding window) va kiem tra tren cua so tuong lai ngay ke tiep.
- Tinh Mean va Std cua MAE, RMSE qua cac fold cho tung loai gao va tong hop chung.
- Xuat bang ket qua ra file: docs/walk_forward_results.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))

from build_features import build_features, load_price_data

FEATURE_COLUMNS = ["lag_1", "rolling_mean_3", "day_of_week"]
TARGET_COLUMN = "target"
MIN_FOLDS = 3
OUTPUT_CSV = BASE_DIR / "docs" / "walk_forward_results.csv"

MODELS = {
    "Naive": None,
    "Linear Regression": lambda: LinearRegression(),
    "Random Forest": lambda: RandomForestRegressor(n_estimators=100, random_state=42),
    "XGBoost": lambda: XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
}


def make_folds(n_rows: int) -> list[tuple[int, int]]:
    """Chia du lieu thanh cac fold theo kieu Expanding Window (khong shuffle).

    Fold sau luon dung nhieu du lieu qua khu hon fold truoc de train,
    va du doan tren khoang thoi gian ke tiep chua tung thay.
    Tra ve danh sach cac cap (train_end, test_end).
    """
    fold_size = max(2, n_rows // 7)
    min_train = max(5, fold_size)

    folds = []
    cutoff = min_train
    while cutoff + fold_size <= n_rows:
        folds.append((cutoff, cutoff + fold_size))
        cutoff += fold_size
    return folds


def compute_errors(y_true: np.ndarray, y_pred: np.ndarray) -> tuple[float, float]:
    """Tinh MAE va RMSE cho mot fold."""
    diff = y_true - y_pred
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    return mae, rmse


def evaluate_category(category: str, group: pd.DataFrame) -> list[dict]:
    """Chay Walk-Forward Validation cho mot loai gao cu the."""
    group = group.sort_values("price_date").reset_index(drop=True)
    n_rows = len(group)
    folds = make_folds(n_rows)

    if len(folds) < MIN_FOLDS:
        print(
            f"[Bo qua] {category}: chi co {n_rows} dong, chia duoc {len(folds)} fold "
            f"(yeu cau toi thieu {MIN_FOLDS} fold)."
        )
        return []

    fold_records = []
    for fold_idx, (train_end, test_end) in enumerate(folds, start=1):
        train_df = group.iloc[:train_end]
        test_df = group.iloc[train_end:test_end]

        X_train = train_df[FEATURE_COLUMNS]
        y_train = train_df[TARGET_COLUMN].to_numpy(dtype=float)
        X_test = test_df[FEATURE_COLUMNS]
        y_test = test_df[TARGET_COLUMN].to_numpy(dtype=float)

        for model_name, build_fn in MODELS.items():
            if model_name == "Naive":
                y_pred = X_test["lag_1"].to_numpy(dtype=float)
            else:
                model = build_fn()
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

            mae, rmse = compute_errors(y_test, y_pred)
            fold_records.append(
                {
                    "category": category,
                    "model": model_name,
                    "fold": fold_idx,
                    "train_size": len(train_df),
                    "test_size": len(test_df),
                    "mae": mae,
                    "rmse": rmse,
                    "n_rows": n_rows,
                    "n_folds": len(folds),
                }
            )

    return fold_records


def summarize_results(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Tong hop Mean va Std cua MAE, RMSE theo tung loai gao va toan cuc."""
    per_category = (
        fold_df.groupby(["category", "model"], sort=False)
        .agg(
            n_rows=("n_rows", "first"),
            n_folds=("n_folds", "first"),
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
            rmse_mean=("rmse", "mean"),
            rmse_std=("rmse", "std"),
        )
        .reset_index()
    )

    overall = (
        fold_df.groupby("model", sort=False)
        .agg(
            n_rows=("train_size", "count"),
            n_folds=("fold", "count"),
            mae_mean=("mae", "mean"),
            mae_std=("mae", "std"),
            rmse_mean=("rmse", "mean"),
            rmse_std=("rmse", "std"),
        )
        .reset_index()
    )
    overall.insert(0, "category", "ALL (Tong hop)")

    summary = pd.concat([per_category, overall], ignore_index=True)
    for col in ["mae_mean", "mae_std", "rmse_mean", "rmse_std"]:
        summary[col] = summary[col].round(2)
    return summary


def print_overall_table(summary: pd.DataFrame) -> None:
    """In bang tong hop ket qua Walk-Forward Validation ra man hinh."""
    overall = summary[summary["category"] == "ALL (Tong hop)"]
    best_model = overall.loc[overall["mae_mean"].idxmin(), "model"]

    print("\n" + "=" * 82)
    print("TONG HOP WALK-FORWARD VALIDATION (TAT CA CAC LOAI GAO & CAC FOLD)")
    print("=" * 82)
    print(
        f"{'Mo hinh':<20} | {'So luot':>7} | {'MAE Mean +- Std':>20} | {'RMSE Mean +- Std':>22}"
    )
    print("-" * 82)
    for _, row in overall.iterrows():
        marker = "  <-- TOT NHAT" if row["model"] == best_model else ""
        mae_str = f"{row['mae_mean']:>7.2f} +- {row['mae_std']:<6.2f}"
        rmse_str = f"{row['rmse_mean']:>7.2f} +- {row['rmse_std']:<6.2f}"
        print(
            f"{row['model']:<20} | {int(row['n_folds']):>7} | {mae_str:>20} | {rmse_str:>22}{marker}"
        )
    print("=" * 82)
    print(f"=> Mo hinh on dinh & chinh xac nhat (MAE Mean thap nhat): {best_model}")


def main() -> None:
    print("Dang tai du lieu gia lua gao tu CSDL Neon...")
    df = load_price_data(crop_type="rice")
    if df.empty:
        print("Khong co du lieu gia lua gao trong CSDL. Vui long kiem tra lai ket noi .env.")
        return

    features = build_features(df)
    print(f"Tong so dong hop le sau khi tao feature: {len(features)}\n")

    all_records: list[dict] = []
    for category, group in features.groupby("category"):
        records = evaluate_category(category, group)
        all_records.extend(records)

    if not all_records:
        print("Khong co loai gao nao du so fold toi thieu de danh gia.")
        return

    fold_df = pd.DataFrame(all_records)
    summary = summarize_results(fold_df)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    print("\nKet qua chi tiet theo tung loai gao:")
    for category, cat_df in summary[summary["category"] != "ALL (Tong hop)"].groupby(
        "category", sort=False
    ):
        n_rows = int(cat_df["n_rows"].iloc[0])
        n_folds = int(cat_df["n_folds"].iloc[0])
        print(f"\n--- {category} ({n_rows} dong, {n_folds} folds) ---")
        for _, r in cat_df.iterrows():
            print(
                f"  {r['model']:<18} | MAE: {r['mae_mean']:>7.2f} +- {r['mae_std']:<6.2f} "
                f"| RMSE: {r['rmse_mean']:>7.2f} +- {r['rmse_std']:<6.2f}"
            )

    print_overall_table(summary)
    print(f"\nDa xuat bang ket qua Walk-Forward ra file: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

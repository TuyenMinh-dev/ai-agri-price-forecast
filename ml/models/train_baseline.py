"""Train va so sanh 5 mo hinh du doan gia lua gao: Naive baseline, Linear Regression, Random Forest, XGBoost va mang LSTM (PyTorch)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor
import torch
import torch.nn as nn

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))
from build_features import load_price_data, build_features

FEATURE_COLUMNS = ["lag_1", "rolling_mean_3", "day_of_week"]
TARGET_COLUMN = "target"
TEST_SIZE_RATIO = 0.2
LSTM_WINDOW = 3
LSTM_EPOCHS = 100
LSTM_HIDDEN = 32
LSTM_LR = 0.005
SEED = 42


def set_seed(seed=SEED):
    np.random.seed(seed)
    torch.manual_seed(seed)


class PriceLSTM(nn.Module):
    def __init__(self, input_size=1, hidden_size=LSTM_HIDDEN, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        last_out = out[:, -1, :]
        pred = self.fc(last_out)
        return pred.squeeze(-1)


def train_and_predict_lstm(train_df: pd.DataFrame, test_df: pd.DataFrame, window: int = LSTM_WINDOW) -> np.ndarray:
    """Huan luyen LSTM theo tung category va du bao tren tap test (chong data leakage)."""
    lstm_predictions = []

    for category, test_group in test_df.groupby("category", sort=False):
        train_group = train_df[train_df["category"] == category].sort_values("price_date")
        test_group = test_group.sort_values("price_date")

        train_prices = train_group["target"].to_numpy().astype(float)
        test_prices = test_group["target"].to_numpy().astype(float)

        if len(train_prices) <= window:
            fallback = test_group["lag_1"].to_numpy()
            for p in fallback:
                lstm_predictions.append((category, p))
            continue

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaler.fit(train_prices.reshape(-1, 1))

        train_scaled = scaler.transform(train_prices.reshape(-1, 1)).flatten()

        X_train_list, y_train_list = [], []
        for i in range(len(train_scaled) - window):
            X_train_list.append(train_scaled[i : i + window])
            y_train_list.append(train_scaled[i + window])

        X_train = np.array(X_train_list, dtype=np.float32)
        y_train = np.array(y_train_list, dtype=np.float32)

        set_seed(SEED)
        model = PriceLSTM(input_size=1, hidden_size=LSTM_HIDDEN)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=LSTM_LR)

        X_train_t = torch.tensor(X_train).unsqueeze(-1)
        y_train_t = torch.tensor(y_train)

        model.train()
        for _ in range(LSTM_EPOCHS):
            optimizer.zero_grad()
            out = model(X_train_t)
            loss = criterion(out, y_train_t)
            loss.backward()
            optimizer.step()

        combined_prices = np.concatenate([train_prices[-window:], test_prices])
        combined_scaled = scaler.transform(combined_prices.reshape(-1, 1)).flatten()

        X_test_list = []
        for t in range(window, len(combined_scaled)):
            X_test_list.append(combined_scaled[t - window : t])

        X_test = np.array(X_test_list, dtype=np.float32)
        X_test_t = torch.tensor(X_test).unsqueeze(-1)

        model.eval()
        with torch.no_grad():
            pred_scaled = model(X_test_t).numpy()

        pred_prices = scaler.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()

        for idx, (_, row) in enumerate(test_group.iterrows()):
            lstm_predictions.append((row.name, pred_prices[idx]))

    pred_map = dict(lstm_predictions)
    return np.array([pred_map.get(idx, test_df.loc[idx, "lag_1"]) for idx in test_df.index])


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


def print_detail_table(test_df: pd.DataFrame, naive_pred, lr_pred, rf_pred, xgb_pred, lstm_pred):
    has_range = "price_min" in test_df.columns and "price_max" in test_df.columns

    print("=" * 105)
    print("CHI TIET: KHOANG GIA THAT vs GIA TUNG MO HINH DU DOAN (don vi: VND/kg)")
    print("=" * 105)
    header = f"{'Loai gao':<12} | {'Ngay':<10} | "
    header += f"{'Khoang that':>15} | " if has_range else f"{'Gia THAT(tb)':>12} | "
    header += f"{'Linear R.':>9} | {'Random F.':>9} | {'XGBoost':>9} | {'LSTM':>9}"
    print(header)
    print("-" * 105)

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
        line += f"{lr_pred[i]:>9.2f} | {rf_pred[i]:>9.2f} | {xgb_pred[i]:>9.2f} | {lstm_pred[i]:>9.2f}"
        print(line)

    print("=" * 105)
    if has_range:
        print("Ghi chu: 'Khoang that' la [gia thap nhat - gia cao nhat] thuc te trong ngay do.")
        print("=" * 105)


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
        print("Khong co du lieu gia lua gao trong CSDL. Hay chay crawler va load_crawler_data.py truoc.")
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

    print("Dang huan luyen Linear Regression, Random Forest, XGBoost...")
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)

    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    xgb_model = XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)

    print("Dang huan luyen mang LSTM (PyTorch)...")
    lstm_pred = train_and_predict_lstm(train_df, test_df)

    print_detail_table(test_df, naive_pred, lr_pred, rf_pred, xgb_pred, lstm_pred)

    results = {
        "Naive": compute_metrics(y_test, naive_pred),
        "Linear Regression": compute_metrics(y_test, lr_pred),
        "Random Forest": compute_metrics(y_test, rf_pred),
        "XGBoost": compute_metrics(y_test, xgb_pred),
        "LSTM": compute_metrics(y_test, lstm_pred),
    }
    best_model = min(
        (name for name in results if name != "Naive"),
        key=lambda n: results[n]["MAE"],
    )
    print_summary_table(results, best_model)


if __name__ == "__main__":
    main()

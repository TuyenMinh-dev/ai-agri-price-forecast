"""
Thu nghiem mo hinh LSTM du bao gia lua gao bang PyTorch.
- Khong gay data leakage: MinMaxScaler chi fit tren tap train.
- So sanh truc tiep voi Naive baseline (persistence).
- Chay thu nghiem trong ml/experiments, chua anh huong pipeline chinh.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "ml" / "features"))

from build_features import load_price_data

WINDOW_SIZE = 5      # So ngay qua khu dung de du doan ngay tiep theo
TEST_RATIO = 0.2     # 20% du lieu cuoi dung lam tap test
HIDDEN_SIZE = 32     # Kich thuoc lop an LSTM
NUM_EPOCHS = 100     # So luot huan luyen
LEARNING_RATE = 0.005
SEED = 42


def set_seed(seed=SEED):
    np.random.seed(seed)
    torch.manual_seed(seed)


class PriceLSTM(nn.Module):
    """Mang LSTM 1 lop + 1 lop Linear du bao gia."""
    def __init__(self, input_size=1, hidden_size=32, num_layers=1):
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


def compute_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    nonzero = y_true != 0
    mape = (
        float(np.mean(np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])) * 100)
        if nonzero.any()
        else float("nan")
    )
    return {"MAE": mae, "RMSE": rmse, "MAPE (%)": mape}


def train_and_eval_category(category: str, group: pd.DataFrame, window: int = WINDOW_SIZE):
    group = group.sort_values("price_date").reset_index(drop=True)
    n = len(group)

    n_test = max(1, int(n * TEST_RATIO))
    n_train = n - n_test

    # Can it nhat (window + 2) dong train de tao duoc it nhat 2 mau sequence
    if n_train <= window:
        print(f"\nBo qua {category}: Khong du du lieu (n={n}, can > {window + n_test}).")
        return None

    train_df = group.iloc[:n_train].copy()
    test_df = group.iloc[n_train:].copy()

    train_prices = train_df["price_avg"].to_numpy().astype(float)
    all_prices = group["price_avg"].to_numpy().astype(float)

    # 1. Scaler: CHI FIT TREN TRAIN (CHONG DATA LEAKAGE)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(train_prices.reshape(-1, 1))

    all_scaled = scaler.transform(all_prices.reshape(-1, 1)).flatten()

    # 2. Tao tap train: sliding window tren train
    X_train_list, y_train_list = [], []
    for i in range(n_train - window):
        X_train_list.append(all_scaled[i : i + window])
        y_train_list.append(all_scaled[i + window])

    X_train = np.array(X_train_list, dtype=np.float32)
    y_train = np.array(y_train_list, dtype=np.float32)

    # 3. Tao tap test: moi target p_t dung window diem ngay truoc do
    X_test_list, y_test_list = [], []
    for t in range(n_train, n):
        X_test_list.append(all_scaled[t - window : t])
        y_test_list.append(all_prices[t])

    X_test = np.array(X_test_list, dtype=np.float32)
    y_test = np.array(y_test_list, dtype=np.float32)

    # Naive baseline: gia ngay hom truoc
    naive_pred = np.array([all_prices[t - 1] for t in range(n_train, n)], dtype=np.float32)

    # 4. Chuyen tensor PyTorch (batch, window, 1)
    set_seed(SEED)
    X_train_t = torch.tensor(X_train).unsqueeze(-1)
    y_train_t = torch.tensor(y_train)
    X_test_t = torch.tensor(X_test).unsqueeze(-1)

    model = PriceLSTM(input_size=1, hidden_size=HIDDEN_SIZE, num_layers=1)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # 5. Loop huan luyen
    model.train()
    for epoch in range(NUM_EPOCHS):
        optimizer.zero_grad()
        out = model(X_train_t)
        loss = criterion(out, y_train_t)
        loss.backward()
        optimizer.step()

    # 6. Du doan tren tap test
    model.eval()
    with torch.no_grad():
        pred_scaled = model(X_test_t).numpy()

    lstm_pred = scaler.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()

    metrics_naive = compute_metrics(y_test, naive_pred)
    metrics_lstm = compute_metrics(y_test, lstm_pred)

    print(f"\n{'='*75}")
    print(f"KET QUA: {category} (Tong: {n} ngay | Train: {n_train} | Test: {n_test})")
    print(f"{'='*75}")
    print(f"{'Ngay':<12} | {'Gia that':>12} | {'Naive':>12} | {'LSTM':>12}")
    print(f"{'-'*75}")

    for idx, (_, row) in enumerate(test_df.iterrows()):
        d_str = str(pd.to_datetime(row['price_date']).date())
        print(f"{d_str:<12} | {y_test[idx]:>12.2f} | {naive_pred[idx]:>12.2f} | {lstm_pred[idx]:>12.2f}")

    print(f"{'-'*75}")
    print(f"Sai so Naive : MAE={metrics_naive['MAE']:.2f} | RMSE={metrics_naive['RMSE']:.2f} | MAPE={metrics_naive['MAPE (%)']:.2f}%")
    print(f"Sai so LSTM  : MAE={metrics_lstm['MAE']:.2f} | RMSE={metrics_lstm['RMSE']:.2f} | MAPE={metrics_lstm['MAPE (%)']:.2f}%")

    better = "LSTM tot hon Naive" if metrics_lstm["MAE"] < metrics_naive["MAE"] else "Naive tot hon LSTM"
    print(f"=> Nhan xet: {better}")
    return {"category": category, "naive": metrics_naive, "lstm": metrics_lstm}


def main():
    print("Dang lay du lieu gia lua gao...")
    df = load_price_data(crop_type="rice")

    if df.empty:
        # Fallback doc tu file CSV neu CSDL chua ket noi duoc
        raw_csv = BASE_DIR / "data" / "raw" / "rice_price_vietnambiz.csv"
        if raw_csv.exists():
            print(f"Khong co DB, chuyen sang doc file CSV cuc bo: {raw_csv}")
            raw = pd.read_csv(raw_csv)
            raw["price_date"] = pd.to_datetime(raw["price_date"])
            raw["price_min"] = pd.to_numeric(raw["price_min"], errors="coerce")
            raw["price_max"] = pd.to_numeric(raw["price_max"], errors="coerce")
            raw["price_avg"] = raw[["price_min", "price_max"]].mean(axis=1)
            df = raw.dropna(subset=["price_avg"]).sort_values(["category", "price_date"]).reset_index(drop=True)
        else:
            print("Khong tim thay du lieu. Hay kiem tra lai CSDL hoac file CSV.")
            return

    print(f"So dong du lieu gia goc: {len(df)}")
    print(f"Cac chung loai: {list(df['category'].unique())}")

    all_results = []
    for category, group in df.groupby("category"):
        res = train_and_eval_category(category, group)
        if res:
            all_results.append(res)

    if all_results:
        print(f"\n{'='*75}")
        print("BANG TONG HOP SO SANH NAIVE vs LSTM (TAT CA CHUNG LOAI)")
        print(f"{'='*75}")
        print(f"{'Chung loai':<15} | {'MAE Naive':>12} | {'MAE LSTM':>12} | {'Chenh lech MAE':>16}")
        print(f"{'-'*75}")
        for r in all_results:
            cat = r["category"]
            m_naive = r["naive"]["MAE"]
            m_lstm = r["lstm"]["MAE"]
            diff = m_lstm - m_naive
            diff_str = f"{diff:+.2f} VND"
            print(f"{cat:<15} | {m_naive:>12.2f} | {m_lstm:>12.2f} | {diff_str:>16}")
        print(f"{'='*75}")
        print("Ghi chu: LSTM thuong cao hon Naive o tap du lieu nho vi mang de overfit.")


if __name__ == "__main__":
    main()

"""
Enhanced Feature Engineering & Model Evaluation for Rice Price Forecasting.
Thành viên thực hiện: TÂM (Nhóm 08 - AgriSight)

Mô tả:
1. Xây dựng bộ đặc trưng nâng cao (Enhanced Features) cho bài toán dự báo giá lúa gạo:
   - lag_1: Giá phiên t-1 (price_avg.shift(1))
   - lag_2: Giá phiên t-2 (price_avg.shift(2))
   - lag_7: Giá phiên t-7 (price_avg.shift(7))
   - rolling_mean_3: Giá trung bình trượt 3 phiên gần nhất (price_avg.shift(1).rolling(3).mean())
   - rolling_mean_7: Giá trung bình trượt 7 phiên gần nhất (price_avg.shift(1).rolling(7).mean())
   - price_change: Biến động giá giữa 2 phiên gần nhất (price_avg.shift(1) - price_avg.shift(2))
   - day_of_week: Thứ trong tuần (0: Thứ hai -> 6: Chủ nhật)
   - target: Giá trung bình của phiên hiện tại (price_avg)

2. Đảm bảo tính đúng đắn khoa học & Code Quality Hardening:
   - Kiểm tra dữ liệu đầu vào nghiêm ngặt (Data Validation): kiểm tra NaT, ngày không hợp lệ,
     kiểm tra khả năng ép kiểu số thực, từ chối NaN, vô hạn (inf/-inf),
     trùng lặp (product_id, price_date), và định danh/metadata bị thiếu.
   - Sắp xếp dữ liệu theo thứ tự thời gian trước khi tính toán.
   - Tính toán đặc trưng độc lập theo từng sản phẩm (product_id), tránh trộn lẫn dữ liệu giữa các sản phẩm.
   - Bảo toàn thông tin metadata (product_id, category, price_date) xuyên suốt quy trình split và train.
   - Loại trừ hoàn toàn hiện tượng rò rỉ dữ liệu (Target Leakage): Cửa sổ trượt rolling loại trừ phiên mục tiêu hiện tại.
   - Kiểm tra tham số test_ratio nghiêm ngặt (0 < test_ratio < 1, từ chối Boolean, None, NaN, Inf).
   - Đánh giá công bằng (Fair Comparison): Baseline và Enhanced được so sánh trên cùng tập mẫu kiểm thử (identical test observations).
   - Xử lý giá trị khuyết thiếu do phép trễ (shift) bằng cách loại bỏ giai đoạn khởi động (warmup period), tuyệt đối không điền giá trị 0.
   - Ghi nhận rõ: lag_7 là 7 phiên quan sát giao dịch trước đó, không đồng nhất với 7 ngày dương lịch do thị trường nghỉ cuối tuần.

3. Đầu ra:
   - docs/figures/price_history_all.png: Lịch sử biến động giá các loại gạo.
   - docs/figures/actual_vs_predicted.png: Phân tán Giá thực tế vs Giá dự báo kèm đường y = x.
   - docs/figures/feature_importance.png: Độ quan trọng đặc trưng từ mô hình Random Forest.
   - docs/feature_comparison_results.csv: Bảng tổng hợp so sánh MAE, RMSE giữa Baseline và Enhanced.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Cấu hình thư mục font matplotlib tránh lỗi phân quyền trên Windows Sandbox
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")  # Chế độ headless cho xuất ảnh không cần màn hình GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

# Thiết lập đường dẫn gốc của repository
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(REPO_ROOT / "ml" / "features"))
sys.path.append(str(REPO_ROOT / "backend"))

# Danh sách tên các đặc trưng
BASELINE_FEATURES: List[str] = ["lag_1", "rolling_mean_3", "day_of_week"]
ENHANCED_FEATURES: List[str] = [
    "lag_1",
    "lag_2",
    "lag_7",
    "rolling_mean_3",
    "rolling_mean_7",
    "price_change",
    "day_of_week",
]
TARGET_COLUMN: str = "target"
REQUIRED_METADATA: List[str] = ["product_id", "category", "price_date"]
TEST_RATIO: float = 0.2
RANDOM_SEED: int = 42

# Thư mục xuất kết quả
DOCS_DIR = REPO_ROOT / "docs"
FIGURES_DIR = DOCS_DIR / "figures"
CSV_OUTPUT_PATH = DOCS_DIR / "feature_comparison_results.csv"


def _validate_input_data(df: pd.DataFrame) -> None:
    """
    Kiểm định nghiêm ngặt tính toàn vẹn của dữ liệu đầu vào:
    1. Kiểm tra sự tồn tại của các cột bắt buộc ('price_date', 'price_avg').
    2. Kiểm tra 'price_date' không chứa NaT hoặc ngày không hợp lệ.
    3. Kiểm tra 'price_avg' và 'target' (nếu có) có thể chuyển đổi thành số thực.
    4. Từ chối mọi giá trị NaN, vô hạn (inf, -inf) trong Feature và Target.
    5. Kiểm tra định danh và metadata cần thiết ('product_id', 'category' không được chứa NaN/None).
    6. Kiểm tra bản ghi trùng lặp (product_id, price_date).
       Lưu ý về 'source': Nếu dữ liệu chứa nhiều nguồn trên cùng 1 ngày của 1 sản phẩm,
       yêu cầu tầng ingest phải xử lý rõ ràng nguồn trước; hàm này không tự ý drop hay aggregate.
    """
    required_cols = {"price_date", "price_avg"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame đầu vào thiếu các cột bắt buộc: {required_cols - set(df.columns)}")

    # 1. Kiểm tra 'price_date' không chứa NaT hoặc giá trị không thể chuyển thành ngày
    dates_raw = df["price_date"]
    if dates_raw.isna().any():
        raise ValueError("Cột 'price_date' chứa giá trị khuyết thiếu (NaN/NaT).")

    dates_clean = pd.to_datetime(dates_raw, errors="coerce")
    if dates_clean.isna().any():
        invalid_count = int(dates_clean.isna().sum())
        raise ValueError(f"Cột 'price_date' chứa {invalid_count} giá trị ngày không hợp lệ hoặc NaT.")

    # 2. Kiểm tra metadata và định danh nhóm (product_id, category)
    if "product_id" in df.columns:
        if df["product_id"].isna().any():
            missing_count = int(df["product_id"].isna().sum())
            raise ValueError(
                f"Dữ liệu đầu vào chứa {missing_count} bản ghi thiếu định danh 'product_id' (NaN/None). "
                "Không âm thầm bỏ qua các nhóm thiếu định danh."
            )

    if "category" in df.columns:
        if df["category"].isna().any():
            missing_count = int(df["category"].isna().sum())
            raise ValueError(
                f"Dữ liệu đầu vào chứa {missing_count} bản ghi thiếu thông tin metadata 'category' (NaN/None). "
                "Cần đảm bảo tính toàn vẹn của metadata cho báo cáo và trực quan hóa."
            )

    # 3. Kiểm tra khả năng chuyển đổi thành số thực và kiểm tra NaN của price_avg
    numeric_avg = pd.to_numeric(df["price_avg"], errors="coerce")
    if numeric_avg.isna().any():
        invalid_count = int(numeric_avg.isna().sum())
        raise ValueError(
            f"Cột 'price_avg' chứa {invalid_count} giá trị không thể chuyển đổi thành số thực hoặc bị NaN."
        )

    if np.isinf(numeric_avg).any():
        inf_count = int(np.isinf(numeric_avg).sum())
        raise ValueError(f"Phát hiện {inf_count} giá trị vô hạn (inf/-inf) trong cột 'price_avg'.")

    # 4. Kiểm tra Target nếu đã tồn tại sẵn trong DataFrame
    if TARGET_COLUMN in df.columns:
        numeric_target = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
        if numeric_target.isna().any():
            invalid_count = int(numeric_target.isna().sum())
            raise ValueError(
                f"Cột '{TARGET_COLUMN}' chứa {invalid_count} giá trị không thể chuyển đổi thành số thực hoặc bị NaN."
            )
        if np.isinf(numeric_target).any():
            inf_count = int(np.isinf(numeric_target).sum())
            raise ValueError(f"Phát hiện {inf_count} giá trị vô hạn (inf/-inf) trong cột '{TARGET_COLUMN}'.")

    # 5. Kiểm tra bản ghi trùng lặp (product_id, price_date) hoặc (category, price_date)
    # Ghi chú nghiệp vụ: Bảng MarketPrice trong CSDL có trường 'source'.
    # Để tránh suy diễn nghiệp vụ không có căn cứ, quy trình Feature Engineering yêu cầu
    # mỗi chuỗi thời gian đầu vào chỉ có tối đa 1 quan sát trên mỗi mốc thời gian.
    # Tuyệt đối không tự ý aggregate hay drop các bản ghi khác nguồn.
    id_col = "product_id" if "product_id" in df.columns else ("category" if "category" in df.columns else None)
    if id_col is not None:
        temp_check = pd.DataFrame({id_col: df[id_col], "clean_date": dates_clean})
        duplicates_mask = temp_check.duplicated(subset=[id_col, "clean_date"])
        dup_count = int(duplicates_mask.sum())
        if dup_count > 0:
            raise ValueError(
                f"Phát hiện {dup_count} bản ghi trùng lặp đồng thời cả '{id_col}' và 'price_date'. "
                "Dữ liệu chuỗi thời gian yêu cầu mỗi sản phẩm chỉ có tối đa 1 quan sát trên mỗi mốc thời gian. "
                "Nếu dữ liệu có nhiều nguồn ('source'), vui lòng lọc hoặc tiền xử lý rõ ràng trước khi tạo đặc trưng."
            )


def build_enhanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bộ đặc trưng nâng cao (Enhanced Features) cho dữ liệu giá chuỗi thời gian.
    
    Tính toán độc lập theo từng sản phẩm (product_id hoặc category) nhằm tránh
    rò rỉ dữ liệu chéo giữa các mặt hàng khác nhau.
    
    Tham số:
        df: DataFrame chứa các cột ['product_id', 'category', 'price_date', 'price_avg']
            (có thể chứa thêm 'price_min', 'price_max', 'source').
            
    Trả về:
        DataFrame đã tính toán đầy đủ các đặc trưng và loại bỏ các dòng khuyết thiếu
        do quá trình trễ (7 quan sát đầu tiên của mỗi mặt hàng).
    """
    if df.empty:
        return pd.DataFrame()

    # Xác thực dữ liệu đầu vào nghiêm ngặt
    _validate_input_data(df)

    work_df = df.copy()
    work_df["price_date"] = pd.to_datetime(work_df["price_date"])
    work_df["price_avg"] = work_df["price_avg"].astype(float)

    # Xác định trường định danh nhóm: ưu tiên product_id nếu có, nếu không thì dùng category
    if "product_id" in work_df.columns:
        group_cols = ["product_id"]
    elif "category" in work_df.columns:
        group_cols = ["category"]
    else:
        # Nếu không có cả hai, coi toàn bộ là 1 chuỗi đơn lẻ
        group_cols = []

    result_frames = []

    def _process_group(group: pd.DataFrame) -> pd.DataFrame:
        # 1. Sắp xếp tuần tự nghiêm ngặt theo thời gian
        grp = group.sort_values("price_date").copy().reset_index(drop=True)

        # 2. Tạo các đặc trưng trễ (Lag features)
        # shift(1): Giá phiên trước (t-1)
        grp["lag_1"] = grp["price_avg"].shift(1)
        # shift(2): Giá phiên trước nữa (t-2)
        grp["lag_2"] = grp["price_avg"].shift(2)
        # shift(7): Giá 7 phiên giao dịch trước đó (t-7).
        # Lưu ý: 7 phiên quan sát ~ 9-11 ngày dương lịch do không tính cuối tuần.
        grp["lag_7"] = grp["price_avg"].shift(7)

        # 3. Tạo các đặc trưng trung bình trượt (Rolling Mean features)
        # Bắt buộc shift(1) trước khi rolling để loại trừ target hiện tại (ngăn target leakage)
        grp["rolling_mean_3"] = (
            grp["price_avg"].shift(1).rolling(window=3, min_periods=3).mean()
        )
        grp["rolling_mean_7"] = (
            grp["price_avg"].shift(1).rolling(window=7, min_periods=7).mean()
        )

        # 4. Tạo đặc trưng biến động giá gần nhất (Momentum/Price change)
        grp["price_change"] = grp["price_avg"].shift(1) - grp["price_avg"].shift(2)

        # 5. Đặc trưng thời gian: Thứ trong tuần (0: Thứ Hai -> 6: Chủ Nhật)
        grp["day_of_week"] = grp["price_date"].dt.dayofweek

        # 6. Biến mục tiêu: Giá trung bình phiên hiện tại t
        grp[TARGET_COLUMN] = grp["price_avg"]

        return grp

    if group_cols:
        for _, group in work_df.groupby(group_cols):
            result_frames.append(_process_group(group))
    else:
        result_frames.append(_process_group(work_df))

    result = pd.concat(result_frames, ignore_index=True)

    # 7. Xử lý giá trị NaN sinh ra do phép trễ:
    # Do đặc trưng lớn nhất là lag_7 và rolling_mean_7 (cần 7 quan sát lịch sử),
    # ta loại bỏ các dòng khuyết thiếu ở giai đoạn khởi động (warmup period).
    # Không điền 0 vì sẽ làm sai lệch bản chất chuỗi giá nông sản.
    result = result.dropna(subset=ENHANCED_FEATURES + [TARGET_COLUMN]).reset_index(drop=True)

    # 8. Kiểm tra không để sót bất kỳ giá trị vô hạn nào trong Features hoặc Target
    if not result.empty:
        check_cols = ENHANCED_FEATURES + [TARGET_COLUMN]
        if np.isinf(result[check_cols].to_numpy().astype(float)).any():
            raise ValueError("Phát hiện giá trị vô hạn (inf/-inf) trong ma trận đặc trưng sau khi tính toán.")

    # Đảm bảo sắp xếp lại theo danh mục và thời gian để dễ theo dõi
    sort_keys = [c for c in ["category", "price_date"] if c in result.columns]
    if sort_keys:
        result = result.sort_values(sort_keys).reset_index(drop=True)

    return result


def build_baseline_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo bộ đặc trưng Baseline (tương thích với ml/features/build_features.py hiện tại)
    nhưng hỗ trợ phân nhóm theo product_id để chuẩn xác và có kiểm tra validation.
    """
    if df.empty:
        return pd.DataFrame()

    _validate_input_data(df)

    work_df = df.copy()
    work_df["price_date"] = pd.to_datetime(work_df["price_date"])
    work_df["price_avg"] = work_df["price_avg"].astype(float)

    group_cols = ["product_id"] if "product_id" in work_df.columns else (
        ["category"] if "category" in work_df.columns else []
    )

    result_frames = []

    def _process_group(grp: pd.DataFrame) -> pd.DataFrame:
        g = grp.sort_values("price_date").copy().reset_index(drop=True)
        g["lag_1"] = g["price_avg"].shift(1)
        g["rolling_mean_3"] = (
            g["price_avg"].shift(1).rolling(window=3, min_periods=1).mean()
        )
        g["day_of_week"] = g["price_date"].dt.dayofweek
        g[TARGET_COLUMN] = g["price_avg"]
        return g

    if group_cols:
        for _, group in work_df.groupby(group_cols):
            result_frames.append(_process_group(group))
    else:
        result_frames.append(_process_group(work_df))

    result = pd.concat(result_frames, ignore_index=True)
    result = result.dropna(subset=["lag_1", TARGET_COLUMN]).reset_index(drop=True)

    # Kiểm tra tính toàn vẹn của features baseline sau tính toán
    if not result.empty:
        check_cols = BASELINE_FEATURES + [TARGET_COLUMN]
        if np.isinf(result[check_cols].to_numpy().astype(float)).any():
            raise ValueError("Phát hiện giá trị vô hạn (inf/-inf) trong ma trận đặc trưng Baseline sau khi tính toán.")
        if result[check_cols].isna().any().any():
            raise ValueError("Phát hiện giá trị NaN trong ma trận đặc trưng Baseline sau khi xử lý khuyết thiếu.")

    return result


def train_test_split_chronological(
    df: pd.DataFrame, test_ratio: float = TEST_RATIO
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Chia tập Train/Test theo trình tự thời gian độc lập cho từng sản phẩm (Per-product Chronological Split).
    
    Tập Test lấy tỷ lệ phần trăm quan sát cuối cùng (mặc định 20%) của mỗi chuỗi sản phẩm.
    Tuyệt đối không xáo trộn ngẫu nhiên (chống Data Leakage).
    Bảo toàn toàn bộ thông tin metadata (product_id, category, price_date,...).
    
    Lưu ý phương pháp luận:
    Hiện tại áp dụng chiến lược Per-product Chronological Split nhằm đảm bảo tất cả các mặt hàng
    đều có đại diện đánh giá trong cả tập Train và Test. Phương án thay thế là Global Chronological Split
    (cắt theo một mốc thời gian tuyệt đối chung cho toàn hệ thống), tuy nhiên có thể khiến các mặt hàng
    đã ngừng niêm yết trong quá khứ không có mẫu trong tập test hoặc các mặt hàng mới xuất hiện
    không có mẫu trong tập train. Quyết định phương pháp luận này được giữ nguyên trong đợt hardening
    và cần được trao đổi riêng nếu muốn chuyển sang Global Split.
    """
    # 1. Kiểm tra tham số test_ratio nghiêm ngặt
    if test_ratio is None or isinstance(test_ratio, bool):
        raise ValueError(
            f"Tham số test_ratio không hợp lệ: {test_ratio} ({type(test_ratio).__name__}). "
            "Giá trị bắt buộc phải là số thực thỏa mãn 0 < test_ratio < 1."
        )

    try:
        ratio_val = float(test_ratio)
    except (ValueError, TypeError):
        raise ValueError(f"Tham số test_ratio không thể chuyển đổi thành số thực: {test_ratio}")

    if np.isnan(ratio_val) or np.isinf(ratio_val) or not (0.0 < ratio_val < 1.0):
        raise ValueError(
            f"Tham số test_ratio không hợp lệ: {test_ratio}. "
            "Giá trị bắt buộc phải là số thực thỏa mãn 0 < test_ratio < 1."
        )

    # 2. Kiểm tra DataFrame đầu vào
    if df.empty:
        raise ValueError("Không thể chia tập Train/Test trên DataFrame rỗng.")

    train_frames, test_frames = [], []

    group_cols = ["product_id"] if "product_id" in df.columns else (
        ["category"] if "category" in df.columns else []
    )

    def _split_group(group: pd.DataFrame):
        grp = group.sort_values("price_date").reset_index(drop=True)
        n = len(grp)
        # Số lượng mẫu test cho chuỗi này
        n_test = max(1, int(n * ratio_val))
        if n <= 1:
            # Chuỗi quá ngắn (chỉ có 1 quan sát), không thể chia thành cả train và test
            print(f"[CẢNH BÁO] Chuỗi dữ liệu quá ngắn ({n} dòng), không đủ để phân chia train/test.")
            train_frames.append(grp)
        elif n <= n_test:
            # Toàn bộ thuộc test nếu lấy n_test >= n, nên giữ ít nhất 1 mẫu cho train
            train_frames.append(grp.iloc[:-1])
            test_frames.append(grp.iloc[-1:])
        else:
            train_frames.append(grp.iloc[:-n_test])
            test_frames.append(grp.iloc[-n_test:])

    if group_cols:
        for _, group in df.groupby(group_cols):
            _split_group(group)
    else:
        _split_group(df)

    train_df = pd.concat(train_frames, ignore_index=True) if train_frames else pd.DataFrame()
    test_df = pd.concat(test_frames, ignore_index=True) if test_frames else pd.DataFrame()

    # 3. Kiểm tra kết quả sau khi chia
    if train_df.empty or test_df.empty:
        raise ValueError(
            f"Tập dữ liệu sau khi chia không hợp lệ (train: {len(train_df)}, test: {len(test_df)}). "
            "Không thể tiến hành huấn luyện khi tập Train hoặc Test rỗng."
        )

    # 4. Đảm bảo toàn bộ các cột gốc (metadata) đều được bảo toàn nguyên vẹn
    for col in df.columns:
        if col not in train_df.columns or col not in test_df.columns:
            raise ValueError(f"Cột metadata '{col}' bị thất lạc sau quá trình chia train/test.")

    return train_df, test_df


def generate_synthetic_rice_data(
    start_date: str = "2026-05-01", n_days: int = 150
) -> pd.DataFrame:
    """
    Tạo bộ dữ liệu mô phỏng giá gạo chân thực phục vụ kiểm thử cục bộ khi
    CSDL không khả dụng hoặc khi chạy unit test.
    Mô phỏng 4 mặt hàng chính với xu hướng thực tế và bỏ qua ngày cuối tuần.
    """
    np.random.seed(RANDOM_SEED)

    # Sinh danh sách các ngày làm việc (thứ 2 đến thứ 6)
    dates = pd.date_range(start=start_date, periods=n_days * 2, freq="B")[:n_days]

    products_meta = [
        {"product_id": 1, "category": "NL IR 504", "base_price": 8500.0, "volatility": 45.0},
        {"product_id": 4, "category": "Cám", "base_price": 7200.0, "volatility": 35.0},
        {"product_id": 13, "category": "Tấm thơm", "base_price": 9500.0, "volatility": 55.0},
        {"product_id": 14, "category": "NL OM 5451", "base_price": 10200.0, "volatility": 60.0},
    ]

    all_rows = []
    for p in products_meta:
        price = p["base_price"]
        trend = np.random.choice([-1, 1]) * 2.5
        for d in dates:
            noise = np.random.normal(0, p["volatility"])
            price = max(4000.0, price + trend + noise)
            p_min = round(price - np.random.uniform(50, 150), -1)
            p_max = round(price + np.random.uniform(50, 150), -1)
            p_avg = (p_min + p_max) / 2.0
            all_rows.append(
                {
                    "product_id": p["product_id"],
                    "category": p["category"],
                    "price_date": d,
                    "price_min": p_min,
                    "price_max": p_max,
                    "price_avg": p_avg,
                }
            )

    df = pd.DataFrame(all_rows)
    return df.sort_values(["category", "price_date"]).reset_index(drop=True)


def load_dataset(crop_type: str = "rice") -> Tuple[pd.DataFrame, bool]:
    """
    Tải dữ liệu giá từ CSDL thông qua build_features.load_price_data.
    Nếu không kết nối được hoặc CSDL trống, tự động chuyển sang chế độ
    dữ liệu giả lập (synthetic) và thông báo minh bạch.
    
    Trả về: (DataFrame dữ liệu, is_synthetic: bool)
    """
    try:
        from build_features import load_price_data
        df = load_price_data(crop_type=crop_type)
        if not df.empty:
            print(f"[DATA] Đã tải thành công {len(df)} dòng dữ liệu THỰC TẾ từ CSDL Neon Cloud.")
            return df, False
        else:
            print("[DATA] CSDL kết nối được nhưng không có dữ liệu giá. Chuyển sang dữ liệu mô phỏng.")
    except Exception as e:
        print(f"[DATA] Không thể truy cập CSDL ({type(e).__name__}). Chuyển sang dữ liệu mô phỏng cục bộ.")

    synth_df = generate_synthetic_rice_data()
    print(f"[DATA] Đã tạo {len(synth_df)} dòng dữ liệu MÔ PHỎNG (Synthetic) để kiểm thử.")
    return synth_df, True


def compute_metrics(y_true, y_pred) -> Dict[str, float]:
    """
    Tính toán các chỉ số đánh giá sai số: MAE và RMSE.
    
    Ràng buộc nghiêm ngặt:
    - Bắt buộc y_true và y_pred phải có cùng kích thước (shape).
    - Yêu cầu dữ liệu 1 chiều (1D array).
    - Từ chối mảng rỗng, giá trị NaN, hoặc giá trị vô hạn (inf/-inf).
    """
    y_t = np.asarray(y_true)
    y_p = np.asarray(y_pred)

    # 1. Kiểm tra mảng rỗng
    if y_t.size == 0 or y_p.size == 0:
        raise ValueError("Không thể tính toán metrics trên mảng rỗng.")

    # 2. Kiểm tra dữ liệu 1 chiều
    if y_t.ndim != 1 or y_p.ndim != 1:
        raise ValueError(
            f"compute_metrics yêu cầu dữ liệu 1 chiều (1D), nhận được y_true: {y_t.ndim}D, y_pred: {y_p.ndim}D."
        )

    # 3. Kiểm tra cùng shape / kích thước
    if y_t.shape != y_p.shape:
        raise ValueError(
            f"y_true và y_pred bắt buộc phải có cùng kích thước. "
            f"Nhận được y_true.shape={y_t.shape}, y_pred.shape={y_p.shape}."
        )

    # 4. Ép kiểu số và kiểm tra tính toàn vẹn
    try:
        y_t = y_t.astype(float)
        y_p = y_p.astype(float)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Dữ liệu y_true hoặc y_pred không thể chuyển đổi thành số thực: {e}")

    if np.isnan(y_t).any() or np.isnan(y_p).any():
        raise ValueError("Phát hiện giá trị NaN trong mảng y_true hoặc y_pred khi tính metrics.")

    if np.isinf(y_t).any() or np.isinf(y_p).any():
        raise ValueError("Phát hiện giá trị vô hạn (inf/-inf) trong mảng y_true hoặc y_pred khi tính metrics.")

    mae = float(np.mean(np.abs(y_t - y_p)))
    rmse = float(np.sqrt(np.mean((y_t - y_p) ** 2)))
    return {"MAE": mae, "RMSE": rmse}


def run_model_comparison(
    train_df: pd.DataFrame, test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, np.ndarray], RandomForestRegressor]:
    """
    So sánh công bằng giữa Baseline Feature Set và Enhanced Feature Set
    trên 2 thuật toán: Linear Regression và Random Forest.
    
    Đảm bảo 100% tập Test sử dụng cùng các mẫu và cùng các ngày quan sát.
    Bảo toàn toàn bộ thông tin metadata (product_id, category, price_date).
    """
    if train_df.empty or test_df.empty:
        raise ValueError(
            f"Không thể huấn luyện mô hình khi tập dữ liệu rỗng (train: {len(train_df)}, test: {len(test_df)})."
        )

    # Kiểm tra sự hiện diện của metadata bắt buộc (product_id, category, price_date)
    missing_meta_train = [col for col in REQUIRED_METADATA if col not in train_df.columns]
    if missing_meta_train:
        raise ValueError(
            f"Tập dữ liệu Train (train_df) thiếu các cột metadata bắt buộc: {missing_meta_train}. "
            f"Yêu cầu đầy đủ {REQUIRED_METADATA} để bảo đảm tính truy nguyên và trực quan hóa."
        )

    missing_meta_test = [col for col in REQUIRED_METADATA if col not in test_df.columns]
    if missing_meta_test:
        raise ValueError(
            f"Tập dữ liệu Test (test_df) thiếu các cột metadata bắt buộc: {missing_meta_test}. "
            f"Yêu cầu đầy đủ {REQUIRED_METADATA} để bảo đảm tính truy nguyên và trực quan hóa."
        )

    # Kiểm tra cột mục tiêu
    if TARGET_COLUMN not in train_df.columns or TARGET_COLUMN not in test_df.columns:
        raise ValueError(f"Tập Train hoặc Test thiếu cột mục tiêu '{TARGET_COLUMN}'.")

    # Kiểm tra tính toàn vẹn của Target
    if train_df[TARGET_COLUMN].isna().any() or test_df[TARGET_COLUMN].isna().any():
        raise ValueError("Phát hiện giá trị NaN trong cột mục tiêu của tập Train hoặc Test.")
    if np.isinf(train_df[TARGET_COLUMN].to_numpy().astype(float)).any() or np.isinf(test_df[TARGET_COLUMN].to_numpy().astype(float)).any():
        raise ValueError("Phát hiện giá trị vô hạn trong cột mục tiêu của tập Train hoặc Test.")

    # Kiểm tra các cột đặc trưng bắt buộc
    missing_features_train = set(ENHANCED_FEATURES) - set(train_df.columns)
    missing_features_test = set(ENHANCED_FEATURES) - set(test_df.columns)
    if missing_features_train or missing_features_test:
        raise ValueError(f"Thiếu các cột đặc trưng bắt buộc: {missing_features_train | missing_features_test}")

    # Kiểm tra tính toàn vẹn của Features
    if train_df[ENHANCED_FEATURES].isna().any().any() or test_df[ENHANCED_FEATURES].isna().any().any():
        raise ValueError("Phát hiện giá trị NaN trong ma trận đặc trưng của tập Train hoặc Test.")
    if np.isinf(train_df[ENHANCED_FEATURES].to_numpy().astype(float)).any() or np.isinf(test_df[ENHANCED_FEATURES].to_numpy().astype(float)).any():
        raise ValueError("Phát hiện giá trị vô hạn trong ma trận đặc trưng của tập Train hoặc Test.")

    y_train = train_df[TARGET_COLUMN].to_numpy()
    y_test = test_df[TARGET_COLUMN].to_numpy()

    n_train = len(train_df)
    n_test = len(test_df)

    results = []
    predictions: Dict[str, np.ndarray] = {"Actual": y_test}

    # 1. Linear Regression - Baseline Features
    lr_base = LinearRegression()
    lr_base.fit(train_df[BASELINE_FEATURES], y_train)
    pred_lr_base = lr_base.predict(test_df[BASELINE_FEATURES])
    m_lr_base = compute_metrics(y_test, pred_lr_base)
    results.append(
        {
            "feature_set": "Baseline",
            "model": "Linear Regression",
            "mae": round(m_lr_base["MAE"], 2),
            "rmse": round(m_lr_base["RMSE"], 2),
            "train_samples": n_train,
            "test_samples": n_test,
        }
    )
    predictions["Linear Regression (Baseline)"] = pred_lr_base

    # 2. Linear Regression - Enhanced Features
    lr_enh = LinearRegression()
    lr_enh.fit(train_df[ENHANCED_FEATURES], y_train)
    pred_lr_enh = lr_enh.predict(test_df[ENHANCED_FEATURES])
    m_lr_enh = compute_metrics(y_test, pred_lr_enh)
    results.append(
        {
            "feature_set": "Enhanced",
            "model": "Linear Regression",
            "mae": round(m_lr_enh["MAE"], 2),
            "rmse": round(m_lr_enh["RMSE"], 2),
            "train_samples": n_train,
            "test_samples": n_test,
        }
    )
    predictions["Linear Regression (Enhanced)"] = pred_lr_enh

    # 3. Random Forest - Baseline Features
    rf_base = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED)
    rf_base.fit(train_df[BASELINE_FEATURES], y_train)
    pred_rf_base = rf_base.predict(test_df[BASELINE_FEATURES])
    m_rf_base = compute_metrics(y_test, pred_rf_base)
    results.append(
        {
            "feature_set": "Baseline",
            "model": "Random Forest",
            "mae": round(m_rf_base["MAE"], 2),
            "rmse": round(m_rf_base["RMSE"], 2),
            "train_samples": n_train,
            "test_samples": n_test,
        }
    )
    predictions["Random Forest (Baseline)"] = pred_rf_base

    # 4. Random Forest - Enhanced Features
    rf_enh = RandomForestRegressor(n_estimators=100, random_state=RANDOM_SEED)
    rf_enh.fit(train_df[ENHANCED_FEATURES], y_train)
    pred_rf_enh = rf_enh.predict(test_df[ENHANCED_FEATURES])
    m_rf_enh = compute_metrics(y_test, pred_rf_enh)
    results.append(
        {
            "feature_set": "Enhanced",
            "model": "Random Forest",
            "mae": round(m_rf_enh["MAE"], 2),
            "rmse": round(m_rf_enh["RMSE"], 2),
            "train_samples": n_train,
            "test_samples": n_test,
        }
    )
    predictions["Random Forest (Enhanced)"] = pred_rf_enh

    results_df = pd.DataFrame(results)
    return results_df, predictions, rf_enh


def plot_price_history_all(
    df: pd.DataFrame, output_path: Path, is_synthetic: bool = False, from_date: Optional[str] = "2026-09-01"
) -> None:
    """
    Biểu đồ 1: docs/figures/price_history_all.png
    Thể hiện xu hướng biến động giá của tất cả các danh mục gạo (từ tháng 9 đến nay).
    Mỗi loại gạo một đường màu riêng biệt kèm chú giải legend rõ ràng.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plot_df = df.copy()
    plot_df["price_date"] = pd.to_datetime(plot_df["price_date"])

    date_filtered = False
    if from_date:
        ts_from = pd.Timestamp(from_date)
        if (plot_df["price_date"] >= ts_from).any():
            plot_df = plot_df[plot_df["price_date"] >= ts_from].reset_index(drop=True)
            date_filtered = True

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

    # Bảng màu hài hòa, phân biệt rõ
    categories = sorted(plot_df["category"].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, max(len(categories), 1)))

    for idx, cat in enumerate(categories):
        cat_df = plot_df[plot_df["category"] == cat].sort_values("price_date")
        ax.plot(
            cat_df["price_date"],
            cat_df["price_avg"],
            marker="o",
            markersize=3,
            linewidth=1.8,
            label=cat,
            color=colors[idx % len(colors)],
            alpha=0.9,
        )

    title_suffix = " [Dữ liệu mô phỏng]" if is_synthetic else " [Dữ liệu CSDL Neon]"
    title_time = "từ tháng 09/2026 đến nay" if date_filtered else "qua các phiên giao dịch"
    ax.set_title(
        f"Lịch sử biến động giá lúa gạo {title_time}{title_suffix}",
        fontsize=14,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Thời gian (Ngày giao dịch)", fontsize=11, labelpad=10)
    ax.set_ylabel("Giá trung bình (VND/kg)", fontsize=11, labelpad=10)

    # Định dạng trục ngày tháng
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
    fig.autofmt_xdate(rotation=30, ha="right")

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(
        title="Mặt hàng gạo",
        title_fontsize=10,
        fontsize=9,
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        borderaxespad=0.0,
    )
    plt.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIGURE 1] Đã lưu biểu đồ lịch sử giá vào: {output_path}")


def plot_actual_vs_predicted(
    y_true: np.ndarray,
    predictions: Dict[str, np.ndarray],
    output_path: Path,
    is_synthetic: bool = False,
) -> None:
    """
    Biểu đồ 2: docs/figures/actual_vs_predicted.png
    Biểu đồ phân tán Giá thực tế (X) vs Giá dự báo (Y) kèm đường lý tưởng y = x.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 8), dpi=300)

    # Đường tham chiếu y = x
    min_val = min(float(y_true.min()), min(float(p.min()) for k, p in predictions.items() if k != "Actual"))
    max_val = max(float(y_true.max()), max(float(p.max()) for k, p in predictions.items() if k != "Actual"))
    padding = (max_val - min_val) * 0.05
    line_min = min_val - padding
    line_max = max_val + padding

    ax.plot(
        [line_min, line_max],
        [line_min, line_max],
        color="crimson",
        linestyle="--",
        linewidth=2,
        label="Đường lý tưởng (y = x)",
        zorder=2,
    )

    style_map = {
        "Linear Regression (Baseline)": {"color": "#4e79a7", "marker": "o", "alpha": 0.65},
        "Linear Regression (Enhanced)": {"color": "#2ca02c", "marker": "^", "alpha": 0.75},
        "Random Forest (Baseline)": {"color": "#f28e2b", "marker": "s", "alpha": 0.65},
        "Random Forest (Enhanced)": {"color": "#d62728", "marker": "D", "alpha": 0.8},
    }

    for name, pred in predictions.items():
        if name == "Actual":
            continue
        cfg = style_map.get(name, {"color": "gray", "marker": "x", "alpha": 0.6})
        ax.scatter(
            y_true,
            pred,
            color=cfg["color"],
            marker=cfg["marker"],
            alpha=cfg["alpha"],
            s=45,
            edgecolors="none",
            label=name,
            zorder=3,
        )

    title_suffix = " (Demo Synthetic)" if is_synthetic else " (Thực nghiệm CSDL)"
    ax.set_title(
        f"So sánh Giá thực tế vs Giá dự báo trên tập kiểm thử{title_suffix}",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.set_xlabel("Giá thực tế - Actual Price (VND/kg)", fontsize=11, labelpad=10)
    ax.set_ylabel("Giá dự báo - Predicted Price (VND/kg)", fontsize=11, labelpad=10)
    ax.set_xlim(line_min, line_max)
    ax.set_ylim(line_min, line_max)
    ax.grid(True, linestyle="--", alpha=0.5, zorder=1)
    ax.legend(loc="upper left", framealpha=0.9, fontsize=9.5)

    plt.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIGURE 2] Đã lưu biểu đồ Actual vs Predicted vào: {output_path}")


def plot_feature_importance(
    rf_model: RandomForestRegressor,
    feature_names: List[str],
    output_path: Path,
    is_synthetic: bool = False,
) -> None:
    """
    Biểu đồ 3: docs/figures/feature_importance.png
    Biểu đồ cột nằm ngang thể hiện độ quan trọng của các đặc trưng (Enhanced Features).
    Sắp xếp theo thứ tự đóng góp và ghi chú rõ ý nghĩa dự báo (predictive power vs causality).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    importances = rf_model.feature_importances_
    indices = np.argsort(importances)

    sorted_features = [feature_names[i] for i in indices]
    sorted_importances = importances[indices]

    # Đặt nhãn giải thích tiếng Việt cho từng đặc trưng
    feature_labels = {
        "lag_1": "lag_1: Giá phiên hôm trước (t-1)",
        "lag_2": "lag_2: Giá phiên 2 hôm trước (t-2)",
        "lag_7": "lag_7: Giá phiên tuần trước (t-7)",
        "rolling_mean_3": "rolling_mean_3: TB trượt 3 phiên gần nhất",
        "rolling_mean_7": "rolling_mean_7: TB trượt 7 phiên gần nhất",
        "price_change": "price_change: Chênh lệch giá (t-1) - (t-2)",
        "day_of_week": "day_of_week: Thứ trong tuần (chu kỳ tuần)",
    }
    display_names = [feature_labels.get(f, f) for f in sorted_features]

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)
    bars = ax.barh(range(len(sorted_features)), sorted_importances, color="#1f77b4", alpha=0.85, height=0.6)

    # Hiển thị giá trị phần trăm trên từng thanh
    for bar in bars:
        width = bar.get_width()
        ax.text(
            width + 0.005,
            bar.get_y() + bar.get_height() / 2,
            f"{width:.3f} ({width * 100:.1f}%)",
            va="center",
            ha="left",
            fontsize=9,
            color="#333333",
            fontweight="bold",
        )

    ax.set_yticks(range(len(sorted_features)))
    ax.set_yticklabels(display_names, fontsize=10)
    ax.set_xlabel("Độ quan trọng (Gini Feature Importance)", fontsize=11, labelpad=10)

    title_suffix = " (Demo Synthetic)" if is_synthetic else " (Mô hình Random Forest)"
    ax.set_title(
        f"Độ quan trọng của các đặc trưng nâng cao (Enhanced Features){title_suffix}",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    ax.set_xlim(0, max(sorted_importances) * 1.25)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # Chú thích học thuật quan trọng: Predictive contribution != Causality
    ax.text(
        0.0,
        -0.18,
        "Lưu ý: Độ quan trọng đặc trưng đo lường mức độ đóng góp giảm phương sai khi phân tách cây quyết định\n"
        "(Predictive Contribution), không mang ý nghĩa là quan hệ nhân quả kinh tế trực tiếp (Causality).",
        transform=ax.transAxes,
        fontsize=8.5,
        fontstyle="italic",
        color="#555555",
    )

    plt.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"[FIGURE 3] Đã lưu biểu đồ Feature Importance vào: {output_path}")


def run_experiment() -> pd.DataFrame:
    """
    Hàm thực thi toàn bộ quy trình thử nghiệm:
    1. Tải dữ liệu (CSDL thực tế hoặc dữ liệu mô phỏng fallback)
    2. Xuất Figure 1: price_history_all.png
    3. Xây dựng bộ đặc trưng Enhanced
    4. Chia tập Train/Test theo thời gian
    5. Đánh giá so sánh Baseline vs Enhanced trên Linear Regression & Random Forest
    6. Xuất Figure 2: actual_vs_predicted.png
    7. Xuất Figure 3: feature_importance.png
    8. Xuất bảng kết quả ra file docs/feature_comparison_results.csv
    """
    print("=" * 80)
    print("BẮT ĐẦU THỰC NGHIỆM KỸ THUẬT ĐẶC TRƯNG (FEATURE ENGINEERING) — AGRISIGHT")
    print("Thành viên phụ trách: TÂM (Nhóm 08)")
    print("=" * 80)

    # 1. Tải dữ liệu
    raw_df, is_synthetic = load_dataset(crop_type="rice")

    # 2. Tạo Figure 1: Lịch sử giá toàn bộ các loại gạo
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig1_path = FIGURES_DIR / "price_history_all.png"
    plot_price_history_all(raw_df, fig1_path, is_synthetic=is_synthetic)

    # 3. Tạo bộ đặc trưng nâng cao
    print("\n[FEATURES] Đang tính toán các đặc trưng nâng cao (lags, rolling means, price change)...")
    enhanced_df = build_enhanced_features(raw_df)
    print(f"[FEATURES] Tổng số quan sát sau khi tạo đặc trưng và loại bỏ warmup: {len(enhanced_df)}")

    # 4. Chia tập Train / Test theo thời gian (80% train, 20% test cuối)
    train_df, test_df = train_test_split_chronological(enhanced_df, test_ratio=TEST_RATIO)
    print(f"[SPLIT] Kích thước tập Train: {len(train_df)} mẫu | Kích thước tập Test: {len(test_df)} mẫu")

    # 5. Huấn luyện và so sánh mô hình
    print("\n[TRAINING] Đang huấn luyện và đánh giá Linear Regression & Random Forest...")
    results_df, predictions, rf_enh_model = run_model_comparison(train_df, test_df)

    # 6. Tạo Figure 2: Actual vs Predicted
    fig2_path = FIGURES_DIR / "actual_vs_predicted.png"
    plot_actual_vs_predicted(predictions["Actual"], predictions, fig2_path, is_synthetic=is_synthetic)

    # 7. Tạo Figure 3: Feature Importance của Random Forest
    fig3_path = FIGURES_DIR / "feature_importance.png"
    plot_feature_importance(rf_enh_model, ENHANCED_FEATURES, fig3_path, is_synthetic=is_synthetic)

    # 8. Xuất kết quả CSV
    CSV_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(CSV_OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\n[CSV] Đã xuất kết quả so sánh ra file: {CSV_OUTPUT_PATH}")

    # In bảng tóm tắt kết quả
    print("\n" + "=" * 80)
    print("BẢNG TỔNG HỢP KẾT QUẢ SO SÁNH: BASELINE vs ENHANCED FEATURES")
    print("=" * 80)
    print(f"{'Feature Set':<15} | {'Mô hình':<20} | {'MAE (VND/kg)':>12} | {'RMSE (VND/kg)':>13} | {'Train':>6} | {'Test':>6}")
    print("-" * 80)
    for _, row in results_df.iterrows():
        print(
            f"{row['feature_set']:<15} | {row['model']:<20} | "
            f"{row['mae']:>12.2f} | {row['rmse']:>13.2f} | "
            f"{row['train_samples']:>6} | {row['test_samples']:>6}"
        )
    print("=" * 80)

    # Đánh giá mức độ cải thiện
    lr_base_mae = results_df.loc[(results_df['feature_set'] == 'Baseline') & (results_df['model'] == 'Linear Regression'), 'mae'].values[0]
    lr_enh_mae = results_df.loc[(results_df['feature_set'] == 'Enhanced') & (results_df['model'] == 'Linear Regression'), 'mae'].values[0]
    rf_base_mae = results_df.loc[(results_df['feature_set'] == 'Baseline') & (results_df['model'] == 'Random Forest'), 'mae'].values[0]
    rf_enh_mae = results_df.loc[(results_df['feature_set'] == 'Enhanced') & (results_df['model'] == 'Random Forest'), 'mae'].values[0]

    lr_diff = (lr_enh_mae - lr_base_mae) / lr_base_mae * 100
    rf_diff = (rf_enh_mae - rf_base_mae) / rf_base_mae * 100

    print("\nNHẬN XÉT ĐÁNH GIÁ:")
    print(f"1. Linear Regression: MAE thay đổi từ {lr_base_mae:.2f} sang {lr_enh_mae:.2f} ({lr_diff:+.2f}%)")
    print(f"2. Random Forest: MAE thay đổi từ {rf_base_mae:.2f} sang {rf_enh_mae:.2f} ({rf_diff:+.2f}%)")
    print("=" * 80)

    return results_df


if __name__ == "__main__":
    run_experiment()

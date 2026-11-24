"""
Unit and Integration Tests for Enhanced Feature Engineering (AgriSight - Nhóm 08)
Thành viên: TÂM

Kiểm thử toàn diện:
1. Tính toán giá trị trễ (lag_1, lag_2, lag_7).
2. Trung bình trượt rolling_mean_3, rolling_mean_7 loại trừ giá trị mục tiêu hiện tại (ngăn target leakage).
3. Tính toán biến động giá (price_change = lag_1 - lag_2).
4. Tính toán độc lập theo từng sản phẩm (product_id), không trộn lẫn dữ liệu.
5. Sắp xếp thứ tự thời gian (chronological ordering) tự động trước khi tính.
6. Xử lý giá trị khuyết thiếu do phép trễ (loại bỏ warmup, không điền 0).
7. Kiểm tra chống rò rỉ dữ liệu mục tiêu (no target leakage).
8. So sánh công bằng: Baseline và Enhanced dùng 100% mẫu test giống hệt nhau.
9. Huấn luyện mô hình Linear Regression và Random Forest thành công, metrics hợp lệ.
10. Sinh đầy đủ các file đầu ra (PNG biểu đồ và CSV kết quả).

Edge cases & Hardening validations:
11. DataFrame rỗng (Empty DataFrame xử lý an toàn).
12. Dữ liệu lịch sử không đủ 8 quan sát (Insufficient historical observations).
13. Nhiều sản phẩm có cùng tên category (Multiple products sharing same category).
14. Khoảng cách ngày không liên tục, nghỉ cuối tuần (Missing dates / Weekend gaps).
15. Kiểm tra dữ liệu mục tiêu Target chứa NaN.
16. Kiểm tra dữ liệu chứa giá trị vô hạn (inf/-inf).
17. Kiểm tra giá trị test_ratio không hợp lệ (bằng 0, bằng 1, âm, lớn hơn 1).
18. Kiểm tra bản ghi trùng lặp đồng thời product_id và price_date.
19. Kiểm tra nhóm dữ liệu thiếu định danh (product_id bị NaN/None).
20. Kiểm tra ngăn chặn tập dữ liệu Train hoặc Test rỗng.
21. Kiểm tra nhiều sản phẩm có cùng mốc ngày giao dịch (Multiple products on same date).
22. Kiểm tra tính đúng đắn và bảo toàn metadata (product_id, category, price_date).

Final Code Quality Hardening Tests:
23. price_date chứa NaT hoặc ngày không thể phân tích (invalid date string).
24. price_avg chứa giá trị không thể chuyển đổi thành số thực (non-numeric string).
25. target chứa NaN hoặc Inf khi đã có sẵn cột target trong DataFrame.
26. compute_metrics với hai mảng khác kích thước (shape mismatch).
27. compute_metrics với dữ liệu nhiều chiều (multidimensional 2D array).
28. test_ratio với các kiểu dữ liệu đặc biệt: None, Boolean (True, False), NaN, Inf.
29. category chứa NaN trong khi product_id vẫn hoàn toàn hợp lệ.
30. Metadata (product_id, category, price_date, price_min, price_max) được bảo toàn nguyên vẹn qua train_test_split.
31. Bản ghi trùng lặp cùng ngày nhưng khác source (source A vs source B): xác nhận từ chối an toàn, không tự ý drop hay aggregate.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Đường dẫn dự án
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(REPO_ROOT / "ml" / "experiments"))

from enhanced_features import (
    BASELINE_FEATURES,
    ENHANCED_FEATURES,
    TARGET_COLUMN,
    build_enhanced_features,
    build_baseline_features,
    train_test_split_chronological,
    compute_metrics,
    run_model_comparison,
    generate_synthetic_rice_data,
    plot_price_history_all,
    plot_actual_vs_predicted,
    plot_feature_importance,
)


class TestEnhancedFeatures(unittest.TestCase):
    def setUp(self):
        """Khởi tạo tập dữ liệu mẫu chuẩn cho 1 sản phẩm."""
        dates = pd.date_range("2026-06-01", periods=15, freq="D")
        prices = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 190.0, 200.0, 210.0, 220.0, 230.0, 240.0]
        self.sample_df = pd.DataFrame(
            {
                "product_id": [1] * 15,
                "category": ["NL IR 504"] * 15,
                "price_date": dates,
                "price_min": [p - 10 for p in prices],
                "price_max": [p + 10 for p in prices],
                "price_avg": prices,
            }
        )

    def test_1_lag_calculations(self):
        """1. Kiểm tra tính chính xác của lag_1, lag_2, lag_7."""
        res = build_enhanced_features(self.sample_df)
        self.assertGreater(len(res), 0)

        # Dòng đầu tiên sau khi loại bỏ 7 dòng warmup tương ứng với ngày thứ 8 (index 7 của prices gốc = 170.0)
        row_0 = res.iloc[0]
        self.assertEqual(row_0["target"], 170.0)
        self.assertEqual(row_0["lag_1"], 160.0)  # t-1 (index 6)
        self.assertEqual(row_0["lag_2"], 150.0)  # t-2 (index 5)
        self.assertEqual(row_0["lag_7"], 100.0)  # t-7 (index 0)

        # Dòng tiếp theo (index 8 của prices gốc = 180.0)
        row_1 = res.iloc[1]
        self.assertEqual(row_1["target"], 180.0)
        self.assertEqual(row_1["lag_1"], 170.0)
        self.assertEqual(row_1["lag_2"], 160.0)
        self.assertEqual(row_1["lag_7"], 110.0)

    def test_2_rolling_means_exclude_current_target(self):
        """2. Kiểm tra rolling_mean_3 và rolling_mean_7 không chứa target hiện tại."""
        res = build_enhanced_features(self.sample_df)
        row_0 = res.iloc[0]  # target = 170.0

        # rolling_mean_3 tại t=7 phải là trung bình của t=4, 5, 6 (140, 150, 160) -> 150.0
        expected_rm3 = (140.0 + 150.0 + 160.0) / 3.0
        self.assertAlmostEqual(row_0["rolling_mean_3"], expected_rm3)

        # rolling_mean_7 tại t=7 phải là trung bình của t=0..6 (100, 110, 120, 130, 140, 150, 160) -> 130.0
        expected_rm7 = sum([100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0]) / 7.0
        self.assertAlmostEqual(row_0["rolling_mean_7"], expected_rm7)

        # Tuyệt đối không chứa 170.0 trong rolling mean
        self.assertNotEqual(row_0["rolling_mean_3"], (150.0 + 160.0 + 170.0) / 3.0)

    def test_3_price_change_calculation(self):
        """3. Kiểm tra biến động giá: price_change = price(t-1) - price(t-2)."""
        res = build_enhanced_features(self.sample_df)
        row_0 = res.iloc[0]
        # t-1 = 160.0, t-2 = 150.0 -> price_change = 10.0
        self.assertEqual(row_0["price_change"], 10.0)
        self.assertEqual(row_0["price_change"], row_0["lag_1"] - row_0["lag_2"])

    def test_4_features_calculated_independently_per_product(self):
        """4. Kiểm tra tính độc lập giữa các sản phẩm (không rò rỉ chéo product_id)."""
        dates = pd.date_range("2026-06-01", periods=10, freq="D")
        df1 = pd.DataFrame(
            {
                "product_id": [10] * 10,
                "category": ["Gạo A"] * 10,
                "price_date": dates,
                "price_avg": [1000.0 + i * 10 for i in range(10)],
            }
        )
        df2 = pd.DataFrame(
            {
                "product_id": [20] * 10,
                "category": ["Gạo B"] * 10,
                "price_date": dates,
                "price_avg": [5000.0 + i * 50 for i in range(10)],
            }
        )
        combined = pd.concat([df1, df2], ignore_index=True)

        res = build_enhanced_features(combined)

        p1_res = res[res["product_id"] == 10]
        p2_res = res[res["product_id"] == 20]

        # Kiểm tra giá trị lag của product 2 hoàn toàn nằm trong dải 5000+, không dính 1000+ của product 1
        self.assertTrue((p2_res["lag_1"] >= 5000.0).all())
        self.assertTrue((p2_res["lag_7"] >= 5000.0).all())
        self.assertTrue((p1_res["lag_1"] <= 2000.0).all())

    def test_5_chronological_ordering(self):
        """5. Kiểm tra tự động sắp xếp theo thứ tự thời gian nếu dữ liệu đầu vào bị xáo trộn."""
        shuffled_df = self.sample_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
        res = build_enhanced_features(shuffled_df)

        # res phải được sắp xếp tuần tự theo price_date
        self.assertTrue(res["price_date"].is_monotonic_increasing)
        # Các giá trị lag phải khớp chuẩn như khi không xáo trộn
        self.assertEqual(res.iloc[0]["target"], 170.0)
        self.assertEqual(res.iloc[0]["lag_1"], 160.0)

    def test_6_missing_values_handled_without_zero(self):
        """6. Kiểm tra xử lý missing values: loại bỏ warmup, không điền 0."""
        res = build_enhanced_features(self.sample_df)
        # Không còn bất kỳ giá trị NaN nào trong các đặc trưng
        self.assertFalse(res[ENHANCED_FEATURES].isna().any().any())
        # Không có giá trị 0 nào được gán bừa bãi vào lag
        self.assertFalse((res[ENHANCED_FEATURES] == 0).any()["lag_1"])
        self.assertFalse((res[ENHANCED_FEATURES] == 0).any()["lag_7"])

    def test_7_no_target_leakage(self):
        """7. Kiểm tra chống rò rỉ dữ liệu mục tiêu (Target Leakage)."""
        df_modified = self.sample_df.copy()
        # Thay đổi giá target tại index 7 thành một số lớn (ví dụ: 999999.0)
        df_modified.loc[7, "price_avg"] = 999999.0

        res_orig = build_enhanced_features(self.sample_df)
        res_mod = build_enhanced_features(df_modified)

        # Tại phiên đó (row_0), các đặc trưng quá khứ (lag, rolling, price_change)
        # KHÔNG ĐƯỢC PHÉP thay đổi vì chúng chỉ nhìn về quá khứ!
        for feat in ["lag_1", "lag_2", "lag_7", "rolling_mean_3", "rolling_mean_7", "price_change"]:
            self.assertEqual(res_orig.iloc[0][feat], res_mod.iloc[0][feat])

    def test_8_identical_test_observations(self):
        """8. Kiểm tra tính công bằng: Baseline và Enhanced dùng chung 100% mẫu test."""
        synth_df = generate_synthetic_rice_data(n_days=100)
        enh_df = build_enhanced_features(synth_df)

        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)
        results_df, predictions, _ = run_model_comparison(train_df, test_df)

        # Cả 2 mô hình và 2 bộ đặc trưng đều dự báo trên cùng y_test
        y_test = test_df[TARGET_COLUMN].to_numpy()
        np.testing.assert_array_equal(predictions["Actual"], y_test)
        self.assertEqual(len(predictions["Linear Regression (Baseline)"]), len(y_test))
        self.assertEqual(len(predictions["Linear Regression (Enhanced)"]), len(y_test))
        self.assertEqual(len(predictions["Random Forest (Baseline)"]), len(y_test))
        self.assertEqual(len(predictions["Random Forest (Enhanced)"]), len(y_test))

    def test_9_model_training_and_metrics(self):
        """9. Kiểm tra huấn luyện mô hình thành công và xuất metrics MAE, RMSE hợp lệ."""
        synth_df = generate_synthetic_rice_data(n_days=50)
        enh_df = build_enhanced_features(synth_df)
        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)

        results_df, _, rf_model = run_model_comparison(train_df, test_df)

        self.assertEqual(len(results_df), 4)  # 2 models x 2 feature sets
        self.assertTrue((results_df["mae"] > 0).all())
        self.assertTrue((results_df["rmse"] > 0).all())
        self.assertTrue((results_df["rmse"] >= results_df["mae"]).all())  # RMSE luôn >= MAE
        self.assertIsNotNone(rf_model)
        self.assertEqual(len(rf_model.feature_importances_), len(ENHANCED_FEATURES))

    def test_10_output_files_generation(self):
        """10. Kiểm tra khả năng tạo tất cả file ảnh PNG và file CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fig1 = tmp_path / "price_history_all.png"
            fig2 = tmp_path / "actual_vs_predicted.png"
            fig3 = tmp_path / "feature_importance.png"
            csv_path = tmp_path / "feature_comparison_results.csv"

            synth_df = generate_synthetic_rice_data(n_days=30)
            enh_df = build_enhanced_features(synth_df)
            train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)
            results_df, predictions, rf_model = run_model_comparison(train_df, test_df)

            plot_price_history_all(synth_df, fig1, is_synthetic=True)
            plot_actual_vs_predicted(predictions["Actual"], predictions, fig2, is_synthetic=True)
            plot_feature_importance(rf_model, ENHANCED_FEATURES, fig3, is_synthetic=True)
            results_df.to_csv(csv_path, index=False)

            self.assertTrue(fig1.exists() and fig1.stat().st_size > 0)
            self.assertTrue(fig2.exists() and fig2.stat().st_size > 0)
            self.assertTrue(fig3.exists() and fig3.stat().st_size > 0)
            self.assertTrue(csv_path.exists() and csv_path.stat().st_size > 0)

    def test_edge_case_empty_dataframe(self):
        """Edge case 11: DataFrame rỗng không gây crash."""
        empty_df = pd.DataFrame()
        res = build_enhanced_features(empty_df)
        self.assertTrue(res.empty)

    def test_edge_case_insufficient_historical_observations(self):
        """Edge case 12: Sản phẩm có ít hơn 8 dòng quan sát thì loại bỏ an toàn, không lỗi."""
        short_df = pd.DataFrame(
            {
                "product_id": [99] * 5,
                "category": ["Gạo thử nghiệm"] * 5,
                "price_date": pd.date_range("2026-07-01", periods=5, freq="D"),
                "price_avg": [8000.0, 8100.0, 8200.0, 8150.0, 8250.0],
            }
        )
        res = build_enhanced_features(short_df)
        # Vì cần tối thiểu 7 dòng lag + 1 dòng mục tiêu, 5 dòng sẽ bị dropna
        self.assertEqual(len(res), 0)

    def test_edge_case_multiple_products_sharing_same_category(self):
        """Edge case 13: 2 sản phẩm khác product_id nhưng cùng category không bị gộp chung."""
        dates = pd.date_range("2026-06-01", periods=10, freq="D")
        p1 = pd.DataFrame(
            {
                "product_id": [101] * 10,
                "category": ["Gạo thơm"] * 10,  # Cùng category
                "price_date": dates,
                "price_avg": [7000.0 + i * 10 for i in range(10)],
            }
        )
        p2 = pd.DataFrame(
            {
                "product_id": [102] * 10,
                "category": ["Gạo thơm"] * 10,  # Cùng category nhưng product_id khác
                "price_date": dates,
                "price_avg": [9000.0 + i * 20 for i in range(10)],
            }
        )
        combined = pd.concat([p1, p2], ignore_index=True)
        res = build_enhanced_features(combined)

        p1_res = res[res["product_id"] == 101]
        p2_res = res[res["product_id"] == 102]

        self.assertEqual(len(p1_res), 3)  # 10 - 7 = 3
        self.assertEqual(len(p2_res), 3)  # 10 - 7 = 3
        self.assertTrue((p1_res["lag_1"] < 8000.0).all())
        self.assertTrue((p2_res["lag_1"] > 8500.0).all())

    def test_edge_case_missing_dates_and_weekend_gaps(self):
        """Edge case 14: Dữ liệu không liên tục (cách ngày, nghỉ cuối tuần) vẫn tính đúng shift(7)."""
        dates = [
            pd.Timestamp("2026-06-01"),  # T2
            pd.Timestamp("2026-06-03"),  # T4
            pd.Timestamp("2026-06-08"),  # T2 tuần sau
            pd.Timestamp("2026-06-10"),  # T4
            pd.Timestamp("2026-06-15"),  # T2
            pd.Timestamp("2026-06-17"),  # T4
            pd.Timestamp("2026-06-22"),  # T2
            pd.Timestamp("2026-06-24"),  # T4 (index 7)
            pd.Timestamp("2026-06-29"),  # T2 (index 8)
        ]
        prices = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0]
        df = pd.DataFrame(
            {
                "product_id": [1] * 9,
                "category": ["Gạo ngắt quãng"] * 9,
                "price_date": dates,
                "price_avg": prices,
            }
        )
        res = build_enhanced_features(df)
        self.assertEqual(len(res), 2)  # 9 - 7 = 2
        row_0 = res.iloc[0]
        self.assertEqual(row_0["lag_7"], 100.0)
        self.assertEqual(row_0["lag_1"], 160.0)

    def test_15_validation_target_nan(self):
        """15. Hardening: Kiểm tra từ chối dữ liệu Target (price_avg) chứa giá trị NaN."""
        df_nan = self.sample_df.copy()
        df_nan.loc[5, "price_avg"] = np.nan
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_nan)
        self.assertIn("NaN", str(ctx.exception))

    def test_16_validation_infinite_values(self):
        """16. Hardening: Kiểm tra từ chối dữ liệu Target chứa giá trị vô hạn (inf/-inf)."""
        df_inf = self.sample_df.copy()
        df_inf.loc[3, "price_avg"] = np.inf
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_inf)
        self.assertIn("vô hạn", str(ctx.exception).lower())

        df_neginf = self.sample_df.copy()
        df_neginf.loc[4, "price_avg"] = -np.inf
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_neginf)
        self.assertIn("vô hạn", str(ctx.exception).lower())

    def test_17_validation_test_ratio_invalid(self):
        """17. Hardening: Kiểm tra xác thực test_ratio (phải thỏa 0 < test_ratio < 1)."""
        enh_df = build_enhanced_features(self.sample_df)

        invalid_ratios = [0.0, 1.0, -0.2, 1.5, 2.0]
        for ratio in invalid_ratios:
            with self.subTest(ratio=ratio):
                with self.assertRaises(ValueError) as ctx:
                    train_test_split_chronological(enh_df, test_ratio=ratio)
                self.assertIn("test_ratio", str(ctx.exception))

    def test_18_validation_duplicate_product_date(self):
        """18. Hardening: Kiểm tra phát hiện bản ghi trùng lặp (product_id, price_date)."""
        df_dup = self.sample_df.copy()
        dup_row = df_dup.iloc[[0]].copy()
        df_with_dup = pd.concat([df_dup, dup_row], ignore_index=True)

        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_with_dup)
        self.assertIn("trùng lặp", str(ctx.exception).lower())

    def test_19_validation_missing_group_identifier(self):
        """19. Hardening: Kiểm tra không âm thầm bỏ qua các nhóm có định danh bị thiếu (NaN/None)."""
        df_missing_id = self.sample_df.copy()
        df_missing_id.loc[2, "product_id"] = np.nan

        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_missing_id)
        self.assertIn("product_id", str(ctx.exception))

    def test_20_validation_empty_train_or_test_sets(self):
        """20. Hardening: Ngăn chặn quy trình huấn luyện tiếp tục khi tập Train hoặc Test rỗng."""
        with self.assertRaises(ValueError) as ctx:
            train_test_split_chronological(pd.DataFrame())
        self.assertIn("rỗng", str(ctx.exception).lower())

        valid_df = build_enhanced_features(self.sample_df)
        with self.assertRaises(ValueError) as ctx:
            run_model_comparison(pd.DataFrame(), valid_df)
        self.assertIn("rỗng", str(ctx.exception).lower())

        with self.assertRaises(ValueError) as ctx:
            run_model_comparison(valid_df, pd.DataFrame())
        self.assertIn("rỗng", str(ctx.exception).lower())

    def test_21_multiple_products_on_same_date(self):
        """21. Hardening: Nhiều sản phẩm cùng giao dịch trong cùng 1 ngày không bị xung đột."""
        dates = pd.date_range("2026-06-01", periods=10, freq="D")
        p1 = pd.DataFrame(
            {
                "product_id": [1] * 10,
                "category": ["Lúa IR 504"] * 10,
                "price_date": dates,
                "price_avg": [6000.0 + i * 20 for i in range(10)],
            }
        )
        p2 = pd.DataFrame(
            {
                "product_id": [2] * 10,
                "category": ["Lúa OM 5451"] * 10,
                "price_date": dates,
                "price_avg": [7000.0 + i * 30 for i in range(10)],
            }
        )
        p3 = pd.DataFrame(
            {
                "product_id": [3] * 10,
                "category": ["Lúa Đài Thơm 8"] * 10,
                "price_date": dates,
                "price_avg": [8000.0 + i * 40 for i in range(10)],
            }
        )
        combined = pd.concat([p1, p2, p3], ignore_index=True)
        res = build_enhanced_features(combined)

        self.assertEqual(len(res), 9)  # 3 sản phẩm x 3 dòng = 9
        res_p1 = res[res["product_id"] == 1]
        res_p2 = res[res["product_id"] == 2]
        res_p3 = res[res["product_id"] == 3]

        self.assertAlmostEqual(res_p1.iloc[0]["lag_1"], 6000.0 + 6 * 20)
        self.assertAlmostEqual(res_p2.iloc[0]["lag_1"], 7000.0 + 6 * 30)
        self.assertAlmostEqual(res_p3.iloc[0]["lag_1"], 8000.0 + 6 * 40)

    def test_22_feature_correctness_and_metadata_preservation(self):
        """22. Hardening: Đảm bảo toàn bộ 7 features hợp lệ và bảo toàn metadata (product_id, category, price_date)."""
        res = build_enhanced_features(self.sample_df)

        for meta_col in ["product_id", "category", "price_date", TARGET_COLUMN]:
            self.assertIn(meta_col, res.columns)

        for feat in ENHANCED_FEATURES:
            self.assertIn(feat, res.columns)
            self.assertFalse(np.isinf(res[feat].to_numpy().astype(float)).any())
            self.assertFalse(res[feat].isna().any())

        self.assertTrue(np.issubdtype(res[TARGET_COLUMN].dtype, np.floating))
        self.assertTrue(np.issubdtype(res["lag_1"].dtype, np.floating))
        self.assertTrue(np.issubdtype(res["day_of_week"].dtype, np.integer))

    # ==========================================
    # CÁC TEST CASES FINAL QUALITY HARDENING
    # ==========================================

    def test_23_validation_price_date_nat_or_invalid(self):
        """23. Final Hardening: price_date chứa NaT hoặc chuỗi ngày không hợp lệ."""
        df_nat = self.sample_df.copy()
        df_nat.loc[2, "price_date"] = pd.NaT
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_nat)
        self.assertTrue("NaT" in str(ctx.exception) or "khuyết thiếu" in str(ctx.exception))

        df_invalid = self.sample_df.copy()
        df_invalid["price_date"] = df_invalid["price_date"].astype(str)
        df_invalid.loc[3, "price_date"] = "ngay_khong_hop_le_9999"
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_invalid)
        self.assertIn("không hợp lệ", str(ctx.exception))

    def test_24_validation_price_avg_non_numeric(self):
        """24. Final Hardening: price_avg chứa chuỗi không thể chuyển thành số thực."""
        df_str = self.sample_df.copy()
        df_str["price_avg"] = df_str["price_avg"].astype(object)
        df_str.loc[4, "price_avg"] = "tam_nghin_nam_tram"
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_str)
        self.assertIn("không thể chuyển đổi", str(ctx.exception))

    def test_25_validation_target_nan_and_inf(self):
        """25. Final Hardening: target chứa NaN hoặc Inf khi đã có sẵn cột target."""
        df_target_nan = self.sample_df.copy()
        df_target_nan[TARGET_COLUMN] = df_target_nan["price_avg"].copy()
        df_target_nan.loc[2, TARGET_COLUMN] = np.nan
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_target_nan)
        self.assertIn("target", str(ctx.exception).lower())

        df_target_inf = self.sample_df.copy()
        df_target_inf[TARGET_COLUMN] = df_target_inf["price_avg"].copy()
        df_target_inf.loc[3, TARGET_COLUMN] = np.inf
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_target_inf)
        self.assertIn("vô hạn", str(ctx.exception).lower())

    def test_26_validation_compute_metrics_dimension_mismatch(self):
        """26. Final Hardening: compute_metrics với hai mảng khác kích thước (shape mismatch)."""
        y_true = np.array([100.0, 110.0, 120.0, 130.0])
        y_pred = np.array([100.0, 110.0, 120.0])  # Thiếu 1 phần tử
        with self.assertRaises(ValueError) as ctx:
            compute_metrics(y_true, y_pred)
        self.assertIn("kích thước", str(ctx.exception))

    def test_27_validation_compute_metrics_multidimensional(self):
        """27. Final Hardening: compute_metrics với dữ liệu nhiều chiều (2D array)."""
        y_true_2d = np.array([[100.0, 110.0], [120.0, 130.0]])
        y_pred_2d = np.array([[100.0, 110.0], [120.0, 130.0]])
        with self.assertRaises(ValueError) as ctx:
            compute_metrics(y_true_2d, y_pred_2d)
        self.assertIn("1 chiều", str(ctx.exception))

    def test_28_validation_test_ratio_types(self):
        """28. Final Hardening: test_ratio với các kiểu dữ liệu đặc biệt (None, Boolean, NaN, Inf)."""
        enh_df = build_enhanced_features(self.sample_df)

        special_cases = [None, True, False, np.nan, np.inf, -np.inf, "khong_phai_so"]
        for case in special_cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError) as ctx:
                    train_test_split_chronological(enh_df, test_ratio=case)
                self.assertIn("test_ratio", str(ctx.exception))

    def test_29_validation_category_nan_when_product_id_valid(self):
        """29. Final Hardening: category chứa NaN trong khi product_id vẫn hoàn toàn hợp lệ."""
        df_cat_nan = self.sample_df.copy()
        df_cat_nan.loc[2, "category"] = np.nan
        # product_id = 1 vẫn hợp lệ nhưng category thiếu -> phải từ chối để bảo đảm metadata
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(df_cat_nan)
        self.assertIn("category", str(ctx.exception))

    def test_30_metadata_preserved_across_train_test_split(self):
        """30. Final Hardening: Metadata được bảo toàn nguyên vẹn qua train_test_split."""
        synth_df = generate_synthetic_rice_data(n_days=40)
        enh_df = build_enhanced_features(synth_df)

        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)

        # Kiểm tra đầy đủ các cột metadata trong cả train_df và test_df
        expected_cols = ["product_id", "category", "price_date", "price_min", "price_max", TARGET_COLUMN]
        for col in expected_cols:
            self.assertIn(col, train_df.columns)
            self.assertIn(col, test_df.columns)

        # Kiểm tra tính toàn vẹn: số dòng train + test bằng tổng số dòng ban đầu
        self.assertEqual(len(train_df) + len(test_df), len(enh_df))

    def test_31_validation_duplicate_same_date_different_source(self):
        """31. Final Hardening: Duplicate cùng ngày nhưng khác source (từ chối an toàn, không tự ý drop/aggregate)."""
        df_sources = self.sample_df.copy()
        df_sources["source"] = "vietnambiz"

        # Thêm 1 dòng trùng ngày và product_id nhưng source là 'luagaoviet'
        dup_diff_source = df_sources.iloc[[0]].copy()
        dup_diff_source["source"] = "luagaoviet"
        dup_diff_source["price_avg"] = 105.0

        combined = pd.concat([df_sources, dup_diff_source], ignore_index=True)

        # Quy tắc: Bắt buộc từ chối trùng lặp thời gian trên cùng sản phẩm, không tự ý aggregate/drop
        with self.assertRaises(ValueError) as ctx:
            build_enhanced_features(combined)
        self.assertIn("trùng lặp", str(ctx.exception).lower())

    # ==========================================
    # CÁC TEST CASES FINAL MICRO-HARDENING
    # ==========================================

    def test_32_run_model_comparison_missing_product_id_in_train(self):
        """32. Final Micro-Hardening: Thiếu product_id trong train_df khi gọi run_model_comparison."""
        synth_df = generate_synthetic_rice_data(n_days=30)
        enh_df = build_enhanced_features(synth_df)
        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)

        # Xóa product_id khỏi train_df
        train_no_pid = train_df.drop(columns=["product_id"])
        with self.assertRaises(ValueError) as ctx:
            run_model_comparison(train_no_pid, test_df)
        self.assertIn("train_df", str(ctx.exception))
        self.assertIn("product_id", str(ctx.exception))

    def test_33_run_model_comparison_missing_category_in_test(self):
        """33. Final Micro-Hardening: Thiếu category trong test_df khi gọi run_model_comparison."""
        synth_df = generate_synthetic_rice_data(n_days=30)
        enh_df = build_enhanced_features(synth_df)
        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)

        # Xóa category khỏi test_df
        test_no_cat = test_df.drop(columns=["category"])
        with self.assertRaises(ValueError) as ctx:
            run_model_comparison(train_df, test_no_cat)
        self.assertIn("test_df", str(ctx.exception))
        self.assertIn("category", str(ctx.exception))

    def test_34_run_model_comparison_missing_price_date_in_train(self):
        """34. Final Micro-Hardening: Thiếu price_date trong train_df khi gọi run_model_comparison."""
        synth_df = generate_synthetic_rice_data(n_days=30)
        enh_df = build_enhanced_features(synth_df)
        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)

        # Xóa price_date khỏi train_df
        train_no_date = train_df.drop(columns=["price_date"])
        with self.assertRaises(ValueError) as ctx:
            run_model_comparison(train_no_date, test_df)
        self.assertIn("train_df", str(ctx.exception))
        self.assertIn("price_date", str(ctx.exception))

    def test_35_run_model_comparison_valid_metadata_trains_normally(self):
        """35. Final Micro-Hardening: Dữ liệu hợp lệ có đủ metadata vẫn huấn luyện bình thường."""
        synth_df = generate_synthetic_rice_data(n_days=30)
        enh_df = build_enhanced_features(synth_df)
        train_df, test_df = train_test_split_chronological(enh_df, test_ratio=0.2)

        # Đảm bảo đủ metadata
        self.assertIn("product_id", train_df.columns)
        self.assertIn("category", train_df.columns)
        self.assertIn("price_date", train_df.columns)

        results_df, predictions, rf_model = run_model_comparison(train_df, test_df)

        self.assertIsNotNone(results_df)
        self.assertEqual(len(results_df), 4)
        self.assertIn("Actual", predictions)
        self.assertIsNotNone(rf_model)
        self.assertTrue((results_df["mae"] > 0).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)

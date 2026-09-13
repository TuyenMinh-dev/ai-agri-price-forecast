"""
So sánh hiệu năng giữa các mô hình đã train.
TODO: load kết quả dự đoán từng mô hình, tính RMSE/MAE, in bảng so sánh.
"""

def compare_models(results: dict):
    for name, metrics in results.items():
        print(f"{name}: RMSE={metrics.get('rmse')}, MAE={metrics.get('mae')}")


if __name__ == "__main__":
    print("[TODO] Chạy so sánh mô hình sau khi có kết quả train")

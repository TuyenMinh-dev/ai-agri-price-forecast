import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR / "backend"))

from app.db.session import engine
from app.models.tables import Base


def main():
    print("Đang tạo bảng trong CSDL...")
    Base.metadata.create_all(engine)
    print("Đã tạo xong toàn bộ bảng: products, market_prices, weather_data, "
          "yearly_production, forecasts")


if __name__ == "__main__":
    main()
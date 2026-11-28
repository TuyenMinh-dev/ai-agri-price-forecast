from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    ForeignKey,
    TIMESTAMP,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Product(Base):
    """Danh mục mặt hàng đang theo dõi. Đã có dữ liệu: có."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    crop_type = Column(String(20), nullable=False)
    category = Column(String(100), nullable=False)
    unit = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class MarketPrice(Base):
    """Giá theo ngày - bảng chính, target để model dự đoán. Đã có dữ liệu: có."""
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price_date = Column(Date, nullable=False)
    price_min = Column(Numeric(12, 2))
    price_max = Column(Numeric(12, 2))
    source = Column(String(255))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("product_id", "price_date", "source", name="uq_market_price"),
        Index("idx_market_prices_product_date", "product_id", "price_date"),
    )


class WeatherData(Base):
    """Thời tiết theo vùng/ngày - feature cho model. Đã có dữ liệu: CHƯA."""
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True)
    region = Column(String(100), nullable=False)
    weather_date = Column(Date, nullable=False)
    rainfall_mm = Column(Numeric(8, 2))
    temperature_avg = Column(Numeric(5, 2))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("region", "weather_date", name="uq_weather_region_date"),
        Index("idx_weather_region_date", "region", "weather_date"),
    )


class YearlyProduction(Base):
    """Sản lượng/diện tích theo năm - feature phụ trợ. Đã có dữ liệu: CHƯA."""
    __tablename__ = "yearly_production"

    id = Column(Integer, primary_key=True)
    crop_type = Column(String(20), nullable=False)
    region = Column(String(100), nullable=True)
    year = Column(Integer, nullable=False)
    production_tons = Column(Numeric(14, 2))
    area_hectares = Column(Numeric(14, 2))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("crop_type", "region", "year", name="uq_yearly_production"),
    )


class Forecast(Base):
    """Kết quả dự báo do model AI sinh ra. Đã có dữ liệu: CHƯA."""
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    forecast_date = Column(Date, nullable=False)
    predicted_price = Column(Numeric(12, 2), nullable=False)
    model_name = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_forecasts_product_date", "product_id", "forecast_date"),
    )
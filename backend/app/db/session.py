"""
Cau hinh ket noi CSDL - dung chung cho toan bo backend va cac script khac.
Doc thong tin ket noi tu file .env o goc project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "agri_price_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Ping CSDL trước mỗi query, tự mở lại nếu kết nối chết
    pool_recycle=300,     # Tự làm mới kết nối sau 5 phút để tránh bị cloud timeout
)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Dependency cung cấp DB session cho mỗi request, tự đóng sau khi xong."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
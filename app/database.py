# database.py : 自動生成されたモジュール
# このファイルに対応する処理を記述してください。

import os
from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

# DATABASE_URL は .env から読み込み
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

# ディレクトリがなければ作成
os.makedirs("./data", exist_ok=True)

# SQLite のときだけ connect_args が必要
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# SQLAlchemy 用のエンジンと metadata
engine = create_engine(DATABASE_URL, connect_args=connect_args)
metadata = MetaData()
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# 非同期DBクライアント
database = Database(DATABASE_URL)
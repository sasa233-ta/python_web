from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME, DB_CHARSET

# MySQL接続情報をconfig.pyから取得
DB_URL = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)

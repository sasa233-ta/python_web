from sqlalchemy import Column, String
from app.database import Base

class StockMaster(Base):
    __tablename__ = "stocks"
    code = Column(String, primary_key=True)
    name = Column(String, index=True)
    name_normalized = Column(String, index=True)  # 正規化済み銘柄名
    date = Column(String)
    market = Column(String)
    sector33_code = Column(String)
    sector33 = Column(String)
    sector17_code = Column(String)
    sector17 = Column(String)
    scale_code = Column(String)
    scale = Column(String)

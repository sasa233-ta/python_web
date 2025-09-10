from sqlalchemy import Column, Integer, String, Boolean, Date
from app.models.user_model import Base

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True)
    code = Column(String(12), unique=True, nullable=False, comment="証券コード（.T付き）")
    name = Column(String(128), nullable=False, comment="銘柄名")
    name_normalized = Column(String(128), nullable=True, comment="正規化銘柄名")
    date = Column(String(16), nullable=True, comment="日付（上場日等）")
    market = Column(String(64), nullable=True, comment="市場区分")
    sector33_code = Column(String(8), nullable=True, comment="33業種コード")
    sector33 = Column(String(64), nullable=True, comment="33業種区分")
    sector17_code = Column(String(8), nullable=True, comment="17業種コード")
    sector17 = Column(String(64), nullable=True, comment="17業種区分")
    scale_code = Column(String(8), nullable=True, comment="規模コード")
    scale = Column(String(32), nullable=True, comment="規模区分")
    is_listed = Column(Boolean, default=True, nullable=False, comment="上場中フラグ")

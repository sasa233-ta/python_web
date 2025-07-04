from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.database import Base
from datetime import datetime

class TradeHistory(Base):
    __tablename__ = "trade_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    symbol = Column(String(16), index=True)
    trade_type = Column(String(8))  # 'buy' or 'sell'
    quantity = Column(Integer)
    price = Column(Float)
    realized_pl = Column(Float, nullable=True)  # 売却時のみ
    traded_at = Column(DateTime, default=datetime.utcnow)

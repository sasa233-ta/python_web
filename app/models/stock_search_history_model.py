from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class StockSearchHistory(Base):
    __tablename__ = "stock_search_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(16), nullable=False)
    searched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

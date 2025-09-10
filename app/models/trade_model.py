from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.user_model import Base

class TradeHistory(Base):
    __tablename__ = 'trade_history'
    id = Column(Integer, primary_key=True, comment="トレード履歴ID（主キー）")
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False, comment="ユーザーID（usersテーブルの外部キー）")
    symbol = Column(String(20), index=True, nullable=False, comment="銘柄コード")
    action = Column(String(10), nullable=False, comment="売買区分（buy/sell）")
    shares = Column(Integer, nullable=False, comment="株数")
    price = Column(Float, nullable=False, comment="約定価格")
    traded_at = Column(DateTime, nullable=False, comment="取引日時")

    user = relationship('User', backref='trades')

# インデックス追加（大量データでも検索高速化）
Index('ix_trade_user_symbol', TradeHistory.user_id, TradeHistory.symbol)

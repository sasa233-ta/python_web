# setup_tables.py
from app.database import Base, engine
from app.models.user_model import User
from app.models.login_history_model import LoginHistory
from app.models.stock_search_history_model import StockSearchHistory
from app.models.virtual_account_model import VirtualAccount
from app.models.virtual_trade_history_model import VirtualTradeHistory

print("⏳ テーブル作成中...")
Base.metadata.create_all(bind=engine)
print("✅ テーブル作成完了！")
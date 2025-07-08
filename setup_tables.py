# setup_tables.py
from app.database import Base, engine
from app.models.user_model import User
from app.models.login_history_model import LoginHistory
from app.models.stock_search_history_model import StockSearchHistory
from app.models.holding_model import Holding  # 新たにHoldingをインポート
from app.models.trade_history_model import TradeHistory  # TradeHistoryをインポート
from app.models.stock_master_model import StockMaster  # 公式銘柄マスタも追加

print("⏳ テーブル作成中...")
Base.metadata.create_all(bind=engine)
print("✅ テーブル作成完了！")
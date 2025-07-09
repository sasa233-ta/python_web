from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.endpoints import auth as web_auth_api
from app.endpoints import stock_search as web_stock_search_api
from app.endpoints import recommend as web_recommend_api
from app.endpoints import trade as web_trade_api
from app.api.v1.endpoints import api_analyze as api_analyze_api
from app.utils.fetch_jpx_listed_companies import fetch_and_import_jpx_listed_companies
from app.database import Base, engine
from app.models.user_model import User
from app.models.login_history_model import LoginHistory
from app.models.stock_search_history_model import StockSearchHistory
from app.models.holding_model import Holding
from app.models.trade_history_model import TradeHistory
from app.models.stock_master_model import StockMaster

# サーバー起動時に一度だけ会社一覧を取得
fetch_and_import_jpx_listed_companies()

# サーバー起動時に一度だけテーブル作成（Hobbyプラン用）
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 静的ファイルとルーティング登録
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(web_auth_api.router)
app.include_router(web_stock_search_api.router)
app.include_router(web_recommend_api.router)
app.include_router(web_trade_api.router)
app.include_router(api_analyze_api.router)
# app.include_router(auth_api.router)  # ←API用authは今後JSON専用にする場合のみ残す
# app.include_router(stock_search_api.router)  # ←API用のみ残す場合はコメントアウト
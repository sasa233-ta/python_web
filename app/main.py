from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import auth as auth_api
from app.api.v1.endpoints import stock_search as stock_search_api
from app.api.v1.endpoints import trade as trade_api
from app.api.v1.endpoints import recommend as recommend_api
from app.utils.fetch_jpx_listed_companies import fetch_and_import_jpx_listed_companies

# サーバー起動時に一度だけ会社一覧を取得
fetch_and_import_jpx_listed_companies()

app = FastAPI()

# 静的ファイルとルーティング登録
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_api.router)
app.include_router(stock_search_api.router)
app.include_router(trade_api.router)
app.include_router(recommend_api.router)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.endpoints import auth as auth_api
from app.api.v1.endpoints import stock_search as stock_search_api

app = FastAPI()

# 静的ファイルとルーティング登録
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_api.router, )
app.include_router(stock_search_api.router,)
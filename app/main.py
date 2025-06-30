from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.views import auth_view
from app.controllers import auth_controller

app = FastAPI()

# 静的ファイルとルーティング登録
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_view.router)
app.include_router(auth_controller.router)
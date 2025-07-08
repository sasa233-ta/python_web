from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.recommend_service import get_today_recommend_stocks
import os

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), '../../../templates'))

@router.get("/recommend", summary="今日おすすめの株を取得", tags=["recommend"])
def get_recommend_stocks():
    stocks = get_today_recommend_stocks()
    return JSONResponse(content={"recommend_stocks": stocks})

@router.get("/recommend_page", response_class=HTMLResponse)
def recommend_page(request: Request):
    stocks_by_sector = get_today_recommend_stocks()
    # セクターが1つもなければ空辞書を渡す
    return templates.TemplateResponse("recommend.html", {"request": request, "stocks_by_sector": stocks_by_sector or {}})

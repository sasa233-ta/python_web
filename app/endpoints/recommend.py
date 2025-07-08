from fastapi import APIRouter, Request
from app.services.recommend_service import get_today_recommend_stocks
from app.core.config import templates
import os
import datetime

router = APIRouter()

@router.get("/recommend_page")
def recommend_page(request: Request):
    today = datetime.date.today().strftime('%Y%m%d')
    cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data', f'recommend_{today}_probs.pkl')
    cache_exists = os.path.exists(cache_path)
    stocks_by_sector = get_today_recommend_stocks() if cache_exists else {}
    return templates.TemplateResponse("recommend.html", {"request": request, "stocks_by_sector": stocks_by_sector or {}, "cache_exists": cache_exists})

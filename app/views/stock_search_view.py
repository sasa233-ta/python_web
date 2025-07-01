from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
import yfinance as yf
from app.core.config import templates
from app.database import SessionLocal
from app.models.stock_search_history_model import StockSearchHistory
from app.utils.auth_utils import get_current_user_id
from app.utils.stock_utils import extract_stock_info, normalize_jp_symbol

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stock_search")
def stock_search_page(request: Request, user_id: str = Depends(get_current_user_id)):
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": None})

@router.post("/stock_search")
def stock_search(request: Request, symbol: str = Form(...), user_id: str = Depends(get_current_user_id)):
    db = next(get_db())
    # 1日100回制限
    today = date.today()
    count = db.query(StockSearchHistory).filter(
        StockSearchHistory.user_id == user_id,
        StockSearchHistory.searched_at >= datetime(today.year, today.month, today.day)
    ).count()
    if count >= 100:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": "1日の検索上限（100回）に達しました"})
    # 日本株コード正規化
    try:
        jp_symbol = normalize_jp_symbol(symbol)
    except ValueError as e:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": str(e)})
    # yfinanceで取得
    try:
        stock = yf.Ticker(jp_symbol)
        info = stock.info
        if not info or 'shortName' not in info:
            raise Exception("該当する銘柄が見つかりません")
        result = extract_stock_info(info)
        # 履歴保存
        history = StockSearchHistory(user_id=user_id, symbol=jp_symbol)
        db.add(history)
        db.commit()
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": result, "error": None})
    except Exception as e:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": str(e)})

from fastapi import APIRouter, Request, Form, Depends
from app.services.trade_service import buy_stock_service, sell_stock_service, get_holdings_with_pl_service, get_realized_pl_service
from app.services.auth_service import get_current_user_id
from app.core.config import templates

router = APIRouter()

@router.post("/buy_stock")
def buy_stock(request: Request, symbol: str = Form(...), price: float = Form(...), user_id: str = Depends(get_current_user_id)):
    from app.services.stock_search_service import stock_search_service  # 遅延import
    result = stock_search_service(symbol, user_id)
    buy_result = buy_stock_service(user_id, symbol, price, 100)
    if buy_result["success"]:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": result["data"] if result["success"] else None, "error": None, "js_alert": "購入しました！"})
    else:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": result["data"] if result["success"] else None, "error": None, "js_alert": "購入に失敗しました"})

@router.post("/sell_stock")
def sell_stock(request: Request, symbol: str = Form(...), price: float = Form(...), user_id: str = Depends(get_current_user_id)):
    result = sell_stock_service(user_id, symbol, price, 100)
    holdings = get_holdings_with_pl_service(user_id)
    total_eval = sum([(h["current_price"] or 0) * h["quantity"] for h in holdings]) if holdings else 0
    realized_pl = get_realized_pl_service(user_id)
    return templates.TemplateResponse(
        "holdings.html",
        {
            "request": request,
            "holdings": holdings,
            "total_eval": total_eval,
            "realized_pl": realized_pl,
            "message": result.get("message"),
            "error": result.get("error")
        }
    )

@router.get("/holdings")
def holdings_page(request: Request, user_id: str = Depends(get_current_user_id)):
    holdings = get_holdings_with_pl_service(user_id)
    total_eval = sum([(h["current_price"] or 0) * h["quantity"] for h in holdings]) if holdings else 0
    realized_pl = get_realized_pl_service(user_id)
    return templates.TemplateResponse("holdings.html", {"request": request, "holdings": holdings, "total_eval": total_eval, "realized_pl": realized_pl})

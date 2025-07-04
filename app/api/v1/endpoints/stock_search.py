from fastapi import APIRouter, Request, Form, Depends
from app.services.stock_search_service import stock_search_service, search_stock_service, record_search_history_service
from app.services.auth_service import get_current_user_id
from app.core.config import templates

router = APIRouter()

@router.get("/stock_search")
def stock_search_page(request: Request, user_id: str = Depends(get_current_user_id)):
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": None})

@router.post("/stock_search")
def stock_search(request: Request, symbol: str = Form(...), user_id: str = Depends(get_current_user_id)):
    result = search_stock_service(symbol)
    if result["success"]:
        record_search_history_service(user_id, result["data"]["symbol"])
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": result["data"], "error": None})
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": result["error"]})

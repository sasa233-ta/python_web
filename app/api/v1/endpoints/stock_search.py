from fastapi import APIRouter, Request, Form, Depends
from app.services.stock_search_service import stock_search_service
from app.services.auth_service import get_current_user_id
from app.core.config import templates

router = APIRouter()

@router.get("/stock_search")
def stock_search_page(request: Request, user_id: str = Depends(get_current_user_id)):
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": None})

@router.post("/stock_search")
def stock_search(request: Request, symbol: str = Form(...), user_id: str = Depends(get_current_user_id)):
    result = stock_search_service(symbol, user_id)
    if result["success"]:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": result["data"], "error": None})
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": result["error"]})

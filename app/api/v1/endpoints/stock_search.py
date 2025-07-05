from fastapi import APIRouter, Request, Form, Depends
from app.services.jp_stock_search_service import search_stocks_by_keyword_db
from app.services.stock_search_service import search_stock_service, record_search_history_service
from app.services.auth_service import get_current_user_id
from app.core.config import templates

router = APIRouter()

@router.get("/stock_search")
def stock_search_page(request: Request, user_id: str = Depends(get_current_user_id)):
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": None, "candidates": None})

@router.post("/stock_search")
def stock_search(request: Request, keyword: str = Form(...), user_id: str = Depends(get_current_user_id)):
    candidates = search_stocks_by_keyword_db(keyword)
    if not candidates:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": "該当する銘柄がありません", "candidates": None})
    if len(candidates) == 1:
        # 1件だけなら即詳細へ
        code = candidates[0]["code"]
        result = search_stock_service(code)
        if result["success"]:
            record_search_history_service(user_id, code)
            return templates.TemplateResponse("stock_search.html", {"request": request, "result": result["data"], "error": None, "candidates": None})
        else:
            return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": result["error"], "candidates": None})
    # 複数候補なら一覧表示
    return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": None, "candidates": candidates})

# --- GETで銘柄詳細 ---
@router.get("/stock_detail/{code}")
def stock_detail(request: Request, code: str, user_id: str = Depends(get_current_user_id)):
    result = search_stock_service(code)
    if result["success"]:
        record_search_history_service(user_id, code)
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": result["data"], "error": None, "candidates": None})
    else:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": result["error"], "candidates": None})

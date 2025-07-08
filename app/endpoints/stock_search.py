import logging
logging.basicConfig(level=logging.INFO)

from fastapi import APIRouter, Request, Form, Depends
from app.services.jp_stock_search_service import search_stocks_by_keyword_db
from app.services.stock_search_service import search_stock_service, record_search_history_service, get_chart_data
from app.services.auth_service import get_current_user_id
from app.core.config import templates
from app.utils import stock_analyzer
import asyncio
import json

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

# --- 分析エンドポイント（async対応） ---
@router.post("/analyze_stock")
async def analyze_stock(request: Request, symbol: str = Form(None), keyword: str = Form(None), user_id: str = Depends(get_current_user_id)):
    logging.info("[分析API] 分析リクエスト受信")
    code = symbol
    candidates = None
    if not code and keyword:
        candidates = search_stocks_by_keyword_db(keyword)
        if not candidates:
            return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": "該当する銘柄がありません", "candidates": None, "analysis": None, "chart_labels": None, "chart_data": None})
        if len(candidates) == 1:
            code = candidates[0]["code"]
        else:
            return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": None, "candidates": candidates, "analysis": None, "chart_labels": None, "chart_data": None})
    if not code:
        return templates.TemplateResponse("stock_search.html", {"request": request, "result": None, "error": "銘柄コードまたは検索語を入力してください", "candidates": None, "analysis": None, "chart_labels": None, "chart_data": None})
    
    result = search_stock_service(code)
    analysis = None
    chart_labels = None
    chart_data = None
    
    if result["success"]:
        try:
            logging.info(f"[分析API] LSTM学習・推論開始: {code}")
            # .Tを付与（日本株用）
            if not code.endswith('.T'):
                code = f"{code}.T"
            # LSTMモデルで学習・予測
            prob = stock_analyzer.predict_probability(code)
            analysis = type('Analysis', (), {"prob_lstm": prob})()
            status = "成功" if prob is not None else "データ不足"
            logging.info(f"[分析API] 分析完了({status}): {code}")
            # チャートデータ取得
            chart = get_chart_data(code)
            if chart and chart.get("labels") and chart.get("data"):
                chart_labels = json.dumps(chart["labels"], ensure_ascii=False)
                chart_data = json.dumps(chart["data"], ensure_ascii=False)
        except Exception as e:
            logging.error(f"[分析API] エラー発生: {e}")
            analysis = type('Analysis', (), {"prob_lstm": None})()
            chart_labels = None
            chart_data = None

    return templates.TemplateResponse(
        "stock_search.html",
        {"request": request, "result": result["data"] if result["success"] else None, "error": None, "candidates": None, "analysis": analysis, "chart_labels": chart_labels, "chart_data": chart_data}
    )

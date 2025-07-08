from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from app.services.stock_search_service import get_chart_data
from app.utils import stock_analyzer

router = APIRouter()

@router.post("/api/analyze_stock")
def api_analyze_stock(symbol: str = Form(...)):
    code = symbol
    if not code:
        return JSONResponse({"success": False, "error": "銘柄コードが必要です"}, status_code=400)
    if not code.endswith('.T'):
        code = f"{code}.T"
    try:
        prob = stock_analyzer.predict_probability(code)
        return JSONResponse({"success": True, "prob_lstm": prob})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@router.get("/api/chart_data")
def api_chart_data(symbol: str):
    code = symbol
    if not code:
        return JSONResponse({"success": False, "error": "銘柄コードが必要です"}, status_code=400)
    if not code.endswith('.T'):
        code = f"{code}.T"
    try:
        chart = get_chart_data(code)
        if chart and chart.get("labels") and chart.get("data"):
            return JSONResponse({"success": True, "labels": chart["labels"], "data": chart["data"]})
        else:
            return JSONResponse({"success": False, "error": "データが取得できませんでした"})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

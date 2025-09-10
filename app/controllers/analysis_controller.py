from app.services.jquants_service import fetch_stock_data_from_jquants
from app.services.analysis_service import analyze_stock

# 株価データ取得＋分析をまとめて呼び出すコントローラー層

def get_stock_analysis(code):
    stock_data = fetch_stock_data_from_jquants(code)
    analysis = analyze_stock(stock_data["prices"])
    return {
        "code": code,
        "prices": stock_data["prices"],
        "dates": stock_data["dates"],
        "mean": analysis["mean"],
        "std": analysis["std"],
        "prediction": analysis["prediction"],
        "prob_up_3days": analysis["prob_up_3days"]
    }

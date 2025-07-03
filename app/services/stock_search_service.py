from datetime import datetime, date
import re
import yfinance as yf
from app.database import SessionLocal
from app.models.stock_search_history_model import StockSearchHistory

def extract_stock_info(info):
    summary = info.get("longBusinessSummary")
    if summary and "。" in summary:
        summary = summary.split("。", 1)[0] + "。"
    employees = info.get("fullTimeEmployees")
    if employees is not None:
        employees = f"{employees:,}"
    return {
        "銘柄名": info.get("longName") or info.get("shortName"),
        "市場": info.get("exchange"),
        "symbol": info.get("symbol"),
        "現在値": info.get("regularMarketPrice"),
        "前日終値": info.get("regularMarketPreviousClose"),
        "始値": info.get("regularMarketOpen"),
        "高値": info.get("regularMarketDayHigh"),
        "安値": info.get("regularMarketDayLow"),
        "出来高": info.get("regularMarketVolume"),
        "時価総額": info.get("marketCap"),
        "PER": info.get("trailingPE"),
        "PBR": info.get("priceToBook"),
        "配当利回り": info.get("dividendYield"),
        "52週高値": info.get("fiftyTwoWeekHigh"),
        "52週安値": info.get("fiftyTwoWeekLow"),
        "業種": info.get("industry"),
        "本社所在地": info.get("city"),
        "従業員数": employees,
        "企業概要": summary,
    }

def normalize_jp_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if re.fullmatch(r"\d{4}", symbol):
        return symbol + ".T"
    if symbol.endswith(".T"):
        return symbol
    raise ValueError("日本株は4桁コードまたは4桁+.Tで入力してください")

def stock_search_service(symbol: str, user_id: str):
    db = SessionLocal()
    try:
        today = date.today()
        count = db.query(StockSearchHistory).filter(
            StockSearchHistory.user_id == user_id,
            StockSearchHistory.searched_at >= datetime(today.year, today.month, today.day)
        ).count()
        if count >= 100:
            return {"success": False, "error": "1日の検索上限（100回）に達しました"}
        try:
            jp_symbol = normalize_jp_symbol(symbol)
        except ValueError as e:
            return {"success": False, "error": str(e)}
        try:
            stock = yf.Ticker(jp_symbol)
            info = stock.info
            if not info or 'shortName' not in info:
                return {"success": False, "error": "該当する銘柄が見つかりません"}
            result = extract_stock_info(info)
            history = StockSearchHistory(user_id=user_id, symbol=jp_symbol)
            db.add(history)
            db.commit()
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    finally:
        db.close()

from datetime import datetime, date
import re
import yfinance as yf
from app.database import SessionLocal
from app.models.stock_search_history_model import StockSearchHistory
from app.models.holding_model import Holding

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

def buy_stock_service(user_id: str, symbol: str, price: float, quantity: int = 100):
    db = SessionLocal()
    try:
        holding = db.query(Holding).filter_by(user_id=user_id, symbol=symbol).first()
        if holding:
            # 平均取得単価を加重平均で更新
            total_quantity = holding.quantity + quantity
            holding.avg_price = (
                (holding.avg_price * holding.quantity + price * quantity) / total_quantity
            )
            holding.quantity = total_quantity
            holding.updated_at = datetime.utcnow()
        else:
            holding = Holding(user_id=user_id, symbol=symbol, quantity=quantity, avg_price=price)
            db.add(holding)
        db.commit()
        return {"success": True, "message": f"{symbol} を{quantity}株購入しました"}
    finally:
        db.close()

def sell_stock_service(user_id: str, symbol: str, price: float, quantity: int = 100):
    db = SessionLocal()
    try:
        holding = db.query(Holding).filter_by(user_id=user_id, symbol=symbol).first()
        if not holding or holding.quantity < quantity:
            return {"success": False, "error": "保有株数が足りません"}
        holding.quantity -= quantity
        holding.updated_at = datetime.utcnow()
        if holding.quantity == 0:
            db.delete(holding)
        db.commit()
        return {"success": True, "message": f"{symbol} を{quantity}株売却しました"}
    finally:
        db.close()

def get_holdings_service(user_id: str):
    db = SessionLocal()
    try:
        holdings = db.query(Holding).filter_by(user_id=user_id).all()
        return holdings
    finally:
        db.close()

def get_holdings_with_pl_service(user_id: str):
    db = SessionLocal()
    try:
        holdings = db.query(Holding).filter_by(user_id=user_id).all()
        result = []
        symbols = [h.symbol for h in holdings]
        prices = {}
        names = {}
        if symbols:
            try:
                tickers = yf.Tickers(" ".join(symbols))
                for symbol in symbols:
                    info = tickers.tickers[symbol].info
                    prices[symbol] = info.get("regularMarketPrice")
                    names[symbol] = info.get("longName") or info.get("shortName")
            except Exception:
                prices = {symbol: None for symbol in symbols}
                names = {symbol: None for symbol in symbols}
        for h in holdings:
            current_price = prices.get(h.symbol)
            name = names.get(h.symbol)
            pl = None
            if current_price and h.avg_price:
                pl = (current_price - h.avg_price) * h.quantity
            result.append({
                "symbol": h.symbol,
                "name": name,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "purchased_at": h.purchased_at,
                "current_price": current_price,
                "pl": pl
            })
        return result
    finally:
        db.close()

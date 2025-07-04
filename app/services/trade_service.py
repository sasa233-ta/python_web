from datetime import datetime
from app.database import SessionLocal
from app.models.holding_model import Holding
from app.models.trade_history_model import TradeHistory
import yfinance as yf

def buy_stock_service(user_id: str, symbol: str, price: float, quantity: int = 100):
    db = SessionLocal()
    try:
        holding = db.query(Holding).filter_by(user_id=user_id, symbol=symbol).first()
        if holding:
            total_quantity = holding.quantity + quantity
            holding.avg_price = (
                (holding.avg_price * holding.quantity + price * quantity) / total_quantity
            )
            holding.quantity = total_quantity
            holding.updated_at = datetime.utcnow()
        else:
            holding = Holding(user_id=user_id, symbol=symbol, quantity=quantity, avg_price=price)
            db.add(holding)
        # 買い履歴を記録
        trade = TradeHistory(user_id=user_id, symbol=symbol, trade_type='buy', quantity=quantity, price=price)
        db.add(trade)
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
        # 実現損益計算（平均取得単価との差額×売却株数）
        realized_pl = (price - holding.avg_price) * quantity if holding.avg_price else 0
        holding.quantity -= quantity
        holding.updated_at = datetime.utcnow()
        if holding.quantity == 0:
            db.delete(holding)
        # 売り履歴を記録
        trade = TradeHistory(user_id=user_id, symbol=symbol, trade_type='sell', quantity=quantity, price=price, realized_pl=realized_pl)
        db.add(trade)
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

def get_realized_pl_service(user_id: str):
    db = SessionLocal()
    try:
        trades = db.query(TradeHistory).filter_by(user_id=user_id, trade_type='sell').all()
        total = sum([t.realized_pl or 0 for t in trades])
        return total
    finally:
        db.close()

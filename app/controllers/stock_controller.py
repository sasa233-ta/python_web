from app.core.db import Session
from app.models.stock_model import Stock

def get_stocks(keyword=None, page=1, per_page=25):
    """
    銘柄一覧をページングで取得する。キーワードがあれば部分一致検索。
    page: 1始まり
    per_page: 1ページあたりの件数
    """
    session = Session()
    query = session.query(Stock)
    if keyword:
        query = query.filter(Stock.name.like(f"%{keyword}%") | Stock.code.like(f"%{keyword}%"))
    total = query.count()
    stocks = query.offset((page-1)*per_page).limit(per_page).all()
    session.close()
    return stocks, total

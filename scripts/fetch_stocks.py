import os
import unicodedata
import pandas as pd
import requests
from datetime import datetime
from app.core.db import Session
from app.models.stock_model import Stock
from app.models.user_model import Base
from app.core.db import engine

def fetch_and_update_stocks():
    """
    JPXの上場会社一覧Excelを1日1回ダウンロードし、DBに全件再投入する
    """
    JPX_XLS_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data'))
    XLS_PATH = os.path.join(DATA_DIR, 'jpx_listed_companies.xls')
    TIMESTAMP_PATH = XLS_PATH + '.timestamp'
    today = datetime.now().strftime('%Y-%m-%d')
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1日1回のみダウンロード
    if os.path.exists(XLS_PATH) and os.path.exists(TIMESTAMP_PATH) and open(TIMESTAMP_PATH, encoding='utf-8').read().strip() == today:
        print("本日分のXLSは既に最新です（DBは再投入します）")
    else:
        # ダウンロード
        r = requests.get(JPX_XLS_URL)
        r.raise_for_status()
        with open(XLS_PATH, 'wb') as f:
            f.write(r.content)
        with open(TIMESTAMP_PATH, 'w', encoding='utf-8') as f:
            f.write(today)

    # DB初期化・テーブル作成（必要に応じて）
    Base.metadata.create_all(bind=engine)

    # Excel→DB投入
    df = pd.read_excel(XLS_PATH, dtype=str)
    colmap = {
        "date": "日付",
        "code": "コード",
        "name": "銘柄名",
        "market": "市場・商品区分",
        "sector33_code": "33業種コード",
        "sector33": "33業種区分",
        "sector17_code": "17業種コード",
        "sector17": "17業種区分",
        "scale_code": "規模コード",
        "scale": "規模区分"
    }
    stocks = []
    for _, row in df.iterrows():
        code = row.get(colmap["code"])
        if code and code.isdigit() and len(code) == 4:
            code = code + ".T"
        name = row.get(colmap["name"])
        name_normalized = unicodedata.normalize("NFKC", name) if name else None
        stocks.append(Stock(
            code=code,
            name=name,
            name_normalized=name_normalized,
            date=row.get(colmap["date"]),
            market=row.get(colmap["market"]),
            sector33_code=row.get(colmap["sector33_code"]),
            sector33=row.get(colmap["sector33"]),
            sector17_code=row.get(colmap["sector17_code"]),
            sector17=row.get(colmap["sector17"]),
            scale_code=row.get(colmap["scale_code"]),
            scale=row.get(colmap["scale"]),
            is_listed=True
        ))
    session = Session()
    try:
        session.query(Stock).delete()  # 全件削除してから再投入
        session.bulk_save_objects(stocks)
        session.commit()
        print(f"DBに{len(stocks)}件インポートしました")
    finally:
        session.close()

if __name__ == "__main__":
    fetch_and_update_stocks()

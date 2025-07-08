import os
from typing import List, Dict
from app.models.stock_master_model import StockMaster
from app.database import SessionLocal
import unicodedata

# rapidfuzzで部分一致・あいまい検索
try:
    from rapidfuzz import process
except ImportError:
    process = None

def search_stocks_by_keyword_db(keyword: str, limit: int = 20):
    db = SessionLocal()
    # キーワードをNFKC正規化
    keyword_norm = unicodedata.normalize("NFKC", keyword)
    # 正規化カラムで部分一致（LIKE）
    stocks = db.query(StockMaster).filter(StockMaster.name_normalized.contains(keyword_norm)).limit(limit).all()
    result = [{
        "code": s.code,
        "name": s.name,
        "market": s.market,
        "sector33": s.sector33,
        "sector17": s.sector17,
        "scale": s.scale
    } for s in stocks]
    # rapidfuzzであいまい検索（部分一致が少ない場合のみ）
    if process and len(result) < 10:
        all_names = [s.name_normalized for s in db.query(StockMaster).all()]
        matches = process.extract(keyword_norm, all_names, limit=10, score_cutoff=60)
        for name_norm, score, idx in matches:
            s = db.query(StockMaster).filter_by(name_normalized=name_norm).first()
            if s:
                candidate = {
                    "code": s.code,
                    "name": s.name,
                    "market": s.market,
                    "sector33": s.sector33,
                    "sector17": s.sector17,
                    "scale": s.scale
                }
                if candidate not in result:
                    result.append(candidate)
    db.close()
    return result

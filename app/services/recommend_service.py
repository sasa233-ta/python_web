import os
import pickle
import datetime
import random
import re
from app.models.stock_master_model import StockMaster
from app.database import SessionLocal
from app.utils.stock_analyzer import predict_probability

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'data')


def normalize_jp_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if symbol.endswith('.T'):
        return symbol
    if re.fullmatch(r'\d{4}', symbol):
        return symbol + '.T'
    raise ValueError('日本株は4桁コードまたは4桁+.Tで入力してください')


def get_today_recommend_stocks(n=10, _called_from_cache=False):
    today = datetime.date.today().strftime('%Y%m%d')
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y%m%d')
    cache_path = os.path.join(CACHE_DIR, f'recommend_{today}_probs.pkl')
    # 昨日分のキャッシュファイルがあれば削除
    yesterday_cache_path = os.path.join(CACHE_DIR, f'recommend_{yesterday}_probs.pkl')
    if os.path.exists(yesterday_cache_path):
        try:
            os.remove(yesterday_cache_path)
        except Exception:
            pass
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            result = pickle.load(f)
            # 総合ランキングもキャッシュに含める
            if 'all' not in result:
                all_stocks = []
                for stocks in result.values():
                    all_stocks.extend(stocks)
                all_stocks.sort(key=lambda x: (x['probability'] is not None, x['probability']), reverse=True)
                result['all'] = all_stocks
            return result
    elif not _called_from_cache:
        generate_recommend_cache(n)
        # 再帰呼び出しでキャッシュを読む（無限ループ防止のためフラグを渡す）
        return get_today_recommend_stocks(n, _called_from_cache=True)
    session = SessionLocal()
    try:
        sector17_list = session.query(StockMaster.sector17_code).distinct().filter(StockMaster.sector17_code != '-').all()
        result = {}
        all_stocks = []
        for (sector17_code,) in sector17_list:
            stocks = session.query(StockMaster).filter(StockMaster.sector17_code == sector17_code).all()
            if not stocks:
                continue
            sample = random.sample(stocks, min(n, len(stocks)))
            stock_dicts = []
            for s in sample:
                try:
                    prob = predict_probability(s.code)
                except Exception:
                    prob = None
                stock_dicts.append({
                    'code': s.code,
                    'name': s.name,
                    'sector33': s.sector33,
                    'sector17': s.sector17_code,
                    'sector17_name': s.sector17,
                    'market': s.market,
                    'probability': prob
                })
            stock_dicts.sort(key=lambda x: (x['probability'] is not None, x['probability']), reverse=True)
            result[sector17_code] = stock_dicts
            all_stocks.extend(stock_dicts)
        all_stocks.sort(key=lambda x: (x['probability'] is not None, x['probability']), reverse=True)
        result['all'] = all_stocks
        with open(cache_path, 'wb') as f:
            pickle.dump(result, f)
        return result
    finally:
        session.close()


def generate_recommend_cache(n=10):
    """
    管理画面等から呼び出し用：本日分のおすすめ株キャッシュ（pickleファイル）を再生成
    """
    get_today_recommend_stocks(n=n, _called_from_cache=True)

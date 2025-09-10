import requests
import os
import pandas as pd
from datetime import datetime, timedelta
import re

# J-Quants APIから株価データを取得するサービス層
# 無料ライセンスは2年分のデータ取得可能

def get_jquants_id_token():
    """
    J-QuantsのリフレッシュトークンからidTokenを取得
    """
    API_URL = os.getenv('JQUANTS_API_URL', 'https://api.jquants.com')
    refreshtoken = os.getenv('JQUANTS_REFRESH_TOKEN')
    print(f"[J-Quants] .env取得: API_URL={API_URL}, REFRESH_TOKEN頭={refreshtoken[:10] if refreshtoken else None}")
    if not refreshtoken:
        print('[J-Quants] 環境変数JQUANTS_REFRESH_TOKENが未設定です')
        return None
    res = requests.post(f"{API_URL}/v1/token/auth_refresh?refreshtoken={refreshtoken}")
    if res.status_code == 200:
        id_token = res.json().get('idToken')
        print('[J-Quants] idTokenの取得に成功')
        return id_token
    else:
        print(f"[J-Quants] idToken取得失敗: {res.text}")
        return None

def fetch_stock_data_from_jquants(code):
    """
    指定した証券コードの株価データをJ-Quants APIから取得（過去2年分、12週間遅延）
    取得データをCSV出力（app/data/stock_{code}.csv）
    """
    BASE_URL = 'https://api.jquants.com/v1/prices/daily_quotes'
    id_token = get_jquants_id_token()
    if not id_token:
        return {"code": code, "prices": [], "dates": []}

    # コードが「1605.T」などの場合は数字部分のみ抽出
    code_api = re.match(r'^(\d{4,5})', str(code))
    if code_api:
        code_api = code_api.group(1)
    else:
        code_api = str(code)
    if not code_api.isdigit() or not (4 <= len(code_api) <= 5):
        print(f"[J-Quants] コード形式不正: {code}")
        return {"code": code, "prices": [], "dates": []}

    today = datetime.now().date()
    end_date = today - timedelta(weeks=12)  # 12週間遅延
    start_date = end_date - timedelta(days=364*2)  # 2年前
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    headers = {'Authorization': f'Bearer {id_token}'}
    params = {
        'code': code_api,
        'from': start_date_str,
        'to': end_date_str
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        print(f"[J-Quants] API error: {response.status_code} {response.text}")
        return {"code": code, "prices": [], "dates": []}
    data = response.json()
    records = data.get('daily_quotes', [])
    # 日付昇順で全データ取得
    records = sorted(records, key=lambda x: x['Date'])
    # 'Close'がNoneや空文字の場合はスキップ
    prices = []
    dates = []
    csv_rows = []
    for r in records:
        close = r.get('Close')
        if close is not None and close != '':
            try:
                price = float(close)
                prices.append(price)
                dates.append(r['Date'])
                csv_rows.append({"Date": r['Date'], "Close": price})
            except Exception as e:
                print(f"[J-Quants] float変換エラー: {close} ({e})")
    # CSV出力
    if csv_rows:
        df = pd.DataFrame(csv_rows)
        os.makedirs('app/data', exist_ok=True)
        csv_path = f'app/data/stock_{code}.csv'
        df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"[J-Quants] CSV出力: {csv_path} ({len(df)}件)")
    # デバッグ出力
    if prices:
        print(f"[J-Quants] {code}: {len(prices)}件取得, {dates[0]}({prices[0]}) ～ {dates[-1]}({prices[-1]})")
    else:
        print(f"[J-Quants] {code}: データなし")
    return {
        "code": code,
        "prices": prices,
        "dates": dates
    }

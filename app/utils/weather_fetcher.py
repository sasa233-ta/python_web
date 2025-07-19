import os
import pickle
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_tokyo_weather(start_date, end_date, pickle_path):
    """
    Open-Meteo APIで東京の日別天気データを取得し、pickleで保存・追記する
    :param start_date: 'YYYY-MM-DD' 文字列
    :param end_date: 'YYYY-MM-DD' 文字列
    :param pickle_path: pickleファイルパス
    :return: DataFrame（date, tmax, tmin, precipitation, weathercode, ...）
    """
    # 既存データ読み込み
    if os.path.exists(pickle_path):
        with open(pickle_path, 'rb') as f:
            weather_df = pickle.load(f)
        if not isinstance(weather_df, pd.DataFrame):
            weather_df = pd.DataFrame(weather_df)
    else:
        weather_df = pd.DataFrame()

    # 既存データの日付セット
    existing_dates = set(weather_df['date']) if not weather_df.empty else set()

    # 取得対象日リスト
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    all_dates = [(start_dt + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((end_dt-start_dt).days+1)]
    fetch_dates = [d for d in all_dates if d not in existing_dates]
    if not fetch_dates:
        return weather_df

    # Open-Meteo API: 東京(緯度35.68, 経度139.76)
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        'latitude': 35.68,
        'longitude': 139.76,
        'start_date': fetch_dates[0],
        'end_date': fetch_dates[-1],
        'daily': ['temperature_2m_max','temperature_2m_min','precipitation_sum','weathercode'],
        'timezone': 'Asia/Tokyo'
    }
    r = requests.get(url, params=params)
    r.raise_for_status()
    data = r.json()['daily']
    df_new = pd.DataFrame(data)
    df_new['date'] = pd.to_datetime(df_new['time']).dt.strftime('%Y-%m-%d')
    df_new = df_new.drop('time', axis=1)

    # 既存データとマージ
    if not weather_df.empty:
        weather_df = pd.concat([weather_df, df_new], ignore_index=True)
        weather_df = weather_df.drop_duplicates('date').sort_values('date').reset_index(drop=True)
    else:
        weather_df = df_new

    # 保存
    with open(pickle_path, 'wb') as f:
        pickle.dump(weather_df, f)
    return weather_df

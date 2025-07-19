import pandas as pd
import time
import os
import logging

# ロガー設定
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def load_past_chart_data(
    file_path=os.path.join(os.path.dirname(__file__), '../../data/rss_stock_data.xlsx'),
    sheet_name='past_chart',
    period_days=900,
    ticker=None
):
    """
    MarketSpeed II RSSの履歴シート（past_chart）から株価データを読み込む関数。
    :param file_path: Excelファイルのパス
    :param sheet_name: シート名
    :param period_days: 取得する日数（デフォルト3年分=756営業日）
    :param ticker: 取得したい銘柄コード（targetシートのticker列を書き換える）
    :return: DataFrame（日付・始値・高値・安値・終値・出来高・ラベル）
    """
    logger.info(f"読み込みファイル: {file_path}, シート: {sheet_name}, 取得日数: {period_days}, ticker: {ticker}")
    if ticker is not None:
        # Excelを起動してtickerセルを書き換え
        logger.info(f"Excelを起動してtargetシートのticker列を {ticker} に書き換えます")
        try:
            import win32com.client
            excel = win32com.client.Dispatch("Excel.Application")
            # 既存のExcelインスタンスからファイル名で取得
            file_name = os.path.basename(os.path.abspath(file_path))
            wb = None
            for book in excel.Workbooks:
                if book.Name == file_name:
                    wb = book
                    break
            if wb is None:
                logger.error(f"Excelで {file_name} が開かれていません。手動で開いてください。処理を中断します。")
                return None
            ws = wb.Worksheets('target')
            # tickerセルの位置を自動検出（1行目の'ticker'列）
            header = [ws.Cells(1, col).Value for col in range(1, ws.UsedRange.Columns.Count+1)]
            if 'ticker' not in header:
                raise ValueError('targetシートにticker列がありません')
            ticker_col = header.index('ticker') + 1
            # 2行目のtickerセルを書き換え（必要に応じて行番号調整）
            ws.Cells(2, ticker_col).Value = ticker
            wb.Save()
            logger.info("Excelでticker列を書き換え、保存しました。ファイルを再度開きます（閉じません）。MarketSpeed II等でデータ取得を確認します。")
            # データが空ならリトライ（最大2回まで）
            df_check = pd.read_excel(file_path, sheet_name=sheet_name)
            df_check.columns = [c.strip().replace('\u3000', '') for c in df_check.columns]
            if '日付' in df_check.columns:
                max_date = df_check['日付'].max()
            elif 'Date' in df_check.columns:
                max_date = df_check['Date'].max()
            else:
                max_date = None
            row_count = len(df_check)
            if row_count == 0 or max_date is None or str(max_date) == 'nan':
                logger.info("Excelデータが空です。リトライします。")
                if not hasattr(load_past_chart_data, '_retry_count'):
                    load_past_chart_data._retry_count = 0
                load_past_chart_data._retry_count += 1
                if load_past_chart_data._retry_count <= 2:
                    time.sleep(2)
                    return load_past_chart_data(file_path=file_path, sheet_name=sheet_name, period_days=period_days, ticker=ticker)
                else:
                    load_past_chart_data._retry_count = 0
        except Exception as e:
            logger.error(f"Excel操作でエラー: {e}")
            raise
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    logger.info(f"データ取得: {len(df)}件")
    logger.info(f"取得カラム: {list(df.columns)}")
    # カラム名の前後空白・全角スペース除去
    df.columns = [c.strip().replace('\u3000', '') for c in df.columns]
    df = df.rename(columns={
        '日付': 'Date',
        '始値': 'Open',
        '高値': 'High',
        '安値': 'Low',
        '終値': 'Close',
        '出来高': 'Volume'
    })
    logger.info(f"正規化後カラム: {list(df.columns)}")
    # 不要な列を除去
    for col in ['銘柄名称', '市場名称', '足種']:
        if col in df.columns:
            df = df.drop(col, axis=1)
    # 数値カラムを明示的にfloat型へ変換
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.sort_values('Date')
    df = df.tail(period_days)
    logger.info(f"並び替え・期間絞り込み後: {len(df)}件")
    df['Return+3'] = df['Close'].shift(-3) > df['Close']
    df['Label'] = df['Return+3'].astype(int)
    # 欠損除去前に各カラムのNaN件数をログ出力
    logger.info(f"欠損除去前 NaN件数: {df.isnull().sum().to_dict()}")
    # 主要カラムのみ欠損除去
    df = df.dropna(subset=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
    logger.info(f"欠損除去後: {len(df)}件")
    if len(df) == 0:
        logger.error("欠損除去後にデータが0件です。Excelデータの空欄や不正値を確認してください。")
        raise ValueError("No data left after dropna. Check Excel for empty or invalid rows.")
    return df

# --- ここから分析用関数群 ---
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, KFold
import lightgbm as lgb
import numpy as np

def create_features_from_excel(df):
    # --- 天気データ結合 ---
    import os
    from app.utils.weather_fetcher import fetch_tokyo_weather
    weather_pickle = os.path.join(os.path.dirname(__file__), '../../data/tokyo_weather.pkl')
    # 日付範囲を決定
    if 'Date' in df.columns:
        date_min = pd.to_datetime(df['Date']).min().strftime('%Y-%m-%d')
        date_max = pd.to_datetime(df['Date']).max().strftime('%Y-%m-%d')
        weather_df = fetch_tokyo_weather(date_min, date_max, weather_pickle)
        if not weather_df.empty:
            df = df.merge(weather_df, left_on=pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d'), right_on='date', how='left')
            # 主要天気特徴量をfloat型で追加
            for col in ['temperature_2m_max','temperature_2m_min','precipitation_sum','weathercode']:
                if col in df:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
    else:
        # Date列がなければ天気特徴量はNaN
        for col in ['temperature_2m_max','temperature_2m_min','precipitation_sum','weathercode']:
            df[col] = np.nan

    logger.info(f"特徴量作成開始: 入力データ {df.shape}")
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA15'] = df['Close'].rolling(15).mean()
    df['Diff'] = df['MA5'] - df['MA10']
    # 価格変動率（前日比）
    df['PriceChangeRate'] = df['Close'].pct_change()
    # ボリンジャーバンド（20日）
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Std'] = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + 2 * df['BB_Std']
    df['BB_Lower'] = df['BB_Mid'] - 2 * df['BB_Std']
    # MACD（12, 26, 9）
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    # 出来高変化率
    df['VolumeChangeRate'] = df['Volume'].pct_change()
    # 既存
    df['Return1'] = df['Close'].pct_change()
    df['Volatility'] = df['Close'].rolling(10).std()
    # RSI
    delta = df['Close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.rolling(14).mean()
    roll_down = down.rolling(14).mean()
    rs = roll_up / (roll_down + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # 曜日・月特徴量追加
    if 'Date' in df.columns:
        df['weekday'] = pd.to_datetime(df['Date']).dt.weekday  # 0=月, ..., 6=日
        df['month'] = pd.to_datetime(df['Date']).dt.month      # 1-12
    else:
        df['weekday'] = np.nan
        df['month'] = np.nan

    # ATR（Average True Range, 14日）
    df['TR1'] = df['High'] - df['Low']
    df['TR2'] = (df['High'] - df['Close'].shift(1)).abs()
    df['TR3'] = (df['Low'] - df['Close'].shift(1)).abs()
    df['TrueRange'] = df[['TR1', 'TR2', 'TR3']].max(axis=1)
    df['ATR'] = df['TrueRange'].rolling(14).mean()

    # ADX（Average Directional Index, 14日）
    df['UpMove'] = df['High'].diff()
    df['DownMove'] = -df['Low'].diff()
    df['PlusDM'] = df['UpMove'].where((df['UpMove'] > df['DownMove']) & (df['UpMove'] > 0), 0.0)
    df['MinusDM'] = df['DownMove'].where((df['DownMove'] > df['UpMove']) & (df['DownMove'] > 0), 0.0)
    df['TR_ADX'] = df['TrueRange'].rolling(14).sum()
    df['PlusDI'] = 100 * df['PlusDM'].rolling(14).sum() / df['TR_ADX']
    df['MinusDI'] = 100 * df['MinusDM'].rolling(14).sum() / df['TR_ADX']
    df['DX'] = (abs(df['PlusDI'] - df['MinusDI']) / (df['PlusDI'] + df['MinusDI'] + 1e-9)) * 100
    df['ADX'] = df['DX'].rolling(14).mean()

    # Stochastic Oscillator（%K, %D, 14日, 3日）
    low14 = df['Low'].rolling(14).min()
    high14 = df['High'].rolling(14).max()
    df['Stoch_K'] = 100 * (df['Close'] - low14) / (high14 - low14 + 1e-9)
    df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()

    # Williams %R（14日）
    df['WilliamsR'] = -100 * (high14 - df['Close']) / (high14 - low14 + 1e-9)

    # 関連株リターン（tickerが渡された場合のみ）
    import inspect
    frame = inspect.currentframe().f_back
    ticker = None
    if frame and 'ticker' in frame.f_locals:
        ticker = frame.f_locals['ticker']
    if ticker is not None:
        try:
            from app.models.stock_master_model import StockMaster
            from app.database import SessionLocal
            import random
            session = SessionLocal()
            target = session.query(StockMaster).filter(StockMaster.code == ticker).first()
            if target and target.sector33_code:
                stocks = session.query(StockMaster).filter(
                    StockMaster.sector33_code == target.sector33_code,
                    StockMaster.code != ticker
                ).all()
                sample = random.sample(stocks, min(3, len(stocks)))
                logger.info(f"関連株選択: {[s.code for s in sample]}")
                returns = []
                for s in sample:
                    try:
                        df_rel = load_past_chart_data(ticker=s.code)
                        rel_ret = df_rel['Close'].pct_change().rename(f'{s.code}_ret')
                        returns.append(rel_ret)
                        logger.info(f"関連株 {s.code} リターン取得成功: {rel_ret.shape}")
                    except Exception as e:
                        logger.warning(f"関連株 {s.code} データ取得エラー: {e}")
                if returns:
                    returns_df = pd.concat(returns, axis=1).mean(axis=1)
                    df = df.join(returns_df.rename('related_ret'))
                    logger.info(f"related_ret列追加: {df['related_ret'].notnull().sum()}件")
                else:
                    logger.info("関連株リターンが取得できませんでした")
            session.close()
        except Exception as e:
            logger.warning(f"関連株リターン取得エラー: {e}")

    features = [
        'Close', 'MA5', 'MA10', 'MA15', 'Diff',
        'PriceChangeRate',
        'BB_Mid', 'BB_Upper', 'BB_Lower',
        'MACD', 'MACD_Signal',
        'VolumeChangeRate',
        'Return1', 'Volatility', 'RSI', 'Volume',
        'ATR', 'ADX', 'Stoch_K', 'Stoch_D', 'WilliamsR',
        'weekday', 'month',
        'temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'weathercode'
    ]
    if 'related_ret' in df:
        features.append('related_ret')
    # 外れ値除去（Z-score±3超をNaN化→dropna）
    from scipy.stats import zscore
    df_z = df[features].apply(zscore)
    outlier_mask = (df_z.abs() > 3)
    df[features] = df[features].mask(outlier_mask)
    logger.info(f"外れ値除去後 NaN件数: {df[features].isnull().sum().to_dict()}")
    df = df.dropna(subset=features)
    logger.info(f"外れ値除去・欠損除去後: {df[features].shape}, ラベル: {df['Label'].shape}")
    # 正規化（StandardScaler）
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])
    logger.info(f"正規化完了: {X_scaled.shape}")
    return pd.DataFrame(X_scaled, index=df.index, columns=features), df['Label']

class Net(nn.Module):
    def __init__(self, input_dim):
        super(Net, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.fc(x)

# LSTM時系列モデル
class LSTMNet(nn.Module):
    def __init__(self, input_dim, hidden_dim=32, num_layers=1):
        super(LSTMNet, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        out, _ = self.lstm(x)
        out = out[:, -1, :]  # 最後の時刻
        return self.fc(out)

def train_lstm_model(X_train, y_train, input_dim, seq_len=20, epochs=50):
    logger.info(f"LSTM学習開始: X_train={X_train.shape}, y_train={y_train.shape}, input_dim={input_dim}, seq_len={seq_len}")
    import inspect
    frame = inspect.currentframe().f_back
    optimize = False
    if frame and 'optimize' in frame.f_locals:
        optimize = frame.f_locals['optimize']
    # 時系列データ生成
    X_seq = []
    y_seq = []
    for i in range(len(X_train) - seq_len):
        X_seq.append(X_train[i:i+seq_len])
        y_seq.append(y_train.values[i+seq_len-1])
    X_seq = torch.FloatTensor(X_seq)
    y_seq = torch.FloatTensor(y_seq).unsqueeze(1)
    if optimize:
        logger.info("LSTMハイパーパラメータ探索開始")
        best_acc = -1
        best_model = None
        best_params = None
        for hidden_dim in [16, 32, 64]:
            for num_layers in [1, 2]:
                for lr in [0.001, 0.01, 0.05]:
                    for ep in [30, 50]:
                        model = LSTMNet(input_dim, hidden_dim=hidden_dim, num_layers=num_layers)
                        criterion = nn.BCELoss()
                        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
                        best_loss = float('inf')
                        patience = 10
                        patience_counter = 0
                        for epoch in range(ep):
                            outputs = model(X_seq)
                            loss = criterion(outputs, y_seq)
                            optimizer.zero_grad()
                            loss.backward()
                            optimizer.step()
                            if loss.item() < best_loss:
                                best_loss = loss.item()
                                patience_counter = 0
                            else:
                                patience_counter += 1
                                if patience_counter > patience:
                                    break
                        # 簡易評価（学習データでの精度）
                        preds = (model(X_seq).detach().numpy().flatten() > 0.5).astype(int)
                        acc = (preds == y_seq.numpy().flatten()).mean()
                        if acc > best_acc:
                            best_acc = acc
                            best_model = model
                            best_params = {'hidden_dim': hidden_dim, 'num_layers': num_layers, 'lr': lr, 'epochs': ep}
        logger.info(f"LSTM最適パラメータ: {best_params}, acc={best_acc:.4f}")
        return best_model
    else:
        model = LSTMNet(input_dim)
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        best_loss = float('inf')
        patience = 10
        patience_counter = 0
        for epoch in range(epochs):
            outputs = model(X_seq)
            loss = criterion(outputs, y_seq)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            if epoch % 10 == 0 or epoch == epochs-1:
                logger.info(f"LSTM epoch {epoch}: loss={loss.item():.4f}")
            if loss.item() < best_loss:
                best_loss = loss.item()
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter > patience:
                    logger.info(f"LSTM Early stopping at epoch {epoch}")
                    break
        logger.info(f"LSTM学習終了: best_loss={best_loss:.4f}")
        return model

def train_model_excel(X_train, y_train, input_dim, epochs=100):
    logger.info(f"PyTorch学習開始: X_train={X_train.shape}, y_train={y_train.shape}, input_dim={input_dim}")
    import inspect
    frame = inspect.currentframe().f_back
    optimize = False
    if frame and 'optimize' in frame.f_locals:
        optimize = frame.f_locals['optimize']
    X_train = torch.FloatTensor(X_train)
    y_train = torch.FloatTensor(y_train.values).unsqueeze(1)
    if optimize:
        logger.info("PyTorchハイパーパラメータ探索開始")
        best_acc = -1
        best_model = None
        best_params = None
        for hidden_dim in [16, 32, 64]:
            for dropout in [0.1, 0.2, 0.3]:
                for lr in [0.001, 0.01, 0.05]:
                    for ep in [50, 100]:
                        model = Net(input_dim)
                        # Dropout変更
                        model.fc[2] = nn.Dropout(dropout)
                        criterion = nn.BCELoss()
                        optimizer = torch.optim.Adam(model.parameters(), lr=lr)
                        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)
                        best_loss = float('inf')
                        patience = 10
                        patience_counter = 0
                        for epoch in range(ep):
                            outputs = model(X_train)
                            loss = criterion(outputs, y_train)
                            optimizer.zero_grad()
                            loss.backward()
                            optimizer.step()
                            scheduler.step()
                            if loss.item() < best_loss:
                                best_loss = loss.item()
                                patience_counter = 0
                            else:
                                patience_counter += 1
                                if patience_counter > patience:
                                    break
                        # 簡易評価（学習データでの精度）
                        preds = (model(X_train).detach().numpy().flatten() > 0.5).astype(int)
                        acc = (preds == y_train.numpy().flatten()).mean()
                        if acc > best_acc:
                            best_acc = acc
                            best_model = model
                            best_params = {'hidden_dim': hidden_dim, 'dropout': dropout, 'lr': lr, 'epochs': ep}
        logger.info(f"PyTorch最適パラメータ: {best_params}, acc={best_acc:.4f}")
        return best_model
    else:
        model = Net(input_dim)
        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)
        best_loss = float('inf')
        patience = 10
        patience_counter = 0
        for epoch in range(epochs):
            outputs = model(X_train)
            loss = criterion(outputs, y_train)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
            if epoch % 10 == 0 or epoch == epochs-1:
                logger.info(f"epoch {epoch}: loss={loss.item():.4f}")
            if loss.item() < best_loss:
                best_loss = loss.item()
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter > patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
        logger.info(f"PyTorch学習終了: best_loss={best_loss:.4f}")
        return model

def train_lightgbm_excel(X_train, y_train):
    logger.info(f"LightGBM学習開始: X_train={X_train.shape}, y_train={y_train.shape}")
    from sklearn.model_selection import GridSearchCV
    import lightgbm as lgbm
    # デフォルトパラメータ
    params = {
        'objective': 'binary',
        'metric': 'binary_error',
        'verbosity': -1,
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9
    }
    # ハイパーパラメータ探索用GridSearchCV
    def train_with_gridsearch(X_train, y_train):
        logger.info("LightGBM GridSearchCVによるハイパーパラメータ探索開始")
        estimator = lgbm.LGBMClassifier(objective='binary', boosting_type='gbdt', metric='binary_error', verbosity=-1)
        param_grid = {
            'num_leaves': [15, 31, 63],
            'learning_rate': [0.01, 0.05, 0.1],
            'feature_fraction': [0.7, 0.9, 1.0],
            'n_estimators': [50, 100, 200]
        }
        grid = GridSearchCV(estimator, param_grid, cv=3, scoring='accuracy', verbose=1, n_jobs=-1)
        grid.fit(X_train, y_train)
        logger.info(f"GridSearchCV best_params: {grid.best_params_}")
        return grid.best_estimator_
    # optimizeフラグで切り替え
    optimize = False
    import inspect
    frame = inspect.currentframe().f_back
    if frame and 'optimize' in frame.f_locals:
        optimize = frame.f_locals['optimize']
    if optimize:
        model = train_with_gridsearch(X_train, y_train)
    else:
        lgb_train = lgb.Dataset(X_train, label=y_train)
        model = lgb.train(params, lgb_train, num_boost_round=100)
    logger.info(f"LightGBM学習終了")
    return model

def predict_probability_excel():
    logger.info(f"予測確率計算開始")
    df = load_past_chart_data()
    X, y = create_features_from_excel(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)
    model = train_model_excel(X_train, y_train, X.shape[1])
    latest = torch.from_numpy(X_scaled[-1].astype('float32')).unsqueeze(0)
    prob = model(latest).item()
    logger.info(f"最新データ予測確率: {prob:.4f}")
    return prob

def predict_ensemble_excel(X, pytorch_model, lgb_model, lstm_model=None, seq_len=20, weights=None):
    """
    2モデル（PyTorch, LightGBM）または3モデル（+LSTM）の重み付きアンサンブル予測
    weights: [w_pytorch, w_lgb, w_lstm]（Noneなら均等）
    """
    X_tensor = torch.FloatTensor(X)
    pytorch_pred = pytorch_model(X_tensor).detach().numpy().flatten()
    lgb_pred = lgb_model.predict(X)
    if lstm_model is not None:
        preds_lstm = predict_lstm(X, lstm_model, seq_len=seq_len)
        # Noneを除外
        valid_idx = [i for i, p in enumerate(preds_lstm) if p is not None]
        pytorch_pred = pytorch_pred[valid_idx]
        lgb_pred = lgb_pred[valid_idx]
        lstm_pred = np.array([preds_lstm[i] for i in valid_idx])
        if weights is None:
            weights = [1/3, 1/3, 1/3]
        ensemble = weights[0]*pytorch_pred + weights[1]*lgb_pred + weights[2]*lstm_pred
        return ensemble, valid_idx
    else:
        if weights is None:
            weights = [0.5, 0.5]
        ensemble = weights[0]*pytorch_pred + weights[1]*lgb_pred
        return ensemble, None

def get_cv_accuracy_excel(n_splits=5):
    logger.info(f"クロスバリデーション精度計算開始 (n_splits={n_splits})")
    df = load_past_chart_data()
    X, y = create_features_from_excel(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    acc_list = []
    for i, (train_idx, test_idx) in enumerate(kf.split(X_scaled)):
        logger.info(f"Fold {i+1}/{n_splits}")
        X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        pytorch_model = train_model_excel(X_train, y_train, X.shape[1])
        lgb_model = train_lightgbm_excel(X_train, y_train)
        preds = predict_ensemble_excel(X_test, pytorch_model, lgb_model)
        preds_label = (preds > 0.5).astype(int)
        acc = (preds_label == y_test.values).mean()
        logger.info(f"Fold {i+1} accuracy: {acc:.4f}")
        acc_list.append(acc)
    mean_acc = sum(acc_list) / len(acc_list)
    logger.info(f"クロスバリデーション平均精度: {mean_acc:.4f}")
    return mean_acc

from sklearn.linear_model import LogisticRegression

def get_model_accuracy_excel(ticker=None):
    logger.info(f"モデル精度評価開始（PyTorch, LightGBM, LSTM Stackingアンサンブル）")
    df = load_past_chart_data(ticker=ticker)
    X, y = create_features_from_excel(df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)
    input_dim = X.shape[1]
    feature_names = list(X.columns)
    # PyTorch
    pytorch_model = train_model_excel(X_train, y_train, input_dim)
    X_test_tensor = torch.FloatTensor(X_test)
    preds_pt = pytorch_model(X_test_tensor).detach().numpy().flatten()
    # LightGBM
    lgb_model = train_lightgbm_excel(X_train, y_train)
    preds_lgb = lgb_model.predict(X_test)
    # LSTM
    seq_len = 20
    lstm_model = train_lstm_model(X_train, y_train, input_dim, seq_len=seq_len, epochs=50)
    preds_lstm = predict_lstm(X_test, lstm_model, seq_len=seq_len)
    # Noneを除外
    valid_idx = [i for i, p in enumerate(preds_lstm) if p is not None]
    preds_pt_valid = preds_pt[valid_idx]
    preds_lgb_valid = preds_lgb[valid_idx]
    preds_lstm_valid = np.array([preds_lstm[i] for i in valid_idx])
    y_test_valid = y_test.values[valid_idx]
    # Stacking用特徴量
    X_stack = np.vstack([preds_pt_valid, preds_lgb_valid, preds_lstm_valid]).T
    # メタモデル学習
    meta = LogisticRegression()
    meta.fit(X_stack, y_test_valid)
    # メタモデル予測
    stack_pred = meta.predict(X_stack)
    acc_stack = (stack_pred == y_test_valid).mean()
    logger.info(f"Stackingアンサンブル精度: {acc_stack:.4f}")
    # 各モデル精度も計算
    acc_pt = (preds_pt_valid > 0.5).astype(int)
    acc_pt = (acc_pt == y_test_valid).mean()
    acc_lgb = (preds_lgb_valid > 0.5).astype(int)
    acc_lgb = (acc_lgb == y_test_valid).mean()
    acc_lstm = (preds_lstm_valid > 0.5).astype(int)
    acc_lstm = (acc_lstm == y_test_valid).mean()

    # --- 特徴量重要度計算 ---
    importances = {}
    # LightGBM: feature_importances_
    if hasattr(lgb_model, 'feature_importance'):
        importances['LightGBM'] = dict(zip(feature_names, lgb_model.feature_importance().tolist()))
    elif hasattr(lgb_model, 'feature_importances_'):
        importances['LightGBM'] = dict(zip(feature_names, lgb_model.feature_importances_.tolist()))
    # PyTorch: permutation importance
    try:
        from sklearn.inspection import permutation_importance
        def pytorch_predict(X):
            X_tensor = torch.FloatTensor(X)
            return pytorch_model(X_tensor).detach().numpy().flatten()
        result_pt = permutation_importance(
            estimator=None, X=X_test, y=y_test, n_repeats=5,
            random_state=42, scoring='accuracy',
            n_jobs=1,
            # estimator=Noneで自前predict関数を使う
            # sklearn>=1.3.0でscoring/predict_funcサポート
            predict_func=pytorch_predict if 'predict_func' in permutation_importance.__code__.co_varnames else None
        )
        importances['PyTorch'] = dict(zip(feature_names, result_pt.importances_mean))
    except Exception as e:
        importances['PyTorch'] = f'計算不可: {e}'
    # LSTM: permutation importance
    try:
        def lstm_predict(X):
            preds = predict_lstm(X, lstm_model, seq_len=seq_len)
            valid_idx = [i for i, p in enumerate(preds) if p is not None]
            return np.array([preds[i] for i in valid_idx])
        result_lstm = permutation_importance(
            estimator=None, X=X_test, y=y_test, n_repeats=5,
            random_state=42, scoring='accuracy',
            n_jobs=1,
            predict_func=lstm_predict if 'predict_func' in permutation_importance.__code__.co_varnames else None
        )
        importances['LSTM'] = dict(zip(feature_names, result_lstm.importances_mean))
    except Exception as e:
        importances['LSTM'] = f'計算不可: {e}'

    # 結果を詳細に返す（Stackingを4番目, 重要度も返す）
    return acc_pt, acc_lgb, acc_lstm, acc_stack, importances

def predict_lstm(X, lstm_model, seq_len=20):
    # X: (N, input_dim)
    preds = []
    for i in range(seq_len, len(X)+1):
        X_seq = torch.FloatTensor(X[i-seq_len:i]).unsqueeze(0)
        pred = lstm_model(X_seq).item()
        preds.append(pred)
    # 先頭seq_len-1は予測不可
    return [None]*(seq_len-1) + preds

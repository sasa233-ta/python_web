import yfinance as yf
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os
import pickle
import datetime
import random
from app.models.stock_master_model import StockMaster  # モデル名は適宜調整
from app.database import SessionLocal

# 1. 株価データの取得
def fetch_stock_data(ticker='AAPL', period='3y'):
    df = yf.download(ticker, period=period)
    df = df[['Close']]
    df['Return+3'] = df['Close'].shift(-3) > df['Close']
    df['Label'] = df['Return+3'].astype(int)
    df = df.dropna()
    return df

def get_related_stock_returns(target_symbol, session, period='3y', n=5):
    # sector_code33を取得
    target = session.query(StockMaster).filter(StockMaster.symbol == target_symbol).first()
    if not target or not target.sector_code33:
        return None
    # 同じsector_code33の銘柄をランダムに5つ取得（自身は除外）
    stocks = session.query(StockMaster).filter(
        StockMaster.sector_code33 == target.sector_code33,
        StockMaster.symbol != target_symbol
    ).all()
    if not stocks:
        return None
    sample = random.sample(stocks, min(n, len(stocks)))
    returns = []
    for s in sample:
        df = fetch_stock_data(s.symbol, period=period)
        if 'Close' in df:
            ret = df['Close'].pct_change().rename(f'{s.symbol}_ret')
            returns.append(ret)
    if not returns:
        return None
    # 各日付で平均を計算
    returns_df = pd.concat(returns, axis=1).mean(axis=1)
    return returns_df

# 2. 特徴量の作成（単純な例）
def create_features(df, symbol=None):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['Diff'] = df['MA5'] - df['MA10']
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
    # 関連株リターン
    if symbol is not None:
        session = SessionLocal()
        rel_ret = get_related_stock_returns(symbol, session, n=5)
        session.close()
        if rel_ret is not None:
            df = df.join(rel_ret.rename('related_ret'))
    df = df.dropna()
    features = ['Close', 'MA5', 'MA10', 'Diff', 'Return1', 'Volatility', 'RSI']
    if 'related_ret' in df:
        features.append('related_ret')
    return df[features], df['Label']

# 3. PyTorch モデル定義
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

# 4. 学習・予測関数
def train_model(X_train, y_train, input_dim, epochs=100):
    model = Net(input_dim)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)

    X_train = torch.FloatTensor(X_train)
    y_train = torch.FloatTensor(y_train.values).unsqueeze(1)

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

        if loss.item() < best_loss:
            best_loss = loss.item()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter > patience:
                print(f"Early stopping at epoch {epoch}")
                break

    return model

# 5. 実行部分
def predict_probability(ticker='AAPL'):
    df = fetch_stock_data(ticker)
    X, y = create_features(df)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, shuffle=False)

    model = train_model(X_train, y_train, X.shape[1])

    # 最新データで予測
    latest = torch.FloatTensor([X_scaled[-1]])
    prob = model(latest).item()
    return prob

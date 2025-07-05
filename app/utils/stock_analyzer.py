import yfinance as yf
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# 1. 株価データの取得
def fetch_stock_data(ticker='AAPL', period='1y'):
    df = yf.download(ticker, period=period)
    df = df[['Close']]
    df['Return+3'] = df['Close'].shift(-3) > df['Close']
    df['Label'] = df['Return+3'].astype(int)
    df = df.dropna()
    return df

# 2. 特徴量の作成（単純な例）
def create_features(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['Diff'] = df['MA5'] - df['MA10']
    df = df.dropna()
    return df[['Close', 'MA5', 'MA10', 'Diff']], df['Label']

# 3. PyTorch モデル定義
class Net(nn.Module):
    def __init__(self, input_dim):
        super(Net, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.fc(x)

# 4. 学習・予測関数
def train_model(X_train, y_train, input_dim, epochs=50):
    model = Net(input_dim)
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    X_train = torch.FloatTensor(X_train)
    y_train = torch.FloatTensor(y_train.values).unsqueeze(1)

    for epoch in range(epochs):
        outputs = model(X_train)
        loss = criterion(outputs, y_train)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
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

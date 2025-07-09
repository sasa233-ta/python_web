FROM python:3.11-slim

WORKDIR /app

# 依存パッケージをインストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体をコピー
COPY . .

# ポート番号は環境変数PORTを展開して起動
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

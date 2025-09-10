from dotenv import load_dotenv
import os

# .envファイルを読み込む
load_dotenv()

# MySQL接続情報（必要に応じて修正）
DB_USER = os.getenv('DB_USER')  # ユーザー名
DB_PASSWORD = os.getenv('DB_PASSWORD')  # パスワード
DB_HOST = os.getenv('DB_HOST')  # ホスト
DB_PORT = os.getenv('DB_PORT')  # ポート
DB_NAME = os.getenv('DB_NAME')  # データベース名
DB_CHARSET = os.getenv('DB_CHARSET')  # 文字コード

# JWTシークレットキー（必要に応じて修正）
JWT_SECRET = os.getenv('JQUANTS_REFRESH_TOKEN')


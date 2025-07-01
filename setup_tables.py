# setup_tables.py
from app.database import Base, engine
from app.models.user_model import User
from app.models.login_history_model import LoginHistory

print("⏳ テーブル作成中...")
Base.metadata.create_all(bind=engine)
print("✅ テーブル作成完了！")
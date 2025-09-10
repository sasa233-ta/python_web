# auth_controller.py : 自動生成されたモジュール
# このファイルに対応する処理を記述してください。

from app.models.user_model import User
from app.core.db import Session
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import logout_user as flask_logout_user

def register_user(username, password):
    session_db = Session()
    if session_db.query(User).filter_by(username=username).first():
        session_db.close()
        return False, '既に登録されています'
    user = User(username=username, password=password)  # 修正: password_hashではなくpasswordを渡す
    session_db.add(user)
    session_db.commit()
    session_db.close()
    return True, '登録成功'

def authenticate_user(username, password):
    session_db = Session()
    user = session_db.query(User).filter_by(username=username).first()
    if user and user.check_password(password):
        session_db.close()
        return user, "ログイン成功"
    session_db.close()
    return None, "ユーザー名またはパスワードが違います"

def logout_user():
    flask_logout_user()
    session.pop('username', None)


from passlib.hash import bcrypt
from datetime import datetime
from fastapi import Request, Response, HTTPException, status
from app.database import SessionLocal
from app.models.user_model import User
from app.models.login_history_model import LoginHistory
from app.core.config import USER_SESSION_COOKIE_NAME, SESSION_COOKIE_MAX_AGE, SESSION_COOKIE_HTTPONLY

USER_SESSION_USERNAME_COOKIE_NAME = "username"

def set_login_session(response: Response, user_id: str, username: str):
    response.set_cookie(
        key=USER_SESSION_COOKIE_NAME,
        value=str(user_id),
        httponly=SESSION_COOKIE_HTTPONLY,
        max_age=SESSION_COOKIE_MAX_AGE
    )
    response.set_cookie(
        key=USER_SESSION_USERNAME_COOKIE_NAME,
        value=username,
        httponly=SESSION_COOKIE_HTTPONLY,
        max_age=SESSION_COOKIE_MAX_AGE
    )

def clear_login_session(response: Response):
    response.delete_cookie(key=USER_SESSION_COOKIE_NAME)
    response.delete_cookie(key=USER_SESSION_USERNAME_COOKIE_NAME)

def get_current_user_id(request: Request) -> str:
    user_id = request.cookies.get(USER_SESSION_COOKIE_NAME)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user_id

def register_user_service(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user:
            return {"success": False, "error": "ユーザー名は既に使われています"}
        hashed_pw = bcrypt.hash(password)
        new_user = User(username=username, hashed_password=hashed_pw)
        db.add(new_user)
        db.commit()
        return {"success": True}
    finally:
        db.close()

def login_user_service(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and bcrypt.verify(password, user.hashed_password):
            def set_session(response):
                set_login_session(response, user.id, user.username)
                login_history = LoginHistory(user_id=user.id, username=user.username, login_at=datetime.utcnow())
                db.add(login_history)
                db.commit()
            return {"success": True, "set_session": set_session}
        return {"success": False, "error": "ログイン失敗"}
    finally:
        db.close()

def logout_user_service(response):
    clear_login_session(response)

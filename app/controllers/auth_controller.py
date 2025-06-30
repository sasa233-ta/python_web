from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
from app.core.config import templates
from app.database import SessionLocal
from app.models.user_model import User
from app.utils.auth_utils import set_login_session, clear_login_session

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register")
def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "ユーザー名は既に使われています"})
    hashed_pw = bcrypt.hash(password)
    new_user = User(username=username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)

@router.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user and bcrypt.verify(password, user.hashed_password):
        response = RedirectResponse(url="/dashboard", status_code=303)
        set_login_session(response, user.id)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "ログイン失敗"})

@router.get("/logout")
def logout_user(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    clear_login_session(response)
    return response
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.config import templates
from app.database import SessionLocal
from app.models.login_history_model import LoginHistory
from app.utils.auth_utils import get_current_user_id

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard")
def dashboard_page(request: Request, user_id: str = Depends(get_current_user_id)):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/login_history")
def login_history_page(request: Request, user_id: str = Depends(get_current_user_id)):
    db = next(get_db())
    histories = db.query(LoginHistory).filter(LoginHistory.user_id == user_id).order_by(LoginHistory.login_at.desc()).all()
    return templates.TemplateResponse("login_history.html", {"request": request, "histories": histories})
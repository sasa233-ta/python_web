from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from app.services.auth_service import register_user_service, login_user_service, logout_user_service, get_current_user_id
from app.services.trade_service import get_holdings_with_pl_service
from app.core.config import templates
from app.database import SessionLocal
from app.models.login_history_model import LoginHistory

router = APIRouter()

@router.get("/")
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/dashboard")
def dashboard_page(request: Request, user_id: str = Depends(get_current_user_id)):
    holdings = get_holdings_with_pl_service(user_id)
    total_pl = sum([h["pl"] for h in holdings if h["pl"] is not None]) if holdings else 0
    return templates.TemplateResponse("dashboard.html", {"request": request, "holdings": holdings, "total_pl": total_pl})

@router.get("/login_history")
def login_history_page(request: Request, user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        histories = db.query(LoginHistory).filter(LoginHistory.user_id == user_id).order_by(LoginHistory.login_at.desc()).all()
        return templates.TemplateResponse("login_history.html", {"request": request, "histories": histories})
    finally:
        db.close()

@router.post("/register")
def register_user(request: Request, username: str = Form(...), password: str = Form(...)):
    result = register_user_service(username, password)
    if result["success"]:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("register.html", {"request": request, "error": result["error"]})

@router.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...)):
    result = login_user_service(username, password)
    if result["success"]:
        response = RedirectResponse(url="/dashboard", status_code=303)
        result["set_session"](response)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": result["error"]})

@router.get("/logout")
def logout_user(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    logout_user_service(response)
    return response

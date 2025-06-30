from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from app.core.config import templates
from app.utils.auth_utils import get_current_user_id

router = APIRouter()

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
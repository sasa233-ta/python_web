from fastapi import APIRouter, Request
from app.core.config import templates

router = APIRouter()

@router.get("/")
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/dashboard")
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})
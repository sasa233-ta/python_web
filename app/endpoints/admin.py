from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import Base, engine
from sqlalchemy import text
import os
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@router.get("/admin/list_tables", response_class=HTMLResponse)
def list_tables(request: Request):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "tables": tables})
    except Exception as e:
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "error": str(e)})

@router.get("/admin/table/{table_name}", response_class=HTMLResponse)
def get_table_data(request: Request, table_name: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result]
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "columns": columns, "rows": rows})
    except Exception as e:
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "error": str(e)})

@router.get("/admin/list_data_dir", response_class=HTMLResponse)
def list_data_dir(request: Request):
    try:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
        if not os.path.exists(data_dir):
            logging.warning(f"{data_dir} ディレクトリが存在しません")
            return templates.TemplateResponse("admin_dashboard.html", {"request": request, "error": f"{data_dir} ディレクトリが存在しません"})
        files = os.listdir(data_dir)
        logging.info(f"{data_dir} 内のファイル一覧: %s", files)
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "files": files})
    except Exception as e:
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "error": str(e)})

@router.post("/admin/update_jpx", response_class=HTMLResponse)
def update_jpx(request: Request):
    try:
        from app.utils.fetch_jpx_listed_companies import fetch_and_import_jpx_listed_companies
        fetch_and_import_jpx_listed_companies()
        msg = "JPX上場銘柄データベースを更新しました"
        logging.info(msg)
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "success": msg})
    except Exception as e:
        logging.error("JPX更新エラー: %s", e)
        return templates.TemplateResponse("admin_dashboard.html", {"request": request, "error": str(e)})

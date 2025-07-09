from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.database import Base, engine
from sqlalchemy import text
import os

router = APIRouter()

@router.get("/admin/list_tables")
def list_tables():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
        return {"tables": tables}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/admin/table/{table_name}")
def get_table_data(table_name: str):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 100"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result]
        return {"columns": columns, "rows": rows}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/admin/list_data_dir")
def list_data_dir():
    try:
        files = os.listdir("/data")
        return {"files": files}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

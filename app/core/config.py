from fastapi.templating import Jinja2Templates

# テンプレート設定
templates = Jinja2Templates(directory="app/templates")

# セッション設定
USER_SESSION_COOKIE_NAME = "user_id"
ADMIN_SESSION_COOKIE_NAME = "admin_id"
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24  # 1日（秒単位）
SESSION_COOKIE_HTTPONLY = True
from fastapi import Request, Response, HTTPException, status
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

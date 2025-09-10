# main.py : 自動生成されたモジュール
# このファイルに対応する処理を記述してください。

from flask import Flask
from flask_login import LoginManager
from app.views.auth_view import auth_bp
from app.views.stock_view import stock_bp
from app.models.user_model import User

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション管理用

# LoginManagerセットアップ
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # 未ログイン時のリダイレクト先

@login_manager.user_loader
def load_user(user_id):
    from app.core.db import Session
    session = Session()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

# Blueprint登録
app.register_blueprint(auth_bp)
app.register_blueprint(stock_bp)

if __name__ == '__main__':
    app.run(debug=True)


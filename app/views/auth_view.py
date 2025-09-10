# auth_view.py : 自動生成されたモジュール
# このファイルに対応する処理を記述してください。


from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user
from app.controllers.auth_controller import authenticate_user, register_user, logout_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user, msg = authenticate_user(username, password)  # userオブジェクトを返すように
        flash(msg)
        if user:
            login_user(user)
            next_url = request.args.get('next')
            if not next_url or not next_url.startswith('/'):
                next_url = url_for('stock.stock_list')
            return redirect(next_url)
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        success, msg = register_user(username, password)
        flash(msg)
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('ログアウトしました')
    return redirect(url_for('auth.login'))


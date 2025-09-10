from flask import Blueprint, render_template, request
from flask_login import login_required
from scripts.fetch_stocks import fetch_and_update_stocks
from app.controllers.stock_controller import get_stocks
from app.controllers.analysis_controller import get_stock_analysis

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/stocks', methods=['GET'])
@login_required
def stock_list():
    fetch_and_update_stocks()  # アクセス時に毎回チェック＆必要ならDL
    keyword = request.args.get('q', '')
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1
    per_page = 25
    stocks, total = get_stocks(keyword=keyword, page=page, per_page=per_page)
    max_page = (total + per_page - 1) // per_page
    return render_template('stock/list.html', stocks=stocks, keyword=keyword, page=page, max_page=max_page, total=total)

@stock_bp.route('/stocks/<string:code>', methods=['GET'])
@login_required
def stock_detail(code):
    stock, _ = get_stocks(keyword=code)
    analysis = get_stock_analysis(code)
    return render_template(
        'stock/detail.html',
        stock=stock,
        analysis=analysis
    )

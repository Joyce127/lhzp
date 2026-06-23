from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services import product_svc

api_product_bp = Blueprint('api_product', __name__, url_prefix='/api/product')


@api_product_bp.route('/search')
@login_required
def search():
    """产品搜索"""
    keyword = request.args.get('keyword', '').strip()
    if not keyword or len(keyword) < 2:
        return jsonify({'code': 0, 'data': []})
    data = product_svc.search_products(keyword)
    return jsonify({'code': 0, 'data': data})


@api_product_bp.route('/<product_id>/profile')
@login_required
def profile(product_id):
    """产品基本信息"""
    data = product_svc.get_product_profile(product_id)
    if data is None:
        return jsonify({'code': 1, 'message': '产品不存在'}), 404
    return jsonify({'code': 0, 'data': data})


@api_product_bp.route('/<product_id>/net-worth')
@login_required
def net_worth(product_id):
    """净值走势数据"""
    period = request.args.get('period', '6m')
    data = product_svc.get_net_worth_history(product_id, period)
    return jsonify({'code': 0, 'data': data})


@api_product_bp.route('/<product_id>/performance')
@login_required
def performance(product_id):
    """业绩指标（可选时间区间）"""
    period = request.args.get('period', '1y')
    data = product_svc.get_performance(product_id, period)
    return jsonify({'code': 0, 'data': data})

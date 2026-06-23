from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services import compare_svc

api_compare_bp = Blueprint('api_compare', __name__, url_prefix='/api/marketing')


@api_compare_bp.route('/compare')
@login_required
def compare():
    ids_str = request.args.get('ids', '')
    ids = [i.strip() for i in ids_str.split(',') if i.strip()]
    if not ids or len(ids) < 2:
        return jsonify({'code': 1, 'message': '请至少选择2个产品'}), 400
    data = compare_svc.compare_products(ids)
    if data is None:
        return jsonify({'code': 1, 'message': '对比数据获取失败'}), 500
    return jsonify({'code': 0, 'data': data})

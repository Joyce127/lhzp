from flask import Blueprint, jsonify
from flask_login import login_required
from app.services import asset_svc

api_asset_bp = Blueprint('api_asset', __name__, url_prefix='/api/asset')


@api_asset_bp.route('/<product_id>/allocation')
@login_required
def allocation(product_id):
    data = asset_svc.get_asset_allocation(product_id)
    if data is None:
        return jsonify({'code': 1, 'message': '数据不存在'}), 404
    return jsonify({'code': 0, 'data': data})

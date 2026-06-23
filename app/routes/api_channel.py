from flask import Blueprint, jsonify
from flask_login import login_required
from app.services import channel_svc

api_channel_bp = Blueprint('api_channel', __name__, url_prefix='/api/channel')


@api_channel_bp.route('/list')
@login_required
def channel_list():
    data = channel_svc.get_channel_list()
    return jsonify({'code': 0, 'data': data})


@api_channel_bp.route('/<int:org_id>/overview')
@login_required
def channel_overview(org_id):
    data = channel_svc.get_channel_overview(org_id)
    if data is None:
        return jsonify({'code': 1, 'message': '渠道不存在'}), 404
    return jsonify({'code': 0, 'data': data})


@api_channel_bp.route('/regions')
@login_required
def regions():
    data = channel_svc.get_region_data()
    return jsonify({'code': 0, 'data': data})

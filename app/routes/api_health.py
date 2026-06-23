from flask import Blueprint, jsonify
from flask_login import login_required
from app.services import health_svc

api_health_bp = Blueprint('api_health', __name__, url_prefix='/api/health')


@api_health_bp.route('/scan')
@login_required
def scan():
    data = health_svc.get_health_scan()
    return jsonify({'code': 0, 'data': data})

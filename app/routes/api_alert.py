from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services import alert_svc

api_alert_bp = Blueprint('api_alert', __name__, url_prefix='/api/alert')


@api_alert_bp.route('/list')
@login_required
def alert_list():
    status = request.args.get('status')
    alert_type = request.args.get('type')
    data = alert_svc.get_alert_list(status=status, alert_type=alert_type)
    return jsonify({'code': 0, 'data': data})

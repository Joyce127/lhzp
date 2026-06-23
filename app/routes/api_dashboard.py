from flask import Blueprint, jsonify
from flask_login import login_required
from app.services import cockpit_svc

api_dashboard_bp = Blueprint('api_dashboard', __name__, url_prefix='/api/dashboard')


@api_dashboard_bp.route('/overview')
@login_required
def overview():
    """驾驶舱KPI卡片数据"""
    data = cockpit_svc.get_overview_kpi()
    return jsonify({'code': 0, 'data': data})


@api_dashboard_bp.route('/scale-structure')
@login_required
def scale_structure():
    """规模结构饼图数据"""
    data = cockpit_svc.get_scale_structure()
    return jsonify({'code': 0, 'data': data})


@api_dashboard_bp.route('/risk-indicators')
@login_required
def risk_indicators():
    """核心风险收益指标"""
    data = cockpit_svc.get_risk_indicators()
    return jsonify({'code': 0, 'data': data})


@api_dashboard_bp.route('/alert-summary')
@login_required
def alert_summary():
    """预警摘要列表"""
    data = cockpit_svc.get_alert_summary()
    return jsonify({'code': 0, 'data': data})

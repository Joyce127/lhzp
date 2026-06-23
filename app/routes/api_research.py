from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services import research_svc

api_research_bp = Blueprint('api_research', __name__, url_prefix='/api/research')


@api_research_bp.route('/managers')
@login_required
def managers():
    search = request.args.get('search', '')
    data = research_svc.get_manager_list(search=search)
    return jsonify({'code': 0, 'data': data})


@api_research_bp.route('/manager/<int:manager_id>')
@login_required
def manager_detail(manager_id):
    data = research_svc.get_manager_detail(manager_id)
    if data is None:
        return jsonify({'code': 1, 'message': '投资经理不存在'}), 404
    return jsonify({'code': 0, 'data': data})


@api_research_bp.route('/org-dynamics')
@login_required
def org_dynamics():
    data = research_svc.get_org_dynamics()
    return jsonify({'code': 0, 'data': data})


@api_research_bp.route('/transactions')
@login_required
def transactions():
    product_id = request.args.get('product_id')
    data = research_svc.get_related_transactions(product_id)
    return jsonify({'code': 0, 'data': data})

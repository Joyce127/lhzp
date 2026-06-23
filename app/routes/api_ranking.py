from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services import ranking_svc

api_ranking_bp = Blueprint('api_ranking', __name__, url_prefix='/api/ranking')


@api_ranking_bp.route('/list')
@login_required
def ranking_list():
    rank_type = request.args.get('type', 'return')
    period = request.args.get('period', '3m')
    category = request.args.get('category')
    issuer = request.args.get('issuer')
    page = int(request.args.get('page', 1))

    data = ranking_svc.get_ranking(
        rank_type=rank_type, period=period,
        category=category, issuer=issuer, page=page
    )
    return jsonify({'code': 0, 'data': data})


@api_ranking_bp.route('/categories')
@login_required
def categories():
    data = ranking_svc.get_ranking_categories()
    return jsonify({'code': 0, 'data': data})


@api_ranking_bp.route('/issuers')
@login_required
def issuers():
    data = ranking_svc.get_issuer_list()
    return jsonify({'code': 0, 'data': data})

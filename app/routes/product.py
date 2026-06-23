from flask import Blueprint, render_template, request
from flask_login import login_required

product_bp = Blueprint('product', __name__, url_prefix='/product')


@product_bp.route('/360')
@login_required
def profile():
    return render_template('product/profile.html')


@product_bp.route('/ranking')
@login_required
def ranking():
    return render_template('product/ranking.html')


@product_bp.route('/asset')
@login_required
def asset():
    return render_template('product/asset.html')


@product_bp.route('/research')
@login_required
def research():
    return render_template('product/research.html')

from flask import Blueprint, render_template
from flask_login import login_required

marketing_bp = Blueprint('marketing', __name__, url_prefix='/marketing')


@marketing_bp.route('/channel')
@login_required
def channel():
    return render_template('marketing/channel.html')


@marketing_bp.route('/compare')
@login_required
def compare():
    return render_template('marketing/compare.html')

from flask import Blueprint, render_template
from flask_login import login_required

riskctrl_bp = Blueprint('riskctrl', __name__, url_prefix='/risk')


@riskctrl_bp.route('/alert')
@login_required
def alert():
    return render_template('riskctrl/alert.html')


@riskctrl_bp.route('/health')
@login_required
def health():
    return render_template('riskctrl/health.html')

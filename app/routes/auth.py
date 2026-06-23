from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.extensions import limiter

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        # 检查账号是否被锁定
        if user and user.locked_until and user.locked_until > datetime.utcnow():
            remain = int((user.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            flash(f'账号已被临时锁定，请 {remain} 分钟后重试', 'danger')
            return render_template('auth/login.html')

        if user and user.check_password(password):
            # 登录成功，重置计数
            user.login_attempts = 0
            user.locked_until = None
            from app.extensions import db
            db.session.commit()

            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            flash(f'欢迎回来，{user.display_name}！', 'success')
            return redirect(next_page or url_for('dashboard.index'))

        # 登录失败
        if user:
            user.login_attempts += 1
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                flash('密码错误次数过多，账号已被锁定15分钟', 'danger')
            else:
                remaining = 5 - user.login_attempts
                flash(f'用户名或密码错误，还剩 {remaining} 次尝试机会', 'danger')
            from app.extensions import db
            db.session.commit()
        else:
            flash('用户名或密码错误', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已安全退出', 'info')
    return redirect(url_for('auth.login'))

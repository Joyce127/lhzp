import os
from flask import Flask
from config import Config
from app.extensions import db, login_manager, limiter


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # 创建本地 auth.db 表
    with app.app_context():
        from app.models.user import User
        is_new = not os.path.exists(os.path.join(app.instance_path, 'auth.db'))
        db.create_all(bind_key='auth')
        passwords = User.init_default_users()
        if is_new and passwords:
            print('\n' + '=' * 50)
            print('  初始管理员账号（请妥善保管）：')
            for uname, pwd in passwords.items():
                print(f'  {uname}: {pwd}')
            print('=' * 50 + '\n')

    # Flask-Login 用户加载器
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # 注册 Blueprint
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.product import product_bp
    from app.routes.marketing import marketing_bp
    from app.routes.riskctrl import riskctrl_bp
    from app.routes.api_product import api_product_bp
    from app.routes.api_dashboard import api_dashboard_bp
    from app.routes.api_ranking import api_ranking_bp
    from app.routes.api_asset import api_asset_bp
    from app.routes.api_research import api_research_bp
    from app.routes.api_alert import api_alert_bp
    from app.routes.api_health import api_health_bp
    from app.routes.api_channel import api_channel_bp
    from app.routes.api_compare import api_compare_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(marketing_bp)
    app.register_blueprint(riskctrl_bp)
    app.register_blueprint(api_product_bp)
    app.register_blueprint(api_dashboard_bp)
    app.register_blueprint(api_ranking_bp)
    app.register_blueprint(api_asset_bp)
    app.register_blueprint(api_research_bp)
    app.register_blueprint(api_alert_bp)
    app.register_blueprint(api_health_bp)
    app.register_blueprint(api_channel_bp)
    app.register_blueprint(api_compare_bp)

    # 上下文处理器：注入当前用户信息到所有模板
    @app.context_processor
    def inject_user():
        from flask_login import current_user
        if current_user.is_authenticated:
            return {
                'current_user': current_user,
                'user_modules': current_user.ROLE_MODULES.get(current_user.role, []),
            }
        return {}

    return app

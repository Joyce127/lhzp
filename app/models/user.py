import re
import secrets
import string
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    """用户模型 — 存储在本地 SQLite auth.db"""
    __bind_key__ = 'auth'
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    ROLE_LABELS = {
        'admin': '管理员',
        'product': '产品投研',
        'marketing': '营销渠道',
        'risk': '风控合规',
        'viewer': '只读用户',
    }

    ROLE_MODULES = {
        'admin': ['dashboard', 'product', 'marketing', 'riskctrl'],
        'product': ['dashboard', 'product'],
        'marketing': ['dashboard', 'marketing'],
        'risk': ['dashboard', 'riskctrl'],
        'viewer': ['dashboard'],
    }

    @staticmethod
    def validate_password(password):
        """校验密码强度：至少8位，包含大小写字母+数字+特殊字符"""
        if len(password) < 12:
            return False, '密码长度至少12位'
        if not re.search(r'[A-Z]', password):
            return False, '密码需包含大写字母'
        if not re.search(r'[a-z]', password):
            return False, '密码需包含小写字母'
        if not re.search(r'[0-9]', password):
            return False, '密码需包含数字'
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\"\\|,.<>\/?]', password):
            return False, '密码需包含特殊字符'
        return True, ''

    @staticmethod
    def generate_strong_password():
        """生成12位强随机密码"""
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        while True:
            pwd = ''.join(secrets.choice(chars) for _ in range(16))
            # 确保包含各类字符
            if (re.search(r'[A-Z]', pwd) and re.search(r'[a-z]', pwd)
                    and re.search(r'[0-9]', pwd) and re.search(r'[!@#$%^&*]', pwd)):
                return pwd

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_access(self, module_name):
        return module_name in self.ROLE_MODULES.get(self.role, [])

    @property
    def role_label(self):
        return self.ROLE_LABELS.get(self.role, self.role)

    @classmethod
    def init_default_users(cls):
        """初始化预置用户账号（强密码）"""
        defaults = [
            {'username': 'admin', 'display_name': '管理员', 'role': 'admin'},
            {'username': 'product', 'display_name': '产品经理', 'role': 'product'},
            {'username': 'marketing', 'display_name': '市场经理', 'role': 'marketing'},
            {'username': 'risk', 'display_name': '风控经理', 'role': 'risk'},
            {'username': 'viewer', 'display_name': '访客', 'role': 'viewer'},
        ]
        passwords = {}
        for u in defaults:
            if not cls.query.filter_by(username=u['username']).first():
                user = cls(
                    username=u['username'],
                    display_name=u['display_name'],
                    role=u['role'],
                )
                pwd = cls.generate_strong_password()
                user.set_password(pwd)
                db.session.add(user)
                passwords[u['username']] = pwd
        db.session.commit()
        return passwords

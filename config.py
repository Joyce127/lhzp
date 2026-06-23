import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 加载 .env 文件（本地开发用；生产环境直接设置系统环境变量）
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('未设置 SECRET_KEY 环境变量，请检查 .env 文件')

    # 远程 PostgreSQL 数据库
    PG_HOST = os.environ.get('PG_HOST')
    PG_PORT = os.environ.get('PG_PORT', '5432')
    PG_USER = os.environ.get('PG_USER')
    PG_PASSWORD = os.environ.get('PG_PASSWORD')
    PG_DATABASE = os.environ.get('PG_DATABASE')

    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        if not all([PG_HOST, PG_USER, PG_PASSWORD, PG_DATABASE]):
            raise RuntimeError(
                '数据库连接信息不完整。请在 .env 中设置 DATABASE_URL 或 '
                '(PG_HOST, PG_USER, PG_PASSWORD, PG_DATABASE)'
            )
        DATABASE_URL = (
            f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}'
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # 本地 SQLite 数据库（用户认证）
    SQLALCHEMY_BINDS = {
        'auth': f'sqlite:///{os.path.join(BASE_DIR, "instance", "auth.db")}',
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }

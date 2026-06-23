from sqlalchemy import create_engine, MetaData, Table, inspect, text
from config import Config

_engine = None
_metadata = MetaData()
_reflected_tables = {}


def get_engine():
    """获取 PostgreSQL 数据库引擎（单例）"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            Config.SQLALCHEMY_DATABASE_URI,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _engine


def reflect_table(table_name: str) -> Table:
    """反射单张表，返回 SQLAlchemy Table 对象（带缓存）"""
    global _reflected_tables
    if table_name not in _reflected_tables:
        engine = get_engine()
        table = Table(table_name, _metadata, autoload_with=engine)
        _reflected_tables[table_name] = table
    return _reflected_tables[table_name]


def get_all_table_names():
    """获取 PostgreSQL 数据库中所有表名"""
    engine = get_engine()
    inspector = inspect(engine)
    return inspector.get_table_names()


def execute_query(sql: str, params=None):
    """执行原始 SQL 查询，返回结果列表"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]


def execute_scalar(sql: str, params=None):
    """执行 SQL 查询，返回单个标量值"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        row = result.fetchone()
        return row[0] if row else None


def execute_single(sql: str, params=None):
    """执行 SQL 查询，返回单行 dict"""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        row = result.fetchone()
        if row:
            columns = result.keys()
            return dict(zip(columns, row))
        return None


def get_year_table_name(base_pattern: str, year: int = None):
    """处理年份分表名称，如 max_drawdown -> lh_dc_wealth_max_drawdown_20192025"""
    # 大部分分表是 _20192025 后缀
    return f"{base_pattern}_20192025"

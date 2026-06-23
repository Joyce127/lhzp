"""
市场与投研洞察服务（原型五）
投资经理画像、竞品机构动态、关联交易监控
"""
from app.models.base import execute_query, execute_single


def get_manager_list(search=None):
    """获取投资经理列表"""
    base_sql = """
        SELECT * FROM lh_dc_wealth_inv_manager_basic_info
        WHERE valid = 1
    """
    if search:
        results = execute_query(
            base_sql + " AND full_name LIKE :kw ORDER BY manager_start_date DESC LIMIT 20",
            {'kw': f'%{search}%'}
        )
    else:
        results = execute_query(
            base_sql + " ORDER BY manager_start_date DESC LIMIT 20"
        )
    return results or []


def get_manager_detail(manager_id: int):
    """获取投资经理详细画像"""
    manager = execute_single("""
        SELECT * FROM lh_dc_wealth_inv_manager_basic_info
        WHERE id = :mid
    """, {'mid': manager_id})

    if not manager:
        return None

    # 管理的产品
    products = execute_query("""
        SELECT p.product_id, p.product_name, r.start_date, r.end_date
        FROM lh_dc_wealth_product_manager_relation r
        JOIN lh_dc_wealth_product p ON r.product_id = p.product_id
        WHERE r.manager_id = :mid AND p.valid = 1
        LIMIT 30
    """, {'mid': manager.get('manager_id')})

    return {
        'manager': manager,
        'products': products or [],
    }


def get_org_dynamics(limit=10):
    """获取竞品机构动态（托管业务指标）"""
    results = execute_query("""
        SELECT * FROM lh_dc_wealth_custody_business_indicators
        ORDER BY report_date DESC
        LIMIT :lim
    """, {'lim': limit})
    return results or []


def get_related_transactions(product_id: str = None):
    """获取关联交易记录"""
    tables = {
        'lh_dc_wealth_inv_related_issue': '投资关联方发行证券',
        'lh_dc_wealth_inv_related_underwriting': '投资关联方承销证券',
        'lh_dc_wealth_inv_related_other': '其他重大关联交易',
    }
    all_transactions = []
    for table_name, label in tables.items():
        if product_id:
            sql = f"SELECT *, '{label}' as tx_type FROM {table_name} WHERE product_id = :pid LIMIT 20"
            results = execute_query(sql, {'pid': product_id})
        else:
            sql = f"SELECT *, '{label}' as tx_type FROM {table_name} LIMIT 10"
            results = execute_query(sql)
        all_transactions.extend(results or [])

    return all_transactions

"""
资产配置透视服务（原型四）
提供投资范围vs实际配置对比、前十大持仓、杠杆分析
"""
from app.models.base import execute_query, execute_single, execute_scalar


def get_asset_allocation(product_id: str):
    """获取资产配置数据"""
    # 穿透后资产占比
    allocation = execute_query("""
        SELECT asset_type, asset_ratio
        FROM lh_dc_wealth_asset_penetrating_prop
        WHERE product_id = :pid
        ORDER BY asset_ratio DESC
    """, {'pid': product_id})

    # 投资范围
    scope = execute_single("""
        SELECT * FROM lh_dc_wealth_product_investment_scope
        WHERE product_id = :pid
    """, {'pid': product_id})

    # 前十大持仓（穿透后底层资产详情）
    top_holdings = execute_query("""
        SELECT asset_name, asset_type, proportion, issuer
        FROM lh_dc_wealth_asset_details
        WHERE product_id = :pid
        ORDER BY proportion DESC
        LIMIT 10
    """, {'pid': product_id})

    # 杠杆率
    leverage = execute_single("""
        SELECT leverage_ratio, report_date
        FROM lh_dc_wealth_leverage_ratio
        WHERE product_id = :pid
        ORDER BY report_date DESC LIMIT 1
    """, {'pid': product_id})

    return {
        'allocation': [{
            'type': r.get('asset_type', ''),
            'ratio': float(r.get('asset_ratio', 0)) if r.get('asset_ratio') else 0,
        } for r in (allocation or [])],
        'scope': scope,
        'top_holdings': [{
            'name': r.get('asset_name', ''),
            'type': r.get('asset_type', ''),
            'proportion': float(r.get('proportion', 0)) if r.get('proportion') else 0,
            'issuer': r.get('issuer', ''),
        } for r in (top_holdings or [])],
        'leverage': float(leverage.get('leverage_ratio', 0)) if leverage else None,
        'leverage_date': str(leverage.get('report_date', '')) if leverage else '',
    }

"""
产品数据服务（原型二、三）
提供产品搜索、详情、净值、业绩指标等数据
"""
from app.models.base import execute_query, execute_single, execute_scalar


def search_products(keyword: str):
    """按关键字搜索产品"""
    results = execute_query("""
        SELECT product_id, product_name, product_code, raising_type,
               product_status, is_net_worth_type, org_id
        FROM lh_dc_wealth_product
        WHERE valid = 1
          AND (product_name LIKE :kw OR product_code LIKE :kw OR product_id LIKE :kw)
        ORDER BY product_start_date DESC NULLS LAST
        LIMIT 20
    """, {'kw': f'%{keyword}%'})
    return results or []


def get_product_profile(product_id: str):
    """获取产品基本信息（360°档案 - 基本信息Tab）"""
    product = execute_single("""
        SELECT * FROM lh_dc_wealth_product
        WHERE product_id = :pid AND valid = 1
    """, {'pid': product_id})

    if not product:
        return None

    # 子产品列表
    sub_products = execute_query("""
        SELECT * FROM lh_dc_wealth_sub_product
        WHERE product_id = :pid AND valid = 1
        ORDER BY sub_id
    """, {'pid': product_id})

    # 关联机构
    orgs = execute_query("""
        SELECT o.org_name, o.org_abbreviation, o.org_type
        FROM lh_dc_wealth_product_org_relation r
        JOIN lh_dc_wealth_org o ON r.org_id = o.id
        WHERE r.product_id = :pid
    """, {'pid': product_id})

    # 申购规则（取第一个子产品）
    purchase = None
    if sub_products:
        sub_id = sub_products[0].get('sub_id')
        purchase = execute_single("""
            SELECT * FROM lh_dc_wealth_purchase
            WHERE sub_id = :sid
            LIMIT 1
        """, {'sid': sub_id})

    # 费率（取第一个子产品）
    commission = None
    if sub_products:
        sub_id = sub_products[0].get('sub_id')
        commission = execute_single("""
            SELECT * FROM lh_dc_wealth_commision_charge
            WHERE sub_id = :sid
            ORDER BY fee_date DESC LIMIT 1
        """, {'sid': sub_id})

    # 最新净值
    latest_nw = None
    if sub_products:
        sub_id = sub_products[0].get('sub_id')
        latest_nw = execute_single("""
            SELECT net_worth, accumulated_net, net_worth_date
            FROM lh_dc_wealth_product_net_worth_history
            WHERE sub_id = :sid AND valid = 1
            ORDER BY net_worth_date DESC LIMIT 1
        """, {'sid': sub_id})

    # 最新规模
    latest_scale = execute_single("""
        SELECT product_balance, report_date
        FROM lh_dc_wealth_product_amount_total
        WHERE product_id = :pid
        ORDER BY report_date DESC LIMIT 1
    """, {'pid': product_id})

    return {
        'product': product,
        'sub_products': sub_products or [],
        'orgs': orgs or [],
        'purchase': purchase,
        'commission': commission,
        'latest_nw': latest_nw,
        'latest_scale': latest_scale,
    }


def get_net_worth_history(product_id: str, period: str = '6m'):
    """获取产品净值走势数据"""
    period_map = {
        '1m': "AND net_worth_date >= CURRENT_DATE - INTERVAL '1 month'",
        '3m': "AND net_worth_date >= CURRENT_DATE - INTERVAL '3 months'",
        '6m': "AND net_worth_date >= CURRENT_DATE - INTERVAL '6 months'",
        '1y': "AND net_worth_date >= CURRENT_DATE - INTERVAL '1 year'",
        'all': '',
    }
    period_filter = period_map.get(period, period_map['6m'])

    # 先查子产品ID
    sub_ids = execute_query("""
        SELECT sub_id FROM lh_dc_wealth_sub_product
        WHERE product_id = :pid AND valid = 1
        LIMIT 5
    """, {'pid': product_id})

    if not sub_ids:
        return []

    # 使用第一个子产品获取净值
    sub_id = sub_ids[0]['sub_id']
    results = execute_query(f"""
        SELECT net_worth_date, net_worth, accumulated_net, yield_7d
        FROM lh_dc_wealth_product_net_worth_history
        WHERE sub_id = :sid AND valid = 1
          {period_filter}
        ORDER BY net_worth_date ASC
    """, {'sid': sub_id})

    return [{
        'date': str(r['net_worth_date']),
        'net_worth': float(r['net_worth']) if r['net_worth'] else None,
        'accumulated_net': float(r['accumulated_net']) if r['accumulated_net'] else None,
        'yield_7d': float(r['yield_7d']) if r['yield_7d'] else None,
    } for r in (results or [])]


def get_performance(product_id: str, period: str = '1y'):
    """获取产品业绩指标"""
    # 从子产品获取 sub_id
    sub_ids = execute_query("""
        SELECT sub_id FROM lh_dc_wealth_sub_product
        WHERE product_id = :pid AND valid = 1 LIMIT 1
    """, {'pid': product_id})

    if not sub_ids:
        return {'returns': [], 'drawdowns': [], 'sharpes': []}

    sub_id = sub_ids[0]['sub_id']

    # 从最新年份的分表获取数据
    results_2026 = execute_query("""
        SELECT calculate_date,
               seven_day_annualized_return,
               since_inception_annualized_return,
               seven_day_max_drawdown
        FROM lh_dc_wealth_max_drawdown_2026
        WHERE sub_id = :sid
        ORDER BY calculate_date DESC
        LIMIT 30
    """, {'sid': sub_id})

    return {
        'returns': [{
            'date': str(r.get('calculate_date', '')),
            'annualized_return': float(r.get('seven_day_annualized_return', 0) or 0),
            'since_inception': float(r.get('since_inception_annualized_return', 0) or 0),
            'max_drawdown': float(r.get('seven_day_max_drawdown', 0) or 0),
        } for r in (results_2026 or [])],
    }

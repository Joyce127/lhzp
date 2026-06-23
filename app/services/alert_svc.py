"""
风险事件预警服务（原型八）
回撤预警、破净预警、负收益预警、兑付风险预警
"""
from app.models.base import execute_query, execute_single


ALERT_RULES = {
    'drawdown': {
        'name': '回撤预警',
        'table': 'lh_dc_wealth_max_drawdown_2026',
        'column': 'month_max_drawdown',
        'threshold': -5,
        'compare': '<',
    },
    'below_net': {
        'name': '破净预警',
        'table': 'lh_dc_wealth_basic_info_table',
        'column': 'number_of_products_below_net',
        'threshold': 1,
        'compare': '>=',
    },
    'negative_yield': {
        'name': '负收益',
        'table': 'lh_dc_wealth_negative_yield_table',
        'column': None,
        'threshold': None,
        'compare': None,
    },
    'payment_risk': {
        'name': '兑付风险',
        'table': 'lh_dc_wealth_payment_history',
        'column': None,
        'threshold': None,
        'compare': None,
    },
}


def get_alert_list(status=None, alert_type=None, limit=20):
    """获取预警列表"""
    alerts = []

    # 回撤预警
    if not alert_type or alert_type == 'drawdown':
        drawdowns = execute_query("""
            SELECT DISTINCT ON (d.sub_id)
                   d.sub_id, d.month_max_drawdown, d.calculate_date,
                   sp.product_id,
                   p.product_name,
                   o.org_name
            FROM lh_dc_wealth_max_drawdown_2026 d
            JOIN lh_dc_wealth_sub_product sp ON d.sub_id = sp.sub_id
            JOIN lh_dc_wealth_product p ON sp.product_id = p.product_id
            JOIN lh_dc_wealth_org o ON p.org_id = o.id
            WHERE d.month_max_drawdown < -5
            ORDER BY d.sub_id, d.calculate_date DESC
            LIMIT :lim
        """, {'lim': limit})
        for r in (drawdowns or []):
            alerts.append({
                'type': 'drawdown',
                'type_name': '回撤预警',
                'product_name': r.get('product_name', '')[:50],
                'org_name': r.get('org_name', ''),
                'detail': f"近月最大回撤 {float(r.get('month_max_drawdown', 0)):.2f}%，超过-5%阈值",
                'date': str(r.get('calculate_date', '')),
                'status': 'pending',
            })

    # 破净预警（中邮理财破净产品）
    if not alert_type or alert_type == 'below_net':
        broken = execute_query("""
            SELECT statistics_date, issuer_name, number_of_products_below_net,
                   scale_of_products_below_net
            FROM lh_dc_wealth_basic_info_table
            WHERE number_of_products_below_net > 0
              AND issuer_name = '中邮理财'
              AND first_level_dimension = '全部'
            ORDER BY statistics_date DESC
            LIMIT 5
        """)
        for r in (broken or []):
            alerts.append({
                'type': 'below_net',
                'type_name': '破净预警',
                'product_name': f"中邮理财",
                'org_name': '中邮理财',
                'detail': f"破净产品 {r.get('number_of_products_below_net')} 只，规模 {float(r.get('scale_of_products_below_net', 0)):.0f}",
                'date': str(r.get('statistics_date', '')),
                'status': 'pending',
            })

    # 负收益
    if not alert_type or alert_type == 'negative_yield':
        neg = execute_query("""
            SELECT * FROM lh_dc_wealth_negative_yield_table
            ORDER BY statistics_date DESC
            LIMIT :lim
        """, {'lim': limit})
        for r in (neg or []):
            alerts.append({
                'type': 'negative_yield',
                'type_name': '负收益',
                'product_name': '见详情',
                'org_name': str(r.get('issuer_name', '')),
                'detail': f"负收益产品数量占比 {float(r.get('negative_yield_quantity_ratio', 0))*100 if r.get('negative_yield_quantity_ratio') else 0:.1f}%",
                'date': str(r.get('statistics_date', '')),
                'status': 'pending',
            })

    return alerts[:limit]

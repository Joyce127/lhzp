"""
产品健康度扫描服务（原型九）
僵尸产品识别、异动产品监控
"""
from app.models.base import execute_query, execute_scalar


def get_health_scan():
    """执行产品健康度扫描"""

    # 僵尸产品：连续3个月规模低于5000万
    zombies = execute_query("""
        WITH small_products AS (
            SELECT product_id, report_date, product_balance
            FROM lh_dc_wealth_product_amount_total
            WHERE product_balance < 50000000  -- 5000万
              AND report_date >= CURRENT_DATE - INTERVAL '3 months'
        ),
        zombie_ids AS (
            SELECT product_id, COUNT(*) as low_months
            FROM small_products
            GROUP BY product_id
            HAVING COUNT(*) >= 3
        )
        SELECT z.product_id, z.low_months,
               p.product_name, p.product_code,
               a.product_balance,
               a.report_date
        FROM zombie_ids z
        JOIN lh_dc_wealth_product p ON z.product_id = p.product_id
        LEFT JOIN LATERAL (
            SELECT product_balance, report_date
            FROM lh_dc_wealth_product_amount_total
            WHERE product_id = z.product_id
            ORDER BY report_date DESC LIMIT 1
        ) a ON true
        WHERE p.valid = 1
        ORDER BY a.product_balance ASC
        LIMIT 30
    """)

    # 异动产品：代码变更
    code_changes = execute_query("""
        SELECT c.*, p.product_name
        FROM lh_dc_wealth_code_change_history c
        JOIN lh_dc_wealth_product p ON c.product_id = p.product_id
        WHERE c.change_date >= CURRENT_DATE - INTERVAL '3 months'
        ORDER BY c.change_date DESC
        LIMIT 20
    """)

    # 投资经理变更
    manager_changes = execute_query("""
        SELECT p.product_name, o.org_name,
               m.full_name as manager_name
        FROM lh_dc_wealth_product_manager_relation r
        JOIN lh_dc_wealth_product p ON r.product_id = p.product_id
        JOIN lh_dc_wealth_inv_manager_basic_info m ON r.manager_id = m.manager_id
        JOIN lh_dc_wealth_org o ON p.org_id = o.id
        WHERE p.valid = 1
        LIMIT 30
    """)

    # 统计总数
    total_products = execute_scalar("""
        SELECT COUNT(DISTINCT product_id) FROM lh_dc_wealth_product WHERE valid = 1
    """)

    return {
        'total_products': total_products or 0,
        'zombie_count': len(zombies or []),
        'change_count': len(code_changes or []) + len(manager_changes or []),
        'warning_count': len(zombies or []),
        'healthy_count': (total_products or 0) - len(zombies or []),
        'zombies': [{
            'product_name': r.get('product_name', '')[:50] if r.get('product_name') else '',
            'product_code': r.get('product_code', ''),
            'balance': float(r.get('product_balance', 0)) if r.get('product_balance') else 0,
            'low_months': r.get('low_months', 0),
            'advice': '评估合并或清盘可能性' if r.get('low_months', 0) >= 4 else '持续观察',
        } for r in (zombies or [])],
        'code_changes': [{
            'product_name': r.get('product_name', '')[:50] if r.get('product_name') else '',
            'change_date': str(r.get('change_date', '')),
            'change_type': '产品代码变更',
            'change_detail': str(r.get('new_code', '')) if r.get('new_code') else '代码变更',
        } for r in (code_changes or [])],
        'manager_changes': [{
            'product_name': r.get('product_name', '')[:50] if r.get('product_name') else '',
            'org_name': r.get('org_name', ''),
            'manager_name': r.get('manager_name', ''),
            'change_type': '投资经理',
        } for r in (manager_changes or [])[:10]],
    }

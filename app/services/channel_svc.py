"""
渠道与区域分析服务（原型六）
渠道效能评估、区域销售分析（性能优化版）
"""
from app.models.base import execute_query, execute_single, execute_scalar


def get_channel_list():
    """获取代销机构列表"""
    results = execute_query("""
        SELECT DISTINCT o.id as org_id, o.org_name, o.org_abbreviation
        FROM lh_dc_wealth_affiliate_agencies a
        JOIN lh_dc_wealth_org o ON a.org_id = o.id
        WHERE a.valid = 1
        LIMIT 50
    """)
    return results or []


def get_channel_overview(org_id: int):
    """获取单个渠道的概览数据"""
    org = execute_single("""
        SELECT id, org_name, org_abbreviation, org_type, bank_classification
        FROM lh_dc_wealth_org WHERE id = :oid
    """, {'oid': org_id})
    if not org:
        return None

    # 代销产品数
    product_count = execute_scalar("""
        SELECT COUNT(DISTINCT a.sub_id)
        FROM lh_dc_wealth_affiliate_agencies a
        WHERE a.org_id = :oid AND a.valid = 1
    """, {'oid': org_id})

    # 代销产品列表（通过 sub_id → sub_product → product）
    products = execute_query("""
        SELECT DISTINCT p.product_id, p.product_name, p.product_code,
               sp.sub_id
        FROM lh_dc_wealth_affiliate_agencies a
        JOIN lh_dc_wealth_sub_product sp ON a.sub_id = sp.sub_id
        JOIN lh_dc_wealth_product p ON sp.product_id = p.product_id
        WHERE a.org_id = :oid AND a.valid = 1 AND p.valid = 1
        LIMIT 20
    """, {'oid': org_id})

    # 按产品类型分类统计
    type_dist = execute_query("""
        SELECT COALESCE(cl.lh_secondary_classification2, '未分类') as category,
               COUNT(DISTINCT a.sub_id) as cnt
        FROM lh_dc_wealth_affiliate_agencies a
        JOIN lh_dc_wealth_sub_product sp ON a.sub_id = sp.sub_id
        JOIN lh_dc_wealth_product p ON sp.product_id = p.product_id
        LEFT JOIN lh_cal_wealth_classification cl ON p.product_id = cl.product_id
        WHERE a.org_id = :oid AND a.valid = 1
        GROUP BY cl.lh_secondary_classification2
        ORDER BY cnt DESC
    """, {'oid': org_id})

    return {
        'org': org,
        'product_count': product_count or 0,
        'products': [{
            'product_id': r.get('product_id', ''),
            'product_name': (r.get('product_name', '') or '')[:50],
            'product_code': r.get('product_code', ''),
        } for r in (products or [])],
        'type_dist': [{
            'category': r.get('category', '未分类'),
            'count': r.get('cnt', 0),
        } for r in (type_dist or [])],
    }


def get_region_data():
    """获取区域分布数据"""
    results = execute_query("""
        SELECT province_name,
               COUNT(*) as area_count
        FROM lh_wealth_area
        WHERE admin_level_code = '1' AND valid = 1
        GROUP BY province_name
        ORDER BY area_count
        LIMIT 34
    """)
    return [{
        'name': r.get('province_name', ''),
        'count': r.get('area_count', 0),
    } for r in (results or [])]

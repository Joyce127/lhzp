"""
驾驶舱数据服务（原型一）
提供公司经营驾驶舱的KPI、规模结构、风险指标、预警摘要等数据
"""
from app.models.base import execute_query, execute_scalar, execute_single

# 中邮理财机构名称匹配
OUR_ISSUER = '中邮理财'


def get_overview_kpi():
    """获取驾驶舱顶部KPI卡片数据：总管理规模、存续产品数、整体破净情况"""
    # 总管理规模（中邮理财最新总规模）
    aum = execute_scalar("""
        SELECT SUM(product_balance)
        FROM lh_dc_wealth_product_amount_total
        WHERE report_date = (SELECT MAX(report_date) FROM lh_dc_wealth_product_amount_total)
    """)

    # 存续产品数
    product_count = execute_scalar("""
        SELECT COUNT(DISTINCT product_id)
        FROM lh_dc_wealth_product
        WHERE valid = 1 AND product_status = 1
    """)

    # 整体破净情况（中邮理财汇总 - dim1='全部' dim2='全部'）
    negative_info = execute_single("""
        SELECT statistics_date, number_of_products_below_net, scale_of_products_below_net,
               proportion_of_products_below_net, product_quantity, product_scale
        FROM lh_dc_wealth_basic_info_table
        WHERE issuer_name = :issuer
          AND first_level_dimension = '全部' AND second_level_dimension = '全部'
        ORDER BY statistics_date DESC LIMIT 1
    """, {'issuer': OUR_ISSUER})

    # 加权平均收益率（中邮理财全部，成立以来）
    avg_yield = execute_single("""
        SELECT since_inception_weighted_avg_annual_yield
        FROM lh_dc_wealth_yield_weighted_average_table
        WHERE issuer_name = :issuer
          AND first_level_dimension = '全部' AND second_level_dimension = '全部'
        ORDER BY statistics_date DESC LIMIT 1
    """, {'issuer': OUR_ISSUER})

    broken_count = negative_info.get('number_of_products_below_net', 0) if negative_info else 0
    broken_scale = float(negative_info.get('scale_of_products_below_net', 0)) if negative_info else 0
    total_scale = float(negative_info.get('product_scale', 0)) if negative_info else 1

    return {
        'aum': float(aum) if aum else 0,
        'aum_display': _format_amount(aum),
        'product_count': product_count or 0,
        'broken_net_count': broken_count,
        'broken_net_scale': broken_scale,
        'broken_net_rate': round(broken_scale / total_scale * 100, 2) if total_scale > 0 else 0,
        'avg_yield': float(avg_yield.get('since_inception_weighted_avg_annual_yield', 0) or 0) if avg_yield else 0,
        'update_date': str(negative_info.get('statistics_date', '')) if negative_info else '',
    }


def get_scale_structure():
    """获取规模结构数据（按投资性质分类）"""
    results = execute_query("""
        SELECT b.second_level_dimension as category_name,
               SUM(b.product_scale) as total_scale,
               SUM(b.product_quantity) as product_count
        FROM lh_dc_wealth_basic_info_table b
        WHERE b.issuer_name = :issuer
          AND b.first_level_dimension = '投资性质'
          AND b.statistics_date = (SELECT MAX(statistics_date) FROM lh_dc_wealth_basic_info_table
                                    WHERE issuer_name = :issuer2)
        GROUP BY b.second_level_dimension
        ORDER BY total_scale DESC
    """, {'issuer': OUR_ISSUER, 'issuer2': OUR_ISSUER})

    return [
        {
            'name': r.get('category_name', '未分类'),
            'value': float(r.get('total_scale', 0)),
            'count': int(r.get('product_count', 0)),
        }
        for r in (results or []) if float(r.get('total_scale', 0)) > 0
    ]


def get_risk_indicators():
    """获取核心风险收益指标（中邮理财合计）"""
    params = {'issuer': OUR_ISSUER}

    yield_data = execute_single("""
        SELECT one_month_weighted_avg_annual_yield,
               six_months_weighted_avg_annual_yield,
               one_year_weighted_avg_annual_yield,
               since_inception_weighted_avg_annual_yield
        FROM lh_dc_wealth_yield_weighted_average_table
        WHERE issuer_name = :issuer
          AND first_level_dimension = '全部' AND second_level_dimension = '全部'
        ORDER BY statistics_date DESC LIMIT 1
    """, params)

    drawdown_data = execute_single("""
        SELECT max_drawdown_one_month_simple_average,
               max_drawdown_six_months_simple_average,
               max_drawdown_one_year_simple_average
        FROM lh_dc_wealth_max_drawdown_average_table
        WHERE issuer_name = :issuer
          AND first_level_dimension = '全部' AND second_level_dimension = '全部'
        ORDER BY statistics_date DESC LIMIT 1
    """, params)

    sharpe_data = execute_single("""
        SELECT one_month_sharpe_ratio_weighted_average,
               six_months_sharpe_ratio_weighted_average,
               one_year_sharpe_ratio_weighted_average
        FROM lh_dc_wealth_sharpe_weighted_average_table
        WHERE issuer_name = :issuer
          AND first_level_dimension = '全部' AND second_level_dimension = '全部'
        ORDER BY statistics_date DESC LIMIT 1
    """, params)

    compliance_data = execute_single("""
        SELECT one_month_quantity_ratio
        FROM lh_dc_wealth_compliance_beyond_lower_average_table
        WHERE issuer_name = :issuer
          AND first_level_dimension = '全部' AND second_level_dimension = '全部'
        ORDER BY statistics_date DESC LIMIT 1
    """, params)

    return {
        'yield_1m': float(yield_data.get('one_month_weighted_avg_annual_yield', 0) or 0) if yield_data else 0,
        'yield_6m': float(yield_data.get('six_months_weighted_avg_annual_yield', 0) or 0) if yield_data else 0,
        'yield_1y': float(yield_data.get('one_year_weighted_avg_annual_yield', 0) or 0) if yield_data else 0,
        'yield_si': float(yield_data.get('since_inception_weighted_avg_annual_yield', 0) or 0) if yield_data else 0,
        'drawdown_1m': float(drawdown_data.get('max_drawdown_one_month_simple_average', 0) or 0) if drawdown_data else 0,
        'drawdown_6m': float(drawdown_data.get('max_drawdown_six_months_simple_average', 0) or 0) if drawdown_data else 0,
        'drawdown_1y': float(drawdown_data.get('max_drawdown_one_year_simple_average', 0) or 0) if drawdown_data else 0,
        'sharpe_1m': float(sharpe_data.get('one_month_sharpe_ratio_weighted_average', 0) or 0) if sharpe_data else 0,
        'sharpe_6m': float(sharpe_data.get('six_months_sharpe_ratio_weighted_average', 0) or 0) if sharpe_data else 0,
        'sharpe_1y': float(sharpe_data.get('one_year_sharpe_ratio_weighted_average', 0) or 0) if sharpe_data else 0,
        'compliance_ratio': float(compliance_data.get('one_month_quantity_ratio', 0) or 0) if compliance_data else 0,
    }


def get_alert_summary():
    """获取预警摘要列表（回撤较大的产品）"""
    results = execute_query("""
        SELECT '回撤预警' as alert_type,
               (SELECT product_name FROM lh_dc_wealth_product p
                JOIN lh_dc_wealth_sub_product s ON p.product_id = s.product_id
                WHERE s.sub_id = d.sub_id AND p.valid = 1 LIMIT 1) as product_name,
               ROUND(d.seven_day_max_drawdown::numeric, 2)::text || '%' as alert_detail
        FROM lh_dc_wealth_max_drawdown_2026 d
        WHERE d.seven_day_max_drawdown < -5
        ORDER BY d.seven_day_max_drawdown ASC
        LIMIT 5
    """)
    return results or []


def _format_amount(value):
    """格式化金额显示"""
    if not value:
        return '暂无数据'
    value = float(value)
    if value >= 1e8:
        return f'{value/1e8:.2f} 亿'
    elif value >= 1e4:
        return f'{value/1e4:.2f} 万'
    else:
        return f'{value:.2f} 元'

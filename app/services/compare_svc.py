"""
产品PK对比服务（原型七）
多产品维度对比 + 自动判断优劣（批量查询优化版）
"""
from app.models.base import execute_query, execute_single


def compare_products(product_ids: list):
    """对比多个产品的指标"""
    if not product_ids or len(product_ids) < 2:
        return None

    results = []
    for pid in product_ids[:3]:
        product = execute_single("""
            SELECT product_id, product_name, product_code
            FROM lh_dc_wealth_product
            WHERE product_id = :pid AND valid = 1
        """, {'pid': pid})
        if not product:
            continue

        sub = execute_single("""
            SELECT sub_id FROM lh_dc_wealth_sub_product
            WHERE product_id = :pid AND valid = 1 LIMIT 1
        """, {'pid': pid})
        if not sub:
            continue

        sid = sub['sub_id']

        # 批量查询所有指标 — 每个表只查一次
        ret = _batch_query(sid, 'lh_dc_wealth_annualized_compound_return_2026',
                           ['month_annualized_compound_return', 'quarter_annualized_compound_return',
                            'one_year_annualized_compound_return'])
        drawdown = _batch_query(sid, 'lh_dc_wealth_max_drawdown_2026',
                               ['month_max_drawdown', 'quarter_max_drawdown', 'one_year_max_drawdown'])
        sharpe = _batch_query(sid, 'lh_dc_wealth_sharpe_seven_day_basis_2026',
                             ['month_sharpe', 'one_year_sharpe'])
        calmar = _batch_query(sid, 'lh_dc_wealth_calmar1_2026',
                             ['month_calmar', 'half_calmar'])

        dimensions = [
            {'label': '年化收益率(近1月)', 'value': ret.get('month_annualized_compound_return'), 'direction': 'high'},
            {'label': '年化收益率(近3月)', 'value': ret.get('quarter_annualized_compound_return'), 'direction': 'high'},
            {'label': '年化收益率(近1年)', 'value': ret.get('one_year_annualized_compound_return'), 'direction': 'high'},
            {'label': '最大回撤(近1月)', 'value': drawdown.get('month_max_drawdown'), 'direction': 'low'},
            {'label': '最大回撤(近3月)', 'value': drawdown.get('quarter_max_drawdown'), 'direction': 'low'},
            {'label': '最大回撤(近1年)', 'value': drawdown.get('one_year_max_drawdown'), 'direction': 'low'},
            {'label': '夏普比率(近1月)', 'value': sharpe.get('month_sharpe'), 'direction': 'high'},
            {'label': '夏普比率(近1年)', 'value': sharpe.get('one_year_sharpe'), 'direction': 'high'},
            {'label': '卡玛比率(近1月)', 'value': calmar.get('month_calmar'), 'direction': 'high'},
            {'label': '卡玛比率(近6月)', 'value': calmar.get('half_calmar'), 'direction': 'high'},
        ]

        # 费率
        fee = execute_single("""
            SELECT sales_fee, custody_fee, fixed_management_fee
            FROM lh_dc_wealth_commision_charge
            WHERE sub_id = :sid ORDER BY fee_date DESC LIMIT 1
        """, {'sid': sid})

        # 机构
        org = execute_single("""
            SELECT o.org_name FROM lh_dc_wealth_org o
            JOIN lh_dc_wealth_product p ON o.id = p.org_id
            WHERE p.product_id = :pid
        """, {'pid': pid})

        results.append({
            'product_id': pid,
            'product_name': (product.get('product_name', '') or '')[:50],
            'product_code': product.get('product_code', ''),
            'org_name': org.get('org_name', '') if org else '',
            'dimensions': dimensions,
            'fee': {
                'sales_fee': float(fee.get('sales_fee', 0)) if fee and fee.get('sales_fee') else None,
                'custody_fee': float(fee.get('custody_fee', 0)) if fee and fee.get('custody_fee') else None,
                'management_fee': float(fee.get('fixed_management_fee', 0)) if fee and fee.get('fixed_management_fee') else None,
            } if fee else None,
        })

    if len(results) >= 2:
        _mark_winners(results)

    return results if results else None


def _batch_query(sub_id, table, columns):
    """批量查询一个产品的多个指标列 — 一次查询"""
    cols = ', '.join(columns)
    result = execute_single(f"""
        SELECT {cols}
        FROM {table}
        WHERE sub_id = :sid
        ORDER BY calculate_date DESC LIMIT 1
    """, {'sid': sub_id})
    if not result:
        return {}
    return {col: float(result[col]) if result.get(col) is not None else None for col in columns}


def _mark_winners(results):
    """自动标记每个维度的胜者"""
    if len(results) < 2:
        return

    dim_count = len(results[0]['dimensions'])
    for di in range(dim_count):
        values = [(ri, r['dimensions'][di].get('value')) for ri, r in enumerate(results)]
        valid = [(ri, v) for ri, v in values if v is not None]
        if len(valid) < 2:
            continue

        direction = results[0]['dimensions'][di]['direction']
        if direction == 'high':
            winner = max(valid, key=lambda x: x[1])
        else:
            winner = min(valid, key=lambda x: x[1])

        others = [v for ri, v in valid if ri != winner[0]]
        if direction == 'high' and others and winner[1] > max(others):
            results[winner[0]]['dimensions'][di]['winner'] = True
        elif direction == 'low' and others and winner[1] < min(others):
            results[winner[0]]['dimensions'][di]['winner'] = True

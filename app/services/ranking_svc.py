"""
排行榜数据服务（原型三）
提供多维度产品排名：收益率、最大回撤、夏普比率、卡玛比率
"""
from app.models.base import execute_query

PERIOD_MAP = {
    '1m': ('month', 'month'),
    '3m': ('quarter', 'quarter'),
    '6m': ('half', 'half'),
    '1y': ('one_year', 'one_year'),
}

RANK_TYPE_MAP = {
    'return': {
        'table': 'lh_dc_wealth_annualized_compound_return_2026',
        'column': '{}_annualized_compound_return',
        'label': '年化收益率',
    },
    'drawdown': {
        'table': 'lh_dc_wealth_max_drawdown_2026',
        'column': '{}_max_drawdown',
        'label': '最大回撤',
    },
    'sharpe': {
        'table': 'lh_dc_wealth_sharpe_seven_day_basis_2026',
        'column': '{}_sharpe',
        'label': '夏普比率',
    },
    'calmar': {
        'table': 'lh_dc_wealth_calmar1_2026',
        'column': '{}_calmar',
        'label': '卡玛比率',
    },
}

OUR_ISSUER = '中邮理财'


def get_ranking(rank_type='return', period='3m', category=None, issuer=None, page=1, page_size=20):
    """获取产品排行榜"""
    if rank_type not in RANK_TYPE_MAP:
        rank_type = 'return'
    if period not in PERIOD_MAP:
        period = '3m'

    config = RANK_TYPE_MAP[rank_type]
    period_key, _ = PERIOD_MAP[period]
    col = config['column'].format(period_key)

    # 排序方向：收益率和夏普/卡玛是降序，回撤是升序（回撤越小越好）
    order = 'DESC'
    if rank_type == 'drawdown':
        order = 'ASC'

    # 构建查询 - 两步走：先取最新日期，再筛数据
    conditions = []
    params = {}

    # Step 1: Get latest calculate_date globally for filtering
    latest_date_sql = f"SELECT MAX(calculate_date) FROM {config['table']}"

    # Step 2: Query with date filter (much faster than DISTINCT ON)
    subquery = f"""
        SELECT
            l.sub_id, l.{col} as metric_value, l.calculate_date,
            sp.product_id,
            p.product_name, p.product_code,
            o.org_name, o.org_abbreviation,
            cl.lh_secondary_classification2
        FROM {config['table']} l
        JOIN lh_dc_wealth_sub_product sp ON l.sub_id = sp.sub_id AND sp.valid = 1
        JOIN lh_dc_wealth_product p ON sp.product_id = p.product_id AND p.valid = 1
        JOIN lh_dc_wealth_org o ON p.org_id = o.id
        LEFT JOIN lh_cal_wealth_classification cl ON p.product_id = cl.product_id
        WHERE l.calculate_date = ({latest_date_sql})
          AND l.{col} IS NOT NULL
    """

    if category:
        conditions.append("cl.lh_secondary_classification2 = :cat")
        params['cat'] = category
    if issuer:
        conditions.append("(o.org_name LIKE :issuer OR o.org_abbreviation LIKE :issuer2)")
        params['issuer'] = f'%{issuer}%'
        params['issuer2'] = f'%{issuer}%'

    if conditions:
        subquery += ' AND ' + ' AND '.join(conditions)

    # 排序 + 分页
    offset = (page - 1) * page_size
    main_query = f"""
        SELECT * FROM (
            {subquery}
        ) ranked
        ORDER BY metric_value {order}
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = page_size
    params['offset'] = offset

    results = execute_query(main_query, params)

    return [{
        'sub_id': r.get('sub_id'),
        'product_id': r.get('product_id'),
        'product_name': r.get('product_name', '')[:50] if r.get('product_name') else '',
        'product_code': r.get('product_code', ''),
        'org_name': r.get('org_name', ''),
        'org_abbreviation': r.get('org_abbreviation', ''),
        'category1': r.get('lh_secondary_classification1', ''),
        'category2': r.get('lh_secondary_classification2', ''),
        'metric_value': float(r.get('metric_value', 0)) if r.get('metric_value') else 0,
        'calculate_date': str(r.get('calculate_date', '')),
        'is_ours': r.get('org_name', '') == OUR_ISSUER,
    } for r in (results or [])]


def get_ranking_categories():
    """获取可选的产品分类列表"""
    results = execute_query("""
        SELECT DISTINCT lh_secondary_classification1, lh_secondary_classification2
        FROM lh_cal_wealth_classification
        WHERE valid = 1
        ORDER BY lh_secondary_classification1, lh_secondary_classification2
    """)
    cats = {}
    for r in (results or []):
        c1 = r.get('lh_secondary_classification1', '') or '未分类'
        c2 = r.get('lh_secondary_classification2', '') or '未分类'
        if c1 not in cats:
            cats[c1] = []
        cats[c1].append(c2)
    return cats


def get_issuer_list():
    """获取发行机构列表"""
    results = execute_query("""
        SELECT DISTINCT o.org_name, o.org_abbreviation
        FROM lh_dc_wealth_org o
        JOIN lh_dc_wealth_product p ON o.id = p.org_id
        WHERE p.valid = 1
        ORDER BY o.org_name
        LIMIT 100
    """)
    return [{'name': r.get('org_name', ''), 'abbr': r.get('org_abbreviation', '')} for r in (results or [])]

/**
 * 联合智评数据应用平台 - 通用JS
 */

// 金额格式化
function formatAmount(value) {
    if (!value) return '--';
    value = parseFloat(value);
    if (value >= 1e8) return (value / 1e8).toFixed(2) + ' 亿';
    if (value >= 1e4) return (value / 1e4).toFixed(2) + ' 万';
    return value.toFixed(2) + ' 元';
}

// 百分比格式化
function formatPercent(value) {
    if (value === null || value === undefined) return '--';
    return parseFloat(value).toFixed(2) + '%';
}

// AJAX 通用请求
function apiGet(url) {
    return fetch(url)
        .then(res => {
            if (res.status === 401) {
                window.location.href = '/login';
                throw new Error('未登录');
            }
            return res.json();
        });
}

// ECharts 通用初始化
function initChart(domId) {
    const dom = document.getElementById(domId);
    if (!dom) return null;
    // 如果已有实例，先销毁
    if (dom._echart_instance) {
        dom._echart_instance.dispose();
    }
    const chart = echarts.init(dom);
    dom._echart_instance = chart;
    return chart;
}

// 响应式图表
window.addEventListener('resize', function() {
    document.querySelectorAll('[id^="chart"]').forEach(el => {
        if (el._echart_instance) {
            el._echart_instance.resize();
        }
    });
});

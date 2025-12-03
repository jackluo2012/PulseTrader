-- 财务数据表
CREATE TABLE IF NOT EXISTS pulse_trader.financial_data (
    -- 主键标识
    symbol String,
    -- 股票代码
    report_date Date,
    -- 报告期
    report_type String,
    -- 报告类型 (年报/半年报/季报)
    -- 盈利能力指标
    total_revenue Decimal64(2),
    -- 营业总收入
    net_profit Decimal64(2),
    -- 净利润
    gross_profit Decimal64(2),
    -- 毛利润
    operating_profit Decimal64(2),
    -- 营业利润
    eps Decimal32(4),
    -- 每股收益
    roe Decimal32(4),
    -- 净资产收益率
    roa Decimal32(4),
    -- 总资产收益率
    -- 偿债能力指标
    total_assets Decimal64(2),
    -- 总资产
    total_liabilities Decimal64(2),
    -- 总负债
    current_assets Decimal64(2),
    -- 流动资产
    current_liabilities Decimal64(2),
    -- 流动负债
    debt_ratio Decimal32(4),
    -- 资产负债率
    -- 运营能力指标
    inventory_turnover Decimal32(4),
    -- 存货周转率
    receivable_turnover Decimal32(4),
    -- 应收账款周转率
    total_asset_turnover Decimal32(4),
    -- 总资产周转率
    -- 成长能力指标
    revenue_growth Decimal32(4),
    -- 营收增长率
    profit_growth Decimal32(4),
    -- 利润增长率
    -- 现金流量指标
    operating_cash_flow Decimal64(2),
    -- 经营现金流
    free_cash_flow Decimal64(2),
    -- 自由现金流
    -- 其他财务数据
    shares_outstanding Decimal64(2),
    -- 总股本
    book_value_per_share Decimal32(4),
    -- 每股净资产
    -- 元数据
    data_source String DEFAULT 'company_report',
    -- 数据源
    published_at Date,
    -- 发布日期
    created_at DateTime DEFAULT now(),
    -- 创建时间
    updated_at DateTime DEFAULT now() -- 更新时间
) ENGINE = ReplacingMergeTree(updated_at) PARTITION BY (toYYYYMM(report_date), report_type)
ORDER BY (symbol, report_date, report_type);

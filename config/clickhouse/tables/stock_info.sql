CREATE TABLE IF NOT EXISTS pulse_trader.stock_info (
    -- 主键和基础信息
    symbol String,
    -- 股票代码 (6位数字)
    stock_name String,
    -- 股票名称
    short_name Nullable(String),
    -- 股票简称
    market String,
    -- 市场代码 (SH/SZ)
    exchange String,
    -- 交易所名称
    listing_date Date,
    -- 上市日期
    delisting_date Nullable(Date),
    -- 退市日期
    -- 分类信息
    industry String,
    -- 所属行业
    sector String,
    -- 所属板块
    concept_tags Array(String),
    -- 概念标签
    is_st UInt8 DEFAULT 0,
    -- 是否ST股
    is_star UInt8 DEFAULT 0,
    -- 是否科创板
    -- 状态信息
    is_active UInt8 DEFAULT 1,
    -- 是否活跃交易
    is_suspended UInt8 DEFAULT 0,
    -- 是否停牌
    trade_status String DEFAULT '正常',
    -- 交易状态
    -- 公司信息
    total_shares Nullable(Decimal64(2)),
    -- 总股本
    float_shares Nullable(Decimal64(2)),
    -- 流通股本
    market_cap Nullable(Decimal64(2)),
    -- 总市值
    pe_ratio Nullable(Decimal32(4)),
    -- 市盈率
    pb_ratio Nullable(Decimal32(4)),
    -- 市净率
    -- 元数据
    data_source String DEFAULT 'akshare',
    -- 数据源
    created_at DateTime DEFAULT now(),
    -- 创建时间
    updated_at DateTime DEFAULT now(),
    -- 更新时间
    version UInt16 DEFAULT 1 -- 版本号
) ENGINE = ReplacingMergeTree(updated_at, version) PARTITION BY toYYYYMM(updated_at)
ORDER BY (symbol, updated_at) TTL updated_at + toIntervalDay(365) DELETE;

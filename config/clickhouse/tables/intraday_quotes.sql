-- 分钟级行情数据表
CREATE TABLE IF NOT EXISTS pulse_trader.intraday_quotes (
    -- 主键和时间标识
    symbol String,
    -- 股票代码
    datetime DateTime,
    -- 时间戳（精确到分钟）
    date Date,
    -- 日期（从datetime提取）
    time UInt32,
    -- 时间（HHMM格式）
    -- OHLCV价格数据
    open_price Decimal32(4),
    -- 开盘价
    high_price Decimal32(4),
    -- 最高价
    low_price Decimal32(4),
    -- 最低价
    close_price Decimal32(4),
    -- 收盘价
    volume UInt64,
    -- 成交量
    amount Decimal64(2),
    -- 成交额
    -- 市场微结构数据
    bid_price Nullable(Decimal32(4)),
    -- 买一价
    ask_price Nullable(Decimal32(4)),
    -- 卖一价
    bid_volume Nullable(UInt64),
    -- 买一量
    ask_volume Nullable(UInt64),
    -- 卖一量
    -- 实时指标
    vwap Decimal32(4),
    -- 成交量加权平均价
    price_position Decimal32(4),
    -- 价格位置（高低价相对位置）
    body_size Decimal32(4),
    -- K线实体大小
    -- 数据来源和质量
    data_source String DEFAULT 'realtime',
    -- 数据源类型
    data_delay UInt16 DEFAULT 0,
    -- 数据延迟(毫秒)
    collected_at DateTime DEFAULT now(),
    -- 数据采集时间
    -- 数据完整性标记
    is_complete UInt8 DEFAULT 1,
    -- 数据是否完整
    quality_score UInt8 DEFAULT 100 -- 数据质量评分
) ENGINE = MergeTree() PARTITION BY (toYYYYMMDD(datetime), toHour(datetime)) -- 按日期和小时分区
ORDER BY (symbol, datetime) -- 按股票和时间排序
    TTL datetime + toIntervalDay(90) DELETE;
-- 3个月后自动删除

-- 创建物化视图用于实时统计
CREATE MATERIALIZED VIEW IF NOT EXISTS pulse_trader.intraday_stats ENGINE = SummingMergeTree() PARTITION BY toYYYYMMDD(datetime)
ORDER BY (symbol, toStartOfHour(datetime)) AS
SELECT
    symbol,
    toStartOfHour(datetime) as hour_time,
    sum(volume) as total_volume,
    sum(amount) as total_amount,
    avg(close_price) as avg_price,
    min(low_price) as min_price,
    max(high_price) as max_price
FROM pulse_trader.intraday_quotes
GROUP BY symbol, hour_time;

CREATE TABLE IF NOT EXISTS pulse_trader.daily_quotes (
    -- 主键和标识
    symbol String,
    -- 股票代码
    market String,
    -- 市场代码 (SH/SZ)
    date Date,
    -- 交易日期
    -- OHLCV价格数据
    open_price Decimal32(4),
    -- 开盘价 (保留4位小数)
    high_price Decimal32(4),
    -- 最高价
    low_price Decimal32(4),
    -- 最低价
    close_price Decimal32(4),
    -- 收盘价
    volume UInt64,
    -- 成交量 (股)
    amount Decimal64(2),
    -- 成交额 (元)
    -- 价格变动信息
    change_amount Decimal32(4),
    -- 涨跌额
    change_percent Decimal32(4),
    -- 涨跌幅
    amplitude Decimal32(4),
    -- 振幅
    turnover_rate Decimal32(4),
    -- 换手率
    -- 技术指标字段
    ma5 Decimal32(4),
    -- 5日均线
    ma10 Decimal32(4),
    -- 10日均线
    ma20 Decimal32(4),
    -- 20日均线
    ma60 Decimal32(4),
    -- 60日均线
    ema12 Decimal32(4),
    -- 12日指数均线
    ema26 Decimal32(4),
    -- 26日指数均线
    rsi Decimal32(4),
    -- RSI指标
    -- 布林带指标
    bb_upper Decimal32(4),
    -- 布林带上轨
    bb_middle Decimal32(4),
    -- 布林带中轨
    bb_lower Decimal32(4),
    -- 布林带下轨
    bb_width Decimal32(4),
    -- 布林带宽度
    bb_position Decimal32(4),
    -- 价格在布林带中的位置
    -- MACD指标
    macd Decimal32(6),
    -- MACD DIF线
    macd_signal Decimal32(6),
    -- MACD信号线
    macd_histogram Decimal32(6),
    -- MACD柱状图
    -- 成交量指标
    volume_ma5 UInt64,
    -- 5日成交量均线
    volume_ratio Decimal32(4),
    -- 量比
    -- 其他技术指标
    kdj_k Decimal32(4),
    -- KDJ K值
    kdj_d Decimal32(4),
    -- KDJ D值
    kdj_j Decimal32(4),
    -- KDJ J值
    -- 基本面数据
    pe_ratio Decimal32(4),
    -- 市盈率
    pb_ratio Decimal32(4),
    -- 市净率
    -- 元数据
    data_source String DEFAULT 'akshare',
    -- 数据源
    collected_at DateTime DEFAULT now(),
    -- 数据采集时间
    updated_at DateTime DEFAULT now(),
    -- 数据更新时间
    batch_id String,
    -- 批次ID
    -- 数据质量标记
    data_quality_score UInt8 DEFAULT 100,
    -- 数据质量评分(0-100)
    is_holiday UInt8 DEFAULT 0,
    -- 是否为节假日
    is_trading_day UInt8 DEFAULT 1 -- 是否为交易日
) ENGINE = ReplacingMergeTree(updated_at) PARTITION BY (toYYYYMM(date), market) -- 按年份和市场分区
ORDER BY (symbol, date) -- 按股票代码和日期排序
    SETTINGS index_granularity = 8192;
-- 索引粒度

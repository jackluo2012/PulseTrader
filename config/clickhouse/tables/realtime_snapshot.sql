-- 实时行情快照表
CREATE TABLE IF NOT EXISTS pulse_trader.realtime_snapshot (
    -- 主键
    symbol String,
    -- 股票代码
    -- 最新价格信息
    current_price Decimal32(4),
    -- 最新价
    open_price Decimal32(4),
    -- 今开
    high_price Decimal32(4),
    -- 今高
    low_price Decimal32(4),
    -- 今低
    prev_close Decimal32(4),
    -- 昨收
    -- 涨跌信息
    change_amount Decimal32(4),
    -- 涨跌额
    change_percent Decimal32(4),
    -- 涨跌幅
    amplitude Decimal32(4),
    -- 振幅
    -- 成交信息
    volume UInt64,
    -- 成交量
    amount Decimal64(2),
    -- 成交额
    turnover_rate Decimal32(4),
    -- 换手率
    volume_ratio Decimal32(4),
    -- 量比
    -- 买卖盘数据
    bid_price Array(Decimal32(4)),
    -- 买盘价格（买一到买五）
    bid_volume Array(UInt64),
    -- 买盘数量
    ask_price Array(Decimal32(4)),
    -- 卖盘价格
    ask_volume Array(UInt64),
    -- 卖盘数量
    -- 市场深度
    total_bid_volume UInt64,
    -- 总买盘量
    total_ask_volume UInt64,
    -- 总卖盘量
    bid_ask_spread Decimal32(4),
    -- 买卖价差
    -- 基本面数据
    market_cap Decimal64(2),
    -- 总市值
    circulating_capital Decimal64(2),
    -- 流通市值
    pe_ratio Decimal32(4),
    -- 市盈率
    -- 技术指标
    ma5 Decimal32(4),
    ma10 Decimal32(4),
    ma20 Decimal32(4),
    ma60 Decimal32(4),
    -- 更新时间
    updated_at DateTime DEFAULT now(),
    -- 最后更新时间
    data_source String DEFAULT 'realtime',
    -- 数据源
    -- 状态标记
    is_trading UInt8 DEFAULT 1,
    -- 是否交易中
    is_suspended UInt8 DEFAULT 0,
    -- 是否停牌
    update_count UInt32 DEFAULT 1 -- 更新次数
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY symbol SETTINGS index_granularity = 1;

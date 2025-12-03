CREATE TABLE IF NOT EXISTS pulse_trader.trading_calendar (
    -- 主键
    date Date,
    -- 日期
    -- 交易信息
    is_trading_day UInt8 DEFAULT 1,
    -- 是否交易日
    market String,
    -- 市场代码
    -- 节假日信息
    is_holiday UInt8 DEFAULT 0,
    -- 是否节假日
    holiday_name Nullable(String),
    -- 节假日名称
    -- 特殊交易日
    is_special_trading_day UInt8 DEFAULT 0,
    -- 是否特殊交易日
    special_day_type Nullable(String),
    -- 特殊交易日类型
    -- 交易时间
    trading_start_time String DEFAULT '09:30',
    -- 开始交易时间
    trading_end_time String DEFAULT '15:00',
    -- 结束交易时间
    lunch_start_time String DEFAULT '11:30',
    -- 午休开始
    lunch_end_time String DEFAULT '13:00',
    -- 午休结束
    -- 元数据
    data_source String DEFAULT 'exchange',
    -- 数据源
    created_at DateTime DEFAULT now(),
    -- 创建时间
    updated_at DateTime DEFAULT now() -- 更新时间
) ENGINE = ReplacingMergeTree(date)
ORDER BY date
PRIMARY KEY date;

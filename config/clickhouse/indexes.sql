-- 创建索引以提高查询性能

-- 为日线行情数据创建索引
ALTER TABLE pulse_trader.daily_quotes
ADD INDEX IF NOT EXISTS idx_symbol_volume (symbol, volume) TYPE minmax GRANULARITY 1;

ALTER TABLE pulse_trader.daily_quotes
ADD INDEX IF NOT EXISTS idx_price_change (change_percent) TYPE minmax GRANULARITY 10;

ALTER TABLE pulse_trader.daily_quotes
ADD INDEX IF NOT EXISTS idx_date_symbol (date, symbol) TYPE bloom_filter GRANULARITY 1;

-- 为分钟级行情数据创建索引
ALTER TABLE pulse_trader.intraday_quotes
ADD INDEX IF NOT EXISTS idx_datetime_symbol (datetime, symbol) TYPE minmax GRANULARITY 1;

ALTER TABLE pulse_trader.intraday_quotes
ADD INDEX IF NOT EXISTS idx_volume (volume) TYPE minmax GRANULARITY 100;

-- 为实时快照表创建索引
ALTER TABLE pulse_trader.realtime_snapshot
ADD INDEX IF NOT EXISTS idx_market_cap (market_cap) TYPE minmax GRANULARITY 1;

ALTER TABLE pulse_trader.realtime_snapshot
ADD INDEX IF NOT EXISTS idx_change_percent (change_percent) TYPE minmax GRANULARITY 1;

-- 为财务数据创建索引
ALTER TABLE pulse_trader.financial_data
ADD INDEX IF NOT EXISTS idx_report_date (report_date) TYPE minmax GRANULARITY 1;

ALTER TABLE pulse_trader.financial_data
ADD INDEX IF NOT EXISTS idx_symbol_report_type (symbol, report_type) TYPE bloom_filter GRANULARITY 1;

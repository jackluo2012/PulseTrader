-- PulseTrader A股量化交易数据库表结构

-- 使用专门的数据库
USE pulse_trader;

-- 1. 股票基础信息表
CREATE TABLE IF NOT EXISTS stock_info (
    symbol String,           -- 股票代码 (如: 000001.SZ)
    name String,             -- 股票名称
    market String,           -- 市场 (SH/SZ/BJ)
    industry String,         -- 行业
    sector String,           -- 板块
    list_date Date,          -- 上市日期
    delist_date Nullable(Date), -- 退市日期
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY market
ORDER BY (symbol, created_at);

-- 2. 日线行情数据表 (A股专用)
CREATE TABLE IF NOT EXISTS stock_daily (
    symbol String,           -- 股票代码
    trade_date Date,         -- 交易日期
    open Decimal(18, 4),     -- 开盘价
    high Decimal(18, 4),     -- 最高价
    low Decimal(18, 4),      -- 最低价
    close Decimal(18, 4),    -- 收盘价
    volume UInt64,           -- 成交量(股)
    amount Decimal(18, 2),   -- 成交额(元)
    turnover_rate Decimal(8, 4), -- 换手率
    pe_ratio Decimal(10, 4), -- 市盈率
    pb_ratio Decimal(10, 4), -- 市净率
    cap_total Decimal(18, 2), -- 总市值
    cap_flow Decimal(18, 2),  -- 流通市值
    limit_up UInt8 DEFAULT 0, -- 涨停标记
    limit_down UInt8 DEFAULT 0, -- 跌停标记
    created_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(trade_date)
ORDER BY (symbol, trade_date);

-- 3. 分钟线数据表 (用于高频策略)
CREATE TABLE IF NOT EXISTS stock_1min (
    symbol String,           -- 股票代码
    datetime DateTime,       -- 时间戳
    open Decimal(18, 4),     -- 开盘价
    high Decimal(18, 4),     -- 最高价
    low Decimal(18, 4),      -- 最低价
    close Decimal(18, 4),    -- 收盘价
    volume UInt64,           -- 成交量
    amount Decimal(18, 2),   -- 成交额
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(datetime)
ORDER BY (symbol, datetime);

-- 4. 技术指标表
CREATE TABLE IF NOT EXISTS stock_indicators (
    symbol String,           -- 股票代码
    trade_date Date,         -- 交易日期
    indicator_name String,   -- 指标名称
    indicator_value Decimal(18, 6), -- 指标值
    period_param UInt16,     -- 参数周期
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY (indicator_name, toYYYYMM(trade_date))
ORDER BY (symbol, trade_date, indicator_name);

-- 5. 交易信号表
CREATE TABLE IF NOT EXISTS trading_signals (
    signal_id UUID,          -- 信号ID
    symbol String,           -- 股票代码
    strategy_name String,    -- 策略名称
    signal_type String,      -- 信号类型 (BUY/SELL/HOLD)
    signal_time DateTime,    -- 信号时间
    price Decimal(18, 4),    -- 触发价格
    confidence Decimal(5, 4), -- 置信度
    reason String,           -- 信号原因
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(signal_time)
ORDER BY (strategy_name, symbol, signal_time);

-- 6. 回测结果表
CREATE TABLE IF NOT EXISTS backtest_results (
    result_id UUID,          -- 结果ID
    strategy_name String,    -- 策略名称
    start_date Date,         -- 开始日期
    end_date Date,           -- 结束日期
    initial_capital Decimal(18, 2), -- 初始资金
    final_capital Decimal(18, 2),   -- 最终资金
    total_return Decimal(8, 4),      -- 总收益率
    annual_return Decimal(8, 4),     -- 年化收益率
    max_drawdown Decimal(8, 4),      -- 最大回撤
    sharpe_ratio Decimal(8, 4),      -- 夏普比率
    win_rate Decimal(5, 4),          -- 胜率
    profit_loss_ratio Decimal(8, 4), -- 盈亏比
    total_trades UInt32,             -- 总交易次数
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (strategy_name, created_at);

-- 创建视图：最新股票价格
CREATE VIEW IF NOT EXISTS v_latest_price AS
SELECT
    symbol,
    trade_date,
    close as latest_price,
    volume,
    amount,
    turnover_rate
FROM stock_daily
WHERE trade_date = (
    SELECT MAX(trade_date)
    FROM stock_daily
    WHERE stock_daily.symbol = stock_daily.symbol
);

-- 插入一些测试数据
INSERT INTO stock_info (symbol, name, market, industry, list_date) VALUES
('000001.SZ', '平安银行', 'SZ', '银行', '1991-04-03'),
('000002.SZ', '万科A', 'SZ', '房地产', '1991-01-29'),
('600000.SH', '浦发银行', 'SH', '银行', '1999-11-10'),
('600036.SH', '招商银行', 'SH', '银行', '2002-04-09');

-- 查看创建的表
SHOW TABLES;

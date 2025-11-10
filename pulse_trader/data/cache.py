"""
ClickHouse数据缓存管理器

使用ClickHouse作为高性能时序数据库存储量化交易数据
"""

import clickhouse_connect
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import logging
from dataclasses import asdict


class DataCache:
    """
    基于ClickHouse的数据缓存管理器

    相比SQLite3的优势：
    1. 更高的写入性能，适合高频数据
    2. 更好的压缩率，节省存储空间
    3. 更快的查询性能，特别是聚合查询
    4. 原生支持时序数据
    """

    def __init__(self,
                 host: str = 'localhost',
                 port: int = 8123,
                 database: str = 'pulse_trader',
                 username: str = 'devuser',
                 password: str = 'devpass',
                 secure: bool = False):
        """
        初始化ClickHouse连接

        Args:
            host: ClickHouse服务器地址
            port: HTTP接口端口
            database: 数据库名称
            username: 用户名
            password: 密码
            secure: 是否使用HTTPS
        """
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            database=database,
            username=username,
            password=password,
            secure=secure
        )

        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """初始化数据库和表结构"""
        try:
            # 创建数据库
            self.client.command('CREATE DATABASE IF NOT EXISTS pulse_trader')

            # 创建实时行情表 - 使用MergeTree引擎优化时序数据
            self.client.command("""
                CREATE TABLE IF NOT EXISTS pulse_trader.realtime_quotes (
                    symbol String,
                    price Float64,
                    change Float64,
                    change_pct Float64,
                    volume UInt64,
                    timestamp DateTime64(3),
                    bid_price Float64,
                    ask_price Float64,
                    date Date MATERIALIZED toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (symbol, timestamp)
                TTL toDateTime(timestamp) + INTERVAL 30 DAY
            """)

            # 创建日线数据表 - 使用ReplacingMergeTree处理数据更新
            self.client.command("""
                CREATE TABLE IF NOT EXISTS pulse_trader.daily_data (
                    symbol String,
                    date Date,
                    open Float64,
                    high Float64,
                    low Float64,
                    close Float64,
                    volume UInt64,
                    created_at DateTime DEFAULT now()
                ) ENGINE = ReplacingMergeTree(created_at)
                PARTITION BY toYYYYMM(date)
                ORDER BY (symbol, date)
            """)

            # 创建策略信号表
            self.client.command("""
                CREATE TABLE IF NOT EXISTS pulse_trader.strategy_signals (
                    id UInt64,
                    strategy_name String,
                    symbol String,
                    signal Int8,
                    price Float64,
                    timestamp DateTime64(3),
                    created_at DateTime DEFAULT now()
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (strategy_name, symbol, timestamp)
                TTL toDateTime(timestamp) + INTERVAL 90 DAY
            """)

            # 创建交易记录表
            self.client.command("""
                CREATE TABLE IF NOT EXISTS pulse_trader.trade_records (
                    id UInt64,
                    strategy_name String,
                    symbol String,
                    action String,
                    price Float64,
                    quantity UInt64,
                    amount Float64,
                    commission Float64,
                    timestamp DateTime64(3),
                    created_at DateTime DEFAULT now()
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (strategy_name, symbol, timestamp)
            """)

            self.logger.info("ClickHouse数据库初始化完成")

        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise

    def save_realtime_quote(self, quote_data: Dict[str, Any]):
        """
        保存实时行情数据

        Args:
            quote_data: 行情数据字典
        """
        try:
            # 使用参数化查询防止SQL注入
            self.client.insert(
                table='realtime_quotes',
                data=[(
                    quote_data['symbol'],
                    float(quote_data['price']),
                    float(quote_data['change']),
                    float(quote_data['change_pct']),
                    int(quote_data['volume']),
                    quote_data['timestamp'],
                    float(quote_data.get('bid_price', 0)),
                    float(quote_data.get('ask_price', 0))
                )],
                column_names=['symbol', 'price', 'change', 'change_pct', 'volume', 'timestamp', 'bid_price', 'ask_price']
            )
        except Exception as e:
            self.logger.error(f"保存实时行情失败: {e}")

    def get_latest_quotes(self, symbols: List[str] = None) -> pd.DataFrame:
        """
        获取最新行情数据

        Args:
            symbols: 股票代码列表，为空则获取所有股票

        Returns:
            最新行情DataFrame
        """
        try:
            if symbols:
                # 使用IN查询特定股票的最新数据
                symbols_str = "', '".join(symbols)
                query = f"""
                    SELECT *
                    FROM (
                        SELECT
                            symbol,
                            any(price) as price,
                            any(change) as change,
                            any(change_pct) as change_pct,
                            any(volume) as volume,
                            any(timestamp) as timestamp,
                            any(bid_price) as bid_price,
                            any(ask_price) as ask_price
                        FROM pulse_trader.realtime_quotes
                        WHERE symbol IN ('{symbols_str}')
                        GROUP BY symbol
                    )
                    ORDER BY symbol
                """
            else:
                query = """
                    SELECT *
                    FROM (
                        SELECT
                            symbol,
                            any(price) as price,
                            any(change) as change,
                            any(change_pct) as change_pct,
                            any(volume) as volume,
                            any(timestamp) as timestamp,
                            any(bid_price) as bid_price,
                            any(ask_price) as ask_price
                        FROM pulse_trader.realtime_quotes
                        GROUP BY symbol
                    )
                    ORDER BY symbol
                """

            return self.client.query_df(query)

        except Exception as e:
            self.logger.error(f"获取最新行情失败: {e}")
            return pd.DataFrame()

    def save_daily_data(self, symbol: str, data: pd.DataFrame):
        """
        保存日线数据

        Args:
            symbol: 股票代码
            data: 日线数据DataFrame
        """
        try:
            data = data.copy()
            data['symbol'] = symbol

            # 转换数据类型以匹配ClickHouse表结构
            insert_data = data.to_dict('records')

            self.client.insert(
                table='daily_data',
                data=insert_data
            )

            self.logger.info(f"保存 {symbol} 日线数据 {len(data)} 条")

        except Exception as e:
            self.logger.error(f"保存日线数据失败: {e}")

    def get_daily_data(self, symbol: str, start_date: str = None,
                      end_date: str = None) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            日线数据DataFrame
        """
        try:
            query = f"SELECT * FROM pulse_trader.daily_data WHERE symbol = '{symbol}'"

            if start_date:
                query += f" AND date >= '{start_date}'"
            if end_date:
                query += f" AND date <= '{end_date}'"

            query += " ORDER BY date"

            return self.client.query_df(query)

        except Exception as e:
            self.logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()

    def save_strategy_signal(self, strategy_name: str, symbol: str,
                           signal: int, price: float, timestamp: datetime = None):
        """
        保存策略信号

        Args:
            strategy_name: 策略名称
            symbol: 股票代码
            signal: 信号类型 (1: 买入, -1: 卖出, 0: 持有)
            price: 价格
            timestamp: 时间戳
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()

            # 生成唯一ID
            signal_id = int(timestamp.timestamp() * 1000000)

            self.client.insert(
                table='strategy_signals',
                data=[(
                    signal_id,
                    strategy_name,
                    symbol,
                    signal,
                    float(price),
                    timestamp,
                    datetime.now()
                )],
                column_names=['id', 'strategy_name', 'symbol', 'signal', 'price', 'timestamp', 'created_at']
            )

        except Exception as e:
            self.logger.error(f"保存策略信号失败: {e}")
            raise

    def save_trade_record(self, strategy_name: str, symbol: str, action: str,
                         price: float, quantity: int, commission: float = 0):
        """
        保存交易记录

        Args:
            strategy_name: 策略名称
            symbol: 股票代码
            action: 交易动作 (buy/sell)
            price: 价格
            quantity: 数量
            commission: 手续费
        """
        try:
            amount = price * quantity

            # 生成唯一ID
            trade_id = int(datetime.now().timestamp() * 1000000)

            trade_time = datetime.now()
            self.client.insert(
                table='trade_records',
                data=[(
                    trade_id,
                    strategy_name,
                    symbol,
                    action,
                    float(price),
                    quantity,
                    float(amount),
                    float(commission),
                    trade_time,
                    trade_time
                )],
                column_names=['id', 'strategy_name', 'symbol', 'action', 'price', 'quantity', 'amount', 'commission', 'timestamp', 'created_at']
            )

        except Exception as e:
            self.logger.error(f"保存交易记录失败: {e}")
            raise

    def get_strategy_performance(self, strategy_name: str,
                               start_date: str = None) -> Dict[str, Any]:
        """
        获取策略绩效统计

        Args:
            strategy_name: 策略名称
            start_date: 开始日期

        Returns:
            绩效统计字典
        """
        try:
            query = f"""
                SELECT
                    count(*) as total_trades,
                    countIf(action = 'buy') as buy_trades,
                    countIf(action = 'sell') as sell_trades,
                    sum(amount) as total_amount,
                    avg(price) as avg_price,
                    max(timestamp) as last_trade_time
                FROM pulse_trader.trade_records
                WHERE strategy_name = '{strategy_name}'
            """

            if start_date:
                query += f" AND timestamp >= '{start_date}'"

            result = self.client.query(query)
            row = result.result_rows[0]

            return {
                'total_trades': row[0] or 0,
                'buy_trades': row[1] or 0,
                'sell_trades': row[2] or 0,
                'total_amount': row[3] or 0,
                'avg_price': row[4] or 0,
                'last_trade_time': row[5]
            }

        except Exception as e:
            self.logger.error(f"获取策略绩效失败: {e}")
            return {}

    def cleanup_old_data(self, days_to_keep: int = 30):
        """
        清理旧数据

        注意：ClickHouse的TTL会自动清理过期数据，这里只是辅助清理

        Args:
            days_to_keep: 保留天数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # ClickHouse会通过TTL自动清理，这里只是记录日志
            self.logger.info(f"ClickHouse TTL将自动清理 {days_to_keep} 天前的旧数据")

        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")

    def get_aggregated_data(self, symbol: str, interval: str = '1h',
                          start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取聚合数据 - ClickHouse的强大功能

        Args:
            symbol: 股票代码
            interval: 聚合间隔 (1m, 5m, 15m, 1h, 1d)
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            聚合数据DataFrame
        """
        try:
            # 根据间隔确定时间聚合函数
            time_func = {
                '1m': 'toStartOfMinute',
                '5m': 'toStartOfFiveMinutes',
                '15m': 'toStartOfFifteenMinutes',
                '1h': 'toStartOfHour',
                '1d': 'toStartOfDay'
            }.get(interval, 'toStartOfHour')

            query = f"""
                SELECT
                    {time_func}(timestamp) as time_period,
                    argMin(price, timestamp) as open,
                    max(price) as high,
                    min(price) as low,
                    argMax(price, timestamp) as close,
                    sum(volume) as volume
                FROM pulse_trader.realtime_quotes
                WHERE symbol = '{symbol}'
            """

            if start_date:
                query += f" AND timestamp >= '{start_date}'"
            if end_date:
                query += f" AND timestamp <= '{end_date}'"

            query += f" GROUP BY time_period ORDER BY time_period"

            return self.client.query_df(query)

        except Exception as e:
            self.logger.error(f"获取聚合数据失败: {e}")
            return pd.DataFrame()

    def batch_insert_quotes(self, quotes_data: List[Dict[str, Any]]):
        """
        批量插入实时行情数据 - ClickHouse的强项

        Args:
            quotes_data: 行情数据列表
        """
        try:
            if not quotes_data:
                return

            # 转换数据格式
            insert_data = []
            for quote in quotes_data:
                insert_data.append((
                    quote['symbol'],
                    float(quote['price']),
                    float(quote['change']),
                    float(quote['change_pct']),
                    int(quote['volume']),
                    quote['timestamp'],
                    float(quote.get('bid_price', 0)),
                    float(quote.get('ask_price', 0))
                ))

            self.client.insert(
                table='realtime_quotes',
                data=insert_data,
                column_names=['symbol', 'price', 'change', 'change_pct', 'volume', 'timestamp', 'bid_price', 'ask_price']
            )

            self.logger.info(f"批量插入 {len(insert_data)} 条实时行情")

        except Exception as e:
            self.logger.error(f"批量插入实时行情失败: {e}")

    def close(self):
        """关闭连接"""
        if hasattr(self.client, 'close'):
            self.client.close()
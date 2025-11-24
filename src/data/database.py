"""
ClickHouse数据库操作类
提供连接管理、数据查询和插入功能
"""

import logging
from typing import List, Dict, Any, Optional
from clickhouse_driver import Client
from clickhouse_pool import ChPool
import redis
import pandas as pd
from datetime import datetime, date
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClickHouseManager:
    """ClickHouse数据库管理器"""

    def __init__(self, host='localhost', port=9000,
                 user='quant_user', password='Quant@2024',
                 database='pulse_trader'):
        """初始化ClickHouse连接"""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

        # 创建连接池
        self.pool = ChPool(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connections_min=5,
            connections_max=20
        )

        # Redis缓存连接
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)

        # 单例连接（用于复杂查询）
        self.client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

        logger.info("ClickHouse连接初始化完成")

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            result = self.client.execute('SELECT 1')
            if result[0][0] == 1:
                logger.info("ClickHouse连接测试成功")
                return True
        except Exception as e:
            logger.error(f"ClickHouse连接测试失败: {e}")
            return False

    def execute_query(self, query: str, params: Dict = None) -> Any:
        """执行查询"""
        try:
            with self.pool.get_client() as client:
                if params:
                    return client.execute(query, params)
                else:
                    return client.execute(query)
        except Exception as e:
            logger.error(f"查询执行失败: {e}, SQL: {query}")
            raise

    def get_stock_info(self, symbol: str = None) -> pd.DataFrame:
        """获取股票基础信息"""
        try:
            if symbol:
                query = """
                    SELECT * FROM stock_info
                    WHERE symbol = %(symbol)s AND is_active = 1
                """
                params = {'symbol': symbol}
            else:
                query = """
                    SELECT * FROM stock_info
                    WHERE is_active = 1
                    ORDER BY symbol
                """
                params = {}

            result = self.client.execute(query, params)
            columns = ['symbol', 'name', 'market', 'industry', 'sector',
                      'list_date', 'delist_date', 'is_active', 'created_at']
            df = pd.DataFrame(result, columns=columns)

            return df

        except Exception as e:
            logger.error(f"查询股票信息失败: {e}")
            return pd.DataFrame()

    def close(self):
        """关闭连接"""
        try:
            if hasattr(self, 'pool'):
                # ChPool doesn't have a close method, but individual connections do
                pass
            if hasattr(self, 'redis_client'):
                self.redis_client.close()
            logger.info("ClickHouse连接已关闭")
        except Exception as e:
            logger.error(f"关闭连接时发生错误: {e}")

# 创建全局数据库管理器实例
db_manager = ClickHouseManager()

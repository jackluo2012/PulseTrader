#!/usr/bin/env python3
"""
ClickHouse分区管理脚本
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import datetime, timedelta

import pandas as pd

from src.data.database import db_manager

logger = logging.getLogger(__name__)


class PartitionManager:
    """分区管理器"""

    def __init__(self, db_client=None):
        self.db_client = db_client or db_manager

    def create_partition_function(self):
        """创建分区管理函数"""
        sql = """
        -- 自动创建未来分区的存储过程
        CREATE PROCEDURE IF NOT EXISTS pulse_trader.create_future_partitions() AS
        BEGIN
            DECLARE future_days DEFAULT 30;
            DECLARE i DEFAULT 1;
            DECLARE current_date DEFAULT today();
            DECLARE partition_date DATE;
            DECLARE partition_name STRING;

            -- 为日线数据创建未来分区
            WHILE i <= future_days DO
                partition_date = current_date + INTERVAL i DAY;
                partition_name = toString(toYYYYMM(partition_date));

                -- 执行分区创建（实际使用时需要根据具体表结构调整）
                -- ALTER TABLE pulse_trader.daily_quotes ADD PARTITION partition_name;

                i = i + 1;
            END WHILE;
        END;
        """
        self.db_client.execute_query(sql)
        logger.info("分区管理函数创建完成")

    def analyze_partition_usage(self):
        """分析分区使用情况"""
        sql = """
        SELECT
            table,
            partition,
            count() as row_count,
            sum(bytes_on_disk) as size_bytes,
            round(sum(bytes_on_disk) / 1024 / 1024, 2) as size_mb,
            round(avg(row_count), 0) as avg_rows_per_part
        FROM system.parts
        WHERE database = 'pulse_trader'
          AND active = 1
          AND table IN ('daily_quotes', 'intraday_quotes')
        GROUP BY table, partition
        ORDER BY table, partition
        """

        try:
            result = self.db_client.execute_query(sql)
            if result:
                df = pd.DataFrame(
                    result,
                    columns=[
                        "table",
                        "partition",
                        "row_count",
                        "size_bytes",
                        "size_mb",
                        "avg_rows_per_part",
                    ],
                )
                logger.info("分区使用情况分析完成")
                return df
        except Exception as e:
            logger.error(f"分区使用情况分析失败: {e}")
            return pd.DataFrame()

    def optimize_partitions(self, table_name: str, partition_filter: str = None):
        """优化指定分区"""
        base_sql = f"OPTIMIZE TABLE {table_name}"

        if partition_filter:
            sql = f"{base_sql} PARTITION {partition_filter} FINAL"
        else:
            sql = f"{base_sql} FINAL"

        try:
            self.db_client.execute_query(sql)
            logger.info(f"分区优化完成: {table_name} {partition_filter or 'ALL'}")
        except Exception as e:
            logger.error(f"分区优化失败 {table_name}: {e}")

    def drop_old_partitions(self, table_name: str, retention_days: int):
        """删除过期分区"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cutoff_partition = cutoff_date.strftime("%Y%m")

        sql = f"""
        ALTER TABLE {table_name}
        DROP PARTITION WHERE partition < '{cutoff_partition}'
        """

        try:
            self.db_client.execute_query(sql)
            logger.info(f"删除过期分区完成: {table_name}, 保留最近{retention_days}天")
        except Exception as e:
            logger.error(f"删除过期分区失败 {table_name}: {e}")

    def merge_small_partitions(self, table_name: str, min_size_mb: float = 10):
        """合并小分区"""
        sql = f"""
        SELECT
            partition,
            sum(bytes_on_disk) / 1024 / 1024 as size_mb
        FROM system.parts
        WHERE database = 'pulse_trader'
          AND table = '{table_name}'
          AND active = 1
        GROUP BY partition
        HAVING size_mb < {min_size_mb}
        ORDER BY partition
        """

        try:
            small_partitions = self.db_client.execute_query(sql)

            if small_partitions:
                logger.info(f"发现 {len(small_partitions)} 个小分区需要合并")

                for partition_info in small_partitions:
                    partition_name = partition_info[0]
                    size_mb = partition_info[1]
                    logger.info(f"分区 {partition_name}: {size_mb:.2f}MB")

                # 执行分区合并
                merge_sql = f"OPTIMIZE TABLE {table_name} FINAL"
                self.db_client.execute_query(merge_sql)
                logger.info(f"小分区合并完成: {table_name}")

        except Exception as e:
            logger.error(f"合并小分区失败 {table_name}: {e}")


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)

    manager = PartitionManager()

    print("=== ClickHouse分区管理 ===")

    # 1. 分析分区使用情况
    print("\n1. 分析分区使用情况...")
    usage_df = manager.analyze_partition_usage()
    if not usage_df.empty:
        print(usage_df)

    # 2. 优化分区
    print("\n2. 优化分区...")
    tables_to_optimize = ["daily_quotes", "intraday_quotes"]
    for table in tables_to_optimize:
        manager.optimize_partitions(table)

    # 3. 合并小分区
    print("\n3. 合并小分区...")
    for table in tables_to_optimize:
        manager.merge_small_partitions(table, min_size_mb=5)

    print("\n分区管理完成！")


if __name__ == "__main__":
    main()

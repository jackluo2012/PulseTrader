#!/usr/bin/env python3
"""
ClickHouse表结构初始化脚本
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging

from src.data.database import db_manager

logger = logging.getLogger(__name__)


def create_tables():
    """创建所有表结构"""

    table_scripts = [
        "config/clickhouse/tables/stock_info.sql",
        "config/clickhouse/tables/daily_quotes.sql",
        "config/clickhouse/tables/intraday_quotes.sql",
        "config/clickhouse/tables/realtime_snapshot.sql",
        "config/clickhouse/tables/financial_data.sql",
        "config/clickhouse/tables/trading_calendar.sql",
    ]

    for script_path in table_scripts:
        try:
            if os.path.exists(script_path):
                with open(script_path, "r", encoding="utf-8") as f:
                    sql_content = f.read()

                # 分割多个SQL语句
                sql_statements = [
                    stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
                ]

                for sql in sql_statements:
                    if sql:
                        db_manager.execute_query(sql)
                        logger.info(f"执行SQL: {sql[:50]}...")

                logger.info(f"表结构创建完成: {script_path}")
            else:
                logger.warning(f"脚本文件不存在: {script_path}")

        except Exception as e:
            logger.error(f"创建表结构失败 {script_path}: {e}")


def create_indexes():
    """创建索引"""
    index_script = "config/clickhouse/indexes.sql"

    try:
        if os.path.exists(index_script):
            with open(index_script, "r", encoding="utf-8") as f:
                sql_content = f.read()

            sql_statements = [
                stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
            ]

            for sql in sql_statements:
                if sql:
                    db_manager.execute_query(sql)
                    logger.info(f"创建索引: {sql[:50]}...")

            logger.info("索引创建完成")
        else:
            logger.warning(f"索引脚本不存在: {index_script}")

    except Exception as e:
        logger.error(f"创建索引失败: {e}")


def verify_tables():
    """验证表结构"""
    sql = """
    SELECT
        table,
        count() as column_count,
        sum(data_uncompressed_bytes) as size_bytes,
        round(sum(data_uncompressed_bytes) / 1024, 2) as size_kb
    FROM system.columns
    WHERE database = 'pulse_trader'
    GROUP BY table
    ORDER BY table
    """

    try:
        result = db_manager.execute_query(sql)
        if result:
            print("\n=== 表结构验证 ===")
            for row in result:
                print(f"表: {row[0]}, 列数: {row[1]}, 大小: {row[3]} KB")
    except Exception as e:
        logger.error(f"验证表结构失败: {e}")


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)

    print("🚀 开始初始化ClickHouse表结构...")

    # 测试数据库连接
    if not db_manager.test_connection():
        print("❌ 数据库连接失败，请检查配置")
        return

    print("✅ 数据库连接正常")

    # 创建表结构
    print("\n📝 创建表结构...")
    create_tables()

    # 创建索引
    print("\n🔍 创建索引...")
    create_indexes()

    # 验证表结构
    print("\n✔️ 验证表结构...")
    verify_tables()

    print("\n🎉 ClickHouse表结构初始化完成！")


if __name__ == "__main__":
    main()

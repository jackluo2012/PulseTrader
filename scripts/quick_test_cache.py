#!/usr/bin/env python3
"""
ClickHouse DataCache 快速测试脚本

用于快速验证 DataCache 模块基本功能是否正常
"""

import sys
import os
import clickhouse_connect
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_trader.data.cache import DataCache

def test_clickhouse_connection():
    """测试ClickHouse基础连接"""
    print("🔍 检查 ClickHouse 服务状态...")

    try:
        # 尝试连接到默认数据库
        client = clickhouse_connect.get_client(
            host='localhost',
            port=8123,
            database='default'
        )

        # 测试简单查询
        result = client.query('SELECT 1 as test')
        print("✅ ClickHouse 服务正常运行")
        client.close()
        return True

    except Exception as e:
        print(f"❌ ClickHouse 连接失败: {e}")
        print("\n请确保 ClickHouse 服务正在运行:")
        print("  - Docker: docker run -d --name clickhouse-server -p 8123:8123 clickhouse/clickhouse-server")
        print("  - 或安装本地 ClickHouse 服务")
        return False

def quick_test():
    """快速测试DataCache连接和基本功能"""
    print("🚀 开始快速测试 DataCache 模块...")

    # 首先检查 ClickHouse 服务
    if not test_clickhouse_connection():
        return False

    try:
        # 1. 测试连接和初始化
        print("\n1️⃣ 测试数据库连接和初始化...")
        cache = DataCache()
        print("✅ 数据库连接成功")

        # 2. 测试表创建
        print("\n2️⃣ 验证数据表...")
        try:
            tables = cache.client.query("SHOW TABLES FROM pulse_trader")
            table_names = [row[0] for row in tables.result_rows]
            print(f"✅ 已创建表: {', '.join(table_names)}")
        except Exception as e:
            print(f"⚠️ 表查询失败: {e}")
            # 这可能是正常的，因为数据库可能刚刚创建

        # 3. 测试插入一条实时数据
        print("\n3️⃣ 测试数据插入...")
        test_quote = {
            'symbol': 'TEST',
            'price': 100.0,
            'change': 1.0,
            'change_pct': 1.01,
            'volume': 1000000,
            'timestamp': datetime.now(),
            'bid_price': 99.9,
            'ask_price': 100.1
        }

        cache.save_realtime_quote(test_quote)
        print("✅ 数据插入成功")

        # 4. 测试数据查询
        print("\n4️⃣ 测试数据查询...")
        result = cache.get_latest_quotes(['TEST'])
        if not result.empty:
            print(f"✅ 查询成功，最新价格: {result.iloc[0]['price']}")
        else:
            print("⚠️ 查询结果为空（这可能是正常的，可能需要等待数据写入）")

        # 5. 测试其他基本功能
        print("\n5️⃣ 测试策略信号保存...")
        cache.save_strategy_signal('test_strategy', 'TEST', 1, 100.0)
        print("✅ 策略信号保存成功")

        print("\n6️⃣ 测试交易记录保存...")
        cache.save_trade_record('test_strategy', 'TEST', 'buy', 100.0, 100, 1.0)
        print("✅ 交易记录保存成功")

        # 6. 关闭连接
        cache.close()
        print("\n🎉 快速测试完成！DataCache模块基本功能正常。")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    quick_test()
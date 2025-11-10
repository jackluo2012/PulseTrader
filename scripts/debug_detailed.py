#!/usr/bin/env python3
"""
详细调试 DataCache 问题
"""

import sys
import os
from datetime import datetime
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_trader.data.cache import DataCache
import clickhouse_connect

def detailed_debug():
    """详细调试DataCache问题"""
    print("🔍 详细调试 DataCache 问题...")

    try:
        # 创建 DataCache 实例
        cache = DataCache(
            host='localhost',
            port=8124,
            database='pulse_trader',
            username='devuser',
            password='devpass'
        )
        print("✅ DataCache 初始化成功")

        print("\n1️⃣ 测试策略信号保存...")
        try:
            cache.save_strategy_signal('test_strategy', 'AAPL', 1, 150.0)
            print("✅ 策略信号保存成功")
        except Exception as e:
            print(f"❌ 策略信号保存失败: {e}")
            traceback.print_exc()

        print("\n2️⃣ 测试交易记录保存...")
        try:
            cache.save_trade_record('test_strategy', 'AAPL', 'buy', 150.0, 100, 1.5)
            print("✅ 交易记录保存成功")
        except Exception as e:
            print(f"❌ 交易记录保存失败: {e}")
            traceback.print_exc()

        print("\n3️⃣ 检查记录数...")
        try:
            result = cache.client.query("SELECT COUNT(*) FROM pulse_trader.strategy_signals")
            signal_count = result.result_rows[0][0]
            print(f"策略信号记录数: {signal_count}")

            result = cache.client.query("SELECT COUNT(*) FROM pulse_trader.trade_records")
            trade_count = result.result_rows[0][0]
            print(f"交易记录数: {trade_count}")

        except Exception as e:
            print(f"查询失败: {e}")
            traceback.print_exc()

        cache.close()

    except Exception as e:
        print(f"DataCache 初始化失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    detailed_debug()
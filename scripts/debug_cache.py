#!/usr/bin/env python3
"""
调试 DataCache 问题
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_trader.data.cache import DataCache
import clickhouse_connect

def debug():
    """调试DataCache问题"""
    print("🔍 调试 DataCache 问题...")

    # 连接客户端
    client = clickhouse_connect.get_client(
        host='localhost',
        port=8124,
        database='pulse_trader',
        username='devuser',
        password='devpass'
    )

    print("1️⃣ 检查表结构...")

    # 检查策略信号表结构
    print("策略信号表结构:")
    result = client.query("DESCRIBE pulse_trader.strategy_signals")
    for row in result.result_rows:
        print(f"  {row[0]}: {row[1]}")

    print("\n交易记录表结构:")
    result = client.query("DESCRIBE pulse_trader.trade_records")
    for row in result.result_rows:
        print(f"  {row[0]}: {row[1]}")

    print("\n2️⃣ 测试简单插入...")

    # 测试策略信号插入
    try:
        signal_data = [{
            'id': int(datetime.now().timestamp() * 1000000),
            'strategy_name': 'test',
            'symbol': 'TEST',
            'signal': 1,
            'price': 100.0,
            'timestamp': datetime.now(),
            'created_at': datetime.now()
        }]

        client.insert('pulse_trader.strategy_signals', signal_data)
        print("✅ 策略信号插入成功")
    except Exception as e:
        print(f"❌ 策略信号插入失败: {e}")

    # 测试交易记录插入
    try:
        trade_data = [{
            'id': int(datetime.now().timestamp() * 1000000) + 1,
            'strategy_name': 'test',
            'symbol': 'TEST',
            'action': 'buy',
            'price': 100.0,
            'quantity': 100,
            'amount': 10000.0,
            'commission': 1.0,
            'timestamp': datetime.now(),
            'created_at': datetime.now()
        }]

        client.insert('pulse_trader.trade_records', trade_data)
        print("✅ 交易记录插入成功")
    except Exception as e:
        print(f"❌ 交易记录插入失败: {e}")

    print("\n3️⃣ 测试查询...")
    try:
        result = client.query("SELECT COUNT(*) FROM pulse_trader.strategy_signals")
        print(f"策略信号记录数: {result.result_rows[0][0]}")

        result = client.query("SELECT COUNT(*) FROM pulse_trader.trade_records")
        print(f"交易记录数: {result.result_rows[0][0]}")

    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    debug()
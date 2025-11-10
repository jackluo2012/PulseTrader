#!/usr/bin/env python3
"""
测试 ClickHouse 插入格式
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import clickhouse_connect

def test_insert_format():
    """测试不同的插入格式"""
    print("🔍 测试 ClickHouse 插入格式...")

    # 连接客户端
    client = clickhouse_connect.get_client(
        host='localhost',
        port=8124,
        database='pulse_trader',
        username='devuser',
        password='devpass'
    )

    print("1️⃣ 测试字典格式...")
    try:
        # 测试字典列表格式
        signal_data = [{
            'id': 1234567890,
            'strategy_name': 'test',
            'symbol': 'TEST',
            'signal': 1,
            'price': 100.0,
            'timestamp': datetime.now(),
            'created_at': datetime.now()
        }]

        client.insert('pulse_trader.strategy_signals', signal_data)
        print("✅ 字典格式插入成功")
    except Exception as e:
        print(f"❌ 字典格式插入失败: {e}")

    print("2️⃣ 测试元组格式...")
    try:
        # 测试元组格式（按列顺序）
        signal_data = [(1234567891, 'test', 'TEST2', 1, 100.0, datetime.now(), datetime.now())]
        column_names = ['id', 'strategy_name', 'symbol', 'signal', 'price', 'timestamp', 'created_at']

        client.insert('pulse_trader.strategy_signals', signal_data, column_names=column_names)
        print("✅ 元组格式插入成功")
    except Exception as e:
        print(f"❌ 元组格式插入失败: {e}")

    print("3️⃣ 检查记录数...")
    try:
        result = client.query("SELECT COUNT(*) FROM pulse_trader.strategy_signals")
        print(f"策略信号记录数: {result.result_rows[0][0]}")

    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    test_insert_format()
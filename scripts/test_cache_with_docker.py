#!/usr/bin/env python3
"""
ClickHouse DataCache 测试脚本 (Docker 版本)

使用 Docker 容器测试 DataCache 模块功能
"""

import sys
import os
import clickhouse_connect
from datetime import datetime, timedelta
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_trader.data.cache import DataCache

def test_docker_clickhouse():
    """测试 Docker 中的 ClickHouse 连接"""
    print("🐳 测试 Docker ClickHouse 连接...")

    try:
        # 等待容器启动
        print("⏳ 等待 ClickHouse 容器启动...")
        time.sleep(5)

        # 测试连接
        client = clickhouse_connect.get_client(
            host='localhost',
            port=8124,  # 使用映射的端口
            database='pulse_trader',
            username='devuser',
            password='devpass'
        )

        # 测试简单查询
        result = client.query('SELECT 1 as test')
        print("✅ Docker ClickHouse 连接成功")
        client.close()
        return True

    except Exception as e:
        print(f"❌ Docker ClickHouse 连接失败: {e}")
        return False

def test_datacache_functionality():
    """测试 DataCache 功能"""
    print("\n🚀 测试 DataCache 功能...")

    try:
        # 创建自定义配置的 DataCache
        cache = DataCache(
            host='localhost',
            port=8124,  # 使用 Docker 端口
            database='pulse_trader',
            username='devuser',
            password='devpass',
            secure=False
        )

        print("✅ DataCache 初始化成功")

        # 1. 测试实时行情数据
        print("\n📊 测试实时行情数据...")
        test_quote = {
            'symbol': 'AAPL',
            'price': 150.25,
            'change': 1.25,
            'change_pct': 0.84,
            'volume': 1000000,
            'timestamp': datetime.now(),
            'bid_price': 150.20,
            'ask_price': 150.30
        }

        cache.save_realtime_quote(test_quote)
        print("✅ 实时行情数据保存成功")

        # 等待数据写入
        time.sleep(1)

        # 查询数据
        result = cache.get_latest_quotes(['AAPL'])
        if not result.empty:
            print(f"✅ 查询成功，价格: {result.iloc[0]['price']}")
        else:
            print("⚠️ 查询结果为空")

        # 2. 测试批量插入
        print("\n📈 测试批量数据插入...")
        quotes = []
        for i in range(5):
            quote = {
                'symbol': 'MSFT',
                'price': 300.0 + i,
                'change': i * 0.5,
                'change_pct': i * 0.1,
                'volume': 500000 + i * 1000,
                'timestamp': datetime.now(),
                'bid_price': 299.9 + i,
                'ask_price': 300.1 + i
            }
            quotes.append(quote)

        cache.batch_insert_quotes(quotes)
        print("✅ 批量数据插入成功")

        # 3. 测试策略信号
        print("\n🎯 测试策略信号...")
        cache.save_strategy_signal('momentum', 'AAPL', 1, 150.25)
        cache.save_strategy_signal('momentum', 'AAPL', -1, 152.00)
        print("✅ 策略信号保存成功")

        # 4. 测试交易记录
        print("\n💰 测试交易记录...")
        cache.save_trade_record('momentum', 'AAPL', 'buy', 150.25, 100, 1.5)
        cache.save_trade_record('momentum', 'AAPL', 'sell', 152.00, 100, 1.5)
        print("✅ 交易记录保存成功")

        # 5. 测试聚合数据
        print("\n📊 测试聚合数据查询...")
        # 创建更多数据用于聚合
        agg_quotes = []
        base_time = datetime.now() - timedelta(hours=1)

        for i in range(60):  # 1小时的分钟数据
            quote = {
                'symbol': 'GOOGL',
                'price': 2500.0 + (i % 10) * 5,
                'change': (i % 10) * 2,
                'change_pct': (i % 10) * 0.5,
                'volume': 200000 + i * 500,
                'timestamp': base_time + timedelta(minutes=i),
                'bid_price': 2499.0 + (i % 10) * 5,
                'ask_price': 2501.0 + (i % 10) * 5
            }
            agg_quotes.append(quote)

        cache.batch_insert_quotes(agg_quotes)
        time.sleep(1)

        # 查询聚合数据
        start_time = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        agg_result = cache.get_aggregated_data('GOOGL', '5m', start_time, end_time)
        if not agg_result.empty:
            print(f"✅ 聚合数据查询成功，{len(agg_result)} 条记录")
        else:
            print("⚠️ 聚合数据为空")

        # 6. 测试绩效统计
        print("\n📈 测试策略绩效统计...")
        performance = cache.get_strategy_performance('momentum')
        print(f"✅ 策略绩效: {performance}")

        cache.close()
        print("\n🎉 所有测试完成！DataCache 模块功能正常。")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🐳 ClickHouse DataCache Docker 测试")
    print("="*50)

    # 检查 Docker 容器状态
    print("\n1️⃣ 检查 Docker 容器状态...")
    try:
        import subprocess
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if 'clickhouse-test' in result.stdout:
            print("✅ ClickHouse Docker 容器正在运行")
        else:
            print("❌ ClickHouse Docker 容器未运行")
            return
    except:
        print("❌ 无法检查 Docker 容器状态")
        return

    # 测试连接
    if not test_docker_clickhouse():
        print("\n请确保 Docker 容器正确启动:")
        print("docker run -d --name clickhouse-test -p 8124:8123 \\")
        print("  -e CLICKHOUSE_DB=pulse_trader \\")
        print("  -e CLICKHOUSE_USER=devuser \\")
        print("  -e CLICKHOUSE_PASSWORD=devpass \\")
        print("  -e CLICKHOUSE_DEFAULT_ACCESS_MANAGEMENT=1 \\")
        print("  clickhouse/clickhouse-server:latest")
        return

    # 运行功能测试
    test_datacache_functionality()

if __name__ == "__main__":
    main()
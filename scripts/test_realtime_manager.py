"""
实时数据管理器测试脚本
"""
import sys
import os
import asyncio
sys.path.append('.')

from pulse_trader.data.realtime import RealtimeDataManager

async def test_realtime_manager():
    """测试实时数据管理器"""
    print("🚀 测试实时数据管理器...")

    manager = RealtimeDataManager()

    # 测试单只股票
    print("\n📈 获取单只股票实时数据...")
    quote = await manager.get_sina_quote("000001.SZ")
    if quote:
        print(f"股票代码: {quote.symbol}")
        print(f"当前价格: {quote.price}")
        print(f"涨跌幅: {quote.change_pct:+.2f}%")
        print(f"成交量: {quote.volume:,}")
    else:
        print("❌ 获取实时数据失败")
        return False

    # 测试多股票监控（5秒后停止）
    print("\n📊 开始多股票监控（5秒后自动停止）...")

    symbols = ["000001.SZ", "000002.SZ"]

    # 启动监控任务
    monitor_task = asyncio.create_task(
        manager.start_monitoring(symbols)
    )

    # 5秒后停止
    await asyncio.sleep(5)
    manager.stop_monitoring()

    # 等待监控任务结束
    await monitor_task

    print("✅ 实时数据管理器测试完成")
    return True

if __name__ == "__main__":
    asyncio.run(test_realtime_manager())
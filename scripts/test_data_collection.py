#!/usr/bin/env python3
"""
数据采集功能测试脚本
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import datetime, timedelta

from src.data.collectors.historical import HistoricalCollector
from src.data.collectors.realtime import RealtimeCollector
from src.data.collectors.stock_info import StockInfoCollector


def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🚀 开始测试数据采集功能...\n")

    # 1. 测试股票信息采集器
    print("=== 1. 测试股票信息采集器 ===")
    info_collector = StockInfoCollector()

    try:
        stock_list = info_collector.collect_stock_list()
        if stock_list is not None and not stock_list.empty:
            print(f"✅ 成功获取股票列表: {len(stock_list)} 只股票")
            print(f"   列名: {list(stock_list.columns)}")
            print(f"   示例数据:\n{stock_list.head(3)}")
        else:
            print("❌ 获取股票列表失败")
    except Exception as e:
        print(f"❌ 股票信息采集器测试异常: {e}")

    print()

    # 2. 测试实时行情采集器
    print("=== 2. 测试实时行情采集器 ===")
    realtime_collector = RealtimeCollector()

    try:
        # 测试市场概览
        market_overview = realtime_collector.collect_market_overview()
        if market_overview is not None and not market_overview.empty:
            print(f"✅ 成功获取市场概览: {len(market_overview)} 个指数")
            print(f"   数据列: {list(market_overview.columns)}")
            for _, row in market_overview.iterrows():
                print(
                    f"   - {row['index_name']}: {row.get('latest_price', 'N/A')} ({row.get('change_percent', 'N/A')}%)"
                )
        else:
            print("⚠️ 获取市场概览失败 - 可能是网络连接问题或数据源暂时不可用")
    except Exception as e:
        print(f"❌ 实时行情采集器测试异常: {e}")

    print()

    # 3. 测试历史数据采集器
    print("=== 3. 测试历史数据采集器 ===")
    historical_collector = HistoricalCollector()

    try:
        # 测试获取平安银行最近一个月的数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now().replace(day=1) - timedelta(days=1)).strftime(
            "%Y%m%d"
        )  # 上个月第一天

        daily_data = historical_collector.collect_daily_kline(
            "000001", start_date, end_date
        )
        if daily_data is not None and not daily_data.empty:
            print(f"✅ 成功获取历史数据: {len(daily_data)} 条记录")
            if "date" in daily_data.columns:
                print(
                    f"   数据时间范围: {daily_data['date'].min()} ~ {daily_data['date'].max()}"
                )
            else:
                print(f"   数据时间范围: 未知（无date列）")
            print(f"   列名: {list(daily_data.columns)}")
        else:
            print("⚠️ 获取历史数据失败 - 可能是网络连接问题或数据源暂时不可用")
    except Exception as e:
        print(f"❌ 历史数据采集器测试异常: {e}")

    print("\n🎉 数据采集功能测试完成！")


if __name__ == "__main__":
    main()

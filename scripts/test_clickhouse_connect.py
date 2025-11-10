#!/usr/bin/env python3
"""
ClickHouse DataCache 模块测试脚本

测试 pulse_trader.data.cache.DataCache 类的各项功能：
1. 数据库连接和初始化
2. 实时行情数据存储和查询
3. 日线数据存储和查询
4. 策略信号存储
5. 交易记录存储
6. 聚合数据查询
7. 批量操作性能测试
"""

import sys
import os
import time
import pandas as pd
from datetime import datetime, timedelta
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pulse_trader.data.cache import DataCache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCacheTester:
    """DataCache测试类"""

    def __init__(self):
        """初始化测试环境"""
        self.cache = None
        self.test_symbol = "AAPL"
        self.test_strategy = "momentum_strategy"

    def setup(self):
        """设置测试环境"""
        logger.info("🚀 初始化ClickHouse连接...")
        try:
            # 使用默认配置连接ClickHouse
            self.cache = DataCache(
                host='localhost',
                port=8123,
                database='pulse_trader',
                username='devuser',
                password='devpass',
                secure=False
            )
            logger.info("✅ ClickHouse连接成功")
            return True
        except Exception as e:
            logger.error(f"❌ ClickHouse连接失败: {e}")
            return False

    def cleanup(self):
        """清理测试环境"""
        if self.cache:
            self.cache.close()
            logger.info("🧹 数据库连接已关闭")

    def test_realtime_quotes(self) -> bool:
        """测试实时行情数据功能"""
        logger.info("📊 测试实时行情数据功能...")

        try:
            # 生成测试数据
            test_quotes = []
            base_time = datetime.now()

            for i in range(10):
                quote = {
                    'symbol': self.test_symbol,
                    'price': 150.0 + i * 0.1,
                    'change': i * 0.05,
                    'change_pct': i * 0.03,
                    'volume': 1000000 + i * 10000,
                    'timestamp': base_time + timedelta(seconds=i),
                    'bid_price': 149.9 + i * 0.1,
                    'ask_price': 150.1 + i * 0.1
                }
                test_quotes.append(quote)

            # 测试单条插入
            logger.info("  测试单条数据插入...")
            self.cache.save_realtime_quote(test_quotes[0])

            # 测试批量插入
            logger.info("  测试批量数据插入...")
            self.cache.batch_insert_quotes(test_quotes[1:])

            # 等待数据写入
            time.sleep(0.5)

            # 测试查询
            logger.info("  测试数据查询...")
            result_df = self.cache.get_latest_quotes([self.test_symbol])

            if not result_df.empty:
                logger.info(f"  ✅ 成功查询到 {len(result_df)} 条记录")
                logger.info(f"  最新价格: {result_df.iloc[0]['price']}")
                return True
            else:
                logger.error("  ❌ 未查询到数据")
                return False

        except Exception as e:
            logger.error(f"  ❌ 实时行情测试失败: {e}")
            return False

    def test_daily_data(self) -> bool:
        """测试日线数据功能"""
        logger.info("📈 测试日线数据功能...")

        try:
            # 生成测试日线数据
            dates = pd.date_range(
                start='2024-01-01',
                end='2024-01-10',
                freq='D'
            )

            data = pd.DataFrame({
                'date': dates,
                'open': [100 + i for i in range(len(dates))],
                'high': [105 + i for i in range(len(dates))],
                'low': [95 + i for i in range(len(dates))],
                'close': [102 + i for i in range(len(dates))],
                'volume': [1000000 + i * 10000 for i in range(len(dates))]
            })

            # 保存日线数据
            logger.info("  保存日线数据...")
            self.cache.save_daily_data(self.test_symbol, data)

            # 查询日线数据
            logger.info("  查询日线数据...")
            result = self.cache.get_daily_data(
                self.test_symbol,
                start_date='2024-01-01',
                end_date='2024-01-10'
            )

            if not result.empty:
                logger.info(f"  ✅ 成功查询到 {len(result)} 条日线记录")
                logger.info(f"  数据列: {list(result.columns)}")
                return True
            else:
                logger.error("  ❌ 未查询到日线数据")
                return False

        except Exception as e:
            logger.error(f"  ❌ 日线数据测试失败: {e}")
            return False

    def test_strategy_signals(self) -> bool:
        """测试策略信号功能"""
        logger.info("🎯 测试策略信号功能...")

        try:
            # 生成测试信号
            signals = [
                (self.test_strategy, self.test_symbol, 1, 150.5),  # 买入信号
                (self.test_strategy, self.test_symbol, 0, 151.0),  # 持有信号
                (self.test_strategy, self.test_symbol, -1, 152.3), # 卖出信号
            ]

            # 保存信号
            logger.info("  保存策略信号...")
            for strategy, symbol, signal, price in signals:
                self.cache.save_strategy_signal(strategy, symbol, signal, price)

            # 等待数据写入
            time.sleep(0.5)

            # 验证信号保存（通过查询策略信号表）
            logger.info("  验证信号保存...")
            query = f"""
                SELECT COUNT(*) as signal_count
                FROM pulse_trader.strategy_signals
                WHERE strategy_name = '{self.test_strategy}'
                AND symbol = '{self.test_symbol}'
            """

            result = self.cache.client.query(query)
            signal_count = result.result_rows[0][0]

            if signal_count >= 3:
                logger.info(f"  ✅ 成功保存 {signal_count} 个策略信号")
                return True
            else:
                logger.error(f"  ❌ 信号保存失败，期望3个，实际{signal_count}个")
                return False

        except Exception as e:
            logger.error(f"  ❌ 策略信号测试失败: {e}")
            return False

    def test_trade_records(self) -> bool:
        """测试交易记录功能"""
        logger.info("💰 测试交易记录功能...")

        try:
            # 生成测试交易记录
            trades = [
                (self.test_strategy, self.test_symbol, 'buy', 150.0, 100, 1.5),
                (self.test_strategy, self.test_symbol, 'sell', 155.0, 100, 1.5),
            ]

            # 保存交易记录
            logger.info("  保存交易记录...")
            for strategy, symbol, action, price, quantity, commission in trades:
                self.cache.save_trade_record(
                    strategy, symbol, action, price, quantity, commission
                )

            # 等待数据写入
            time.sleep(0.5)

            # 获取策略绩效
            logger.info("  获取策略绩效统计...")
            performance = self.cache.get_strategy_performance(self.test_strategy)

            if performance.get('total_trades', 0) >= 2:
                logger.info(f"  ✅ 策略绩效统计: {performance}")
                return True
            else:
                logger.error(f"  ❌ 交易记录保存失败: {performance}")
                return False

        except Exception as e:
            logger.error(f"  ❌ 交易记录测试失败: {e}")
            return False

    def test_aggregated_data(self) -> bool:
        """测试聚合数据功能"""
        logger.info("📊 测试聚合数据功能...")

        try:
            # 生成更多实时数据用于聚合测试
            base_time = datetime.now() - timedelta(hours=2)
            quotes = []

            for i in range(120):  # 2小时的分钟数据
                quote = {
                    'symbol': self.test_symbol,
                    'price': 150.0 + (i % 10) * 0.5,
                    'change': (i % 10) * 0.1,
                    'change_pct': (i % 10) * 0.05,
                    'volume': 100000 + i * 1000,
                    'timestamp': base_time + timedelta(minutes=i),
                    'bid_price': 149.9 + (i % 10) * 0.5,
                    'ask_price': 150.1 + (i % 10) * 0.5
                }
                quotes.append(quote)

            # 批量插入数据
            self.cache.batch_insert_quotes(quotes)
            time.sleep(1)

            # 测试不同间隔的聚合数据
            intervals = ['1h', '30m', '5m']

            for interval in intervals:
                logger.info(f"  测试 {interval} 聚合数据...")

                start_time = base_time.strftime('%Y-%m-%d %H:%M:%S')
                end_time = (base_time + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')

                agg_data = self.cache.get_aggregated_data(
                    self.test_symbol, interval, start_time, end_time
                )

                if not agg_data.empty:
                    logger.info(f"    ✅ {interval} 聚合数据: {len(agg_data)} 条记录")
                else:
                    logger.warning(f"    ⚠️  {interval} 聚合数据为空")

            return True

        except Exception as e:
            logger.error(f"  ❌ 聚合数据测试失败: {e}")
            return False

    def test_performance(self) -> bool:
        """测试性能"""
        logger.info("⚡ 测试批量操作性能...")

        try:
            # 生成大量测试数据
            batch_size = 1000
            quotes = []
            base_time = datetime.now()

            logger.info(f"  生成 {batch_size} 条测试数据...")
            for i in range(batch_size):
                quote = {
                    'symbol': f"TEST{i % 10}",  # 10个不同的股票
                    'price': 100.0 + (i % 100) * 0.1,
                    'change': (i % 20) * 0.05,
                    'change_pct': (i % 20) * 0.02,
                    'volume': 100000 + i * 100,
                    'timestamp': base_time + timedelta(seconds=i),
                    'bid_price': 99.9 + (i % 100) * 0.1,
                    'ask_price': 100.1 + (i % 100) * 0.1
                }
                quotes.append(quote)

            # 测试批量插入性能
            logger.info("  执行批量插入...")
            start_time = time.time()

            self.cache.batch_insert_quotes(quotes)

            insert_time = time.time() - start_time
            logger.info(f"  ✅ 批量插入 {batch_size} 条数据耗时: {insert_time:.3f}秒")
            logger.info(f"  插入速度: {batch_size/insert_time:.0f} 条/秒")

            # 测试查询性能
            logger.info("  执行查询性能测试...")
            start_time = time.time()

            result = self.cache.get_latest_quotes()

            query_time = time.time() - start_time
            logger.info(f"  ✅ 查询 {len(result)} 条数据耗时: {query_time:.3f}秒")

            return True

        except Exception as e:
            logger.error(f"  ❌ 性能测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🧪 开始运行 DataCache 模块完整测试...")

        # 测试项目列表
        tests = [
            ("实时行情数据", self.test_realtime_quotes),
            ("日线数据", self.test_daily_data),
            ("策略信号", self.test_strategy_signals),
            ("交易记录", self.test_trade_records),
            ("聚合数据", self.test_aggregated_data),
            ("性能测试", self.test_performance),
        ]

        # 运行测试
        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"开始测试: {test_name}")
            logger.info(f"{'='*50}")

            try:
                result = test_func()
                results.append((test_name, result))

                if result:
                    logger.info(f"✅ {test_name} 测试通过")
                else:
                    logger.error(f"❌ {test_name} 测试失败")

            except Exception as e:
                logger.error(f"❌ {test_name} 测试异常: {e}")
                results.append((test_name, False))

        # 输出测试总结
        logger.info(f"\n{'='*50}")
        logger.info("🏁 测试总结")
        logger.info(f"{'='*50}")

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")

        logger.info(f"\n总体结果: {passed}/{total} 项测试通过")

        if passed == total:
            logger.info("🎉 所有测试都通过了！DataCache模块工作正常。")
        else:
            logger.warning(f"⚠️  有 {total - passed} 项测试失败，请检查相关功能。")


def main():
    """主函数"""
    tester = DataCacheTester()

    try:
        # 设置测试环境
        if not tester.setup():
            logger.error("❌ 测试环境设置失败，退出测试")
            return

        # 运行所有测试
        tester.run_all_tests()

    except KeyboardInterrupt:
        logger.info("🛑 测试被用户中断")
    except Exception as e:
        logger.error(f"❌ 测试运行异常: {e}")
    finally:
        # 清理测试环境
        tester.cleanup()


if __name__ == "__main__":
    main()
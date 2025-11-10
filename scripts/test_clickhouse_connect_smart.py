#!/usr/bin/env python3
"""
智能 ClickHouse DataCache 测试脚本

自动检测可用的 ClickHouse 配置并运行测试
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


class SmartClickHouseTester:
    """智能 ClickHouse 测试器"""

    def __init__(self):
        """初始化测试环境"""
        self.cache = None
        self.test_symbol = "AAPL"
        self.test_strategy = "momentum_strategy"

    def find_working_config(self):
        """找到可用的 ClickHouse 配置"""
        logger.info("🔍 搜索可用的 ClickHouse 配置...")

        # 测试配置列表
        configs = [
            {
                'name': 'Docker 容器 (端口 8124)',
                'config': {
                    'host': 'localhost',
                    'port': 8124,
                    'database': 'pulse_trader',
                    'username': 'devuser',
                    'password': 'devpass',
                    'secure': False
                }
            },
            {
                'name': '本地 ClickHouse (devuser)',
                'config': {
                    'host': 'localhost',
                    'port': 8123,
                    'database': 'pulse_trader',
                    'username': 'devuser',
                    'password': 'devpass',
                    'secure': False
                }
            },
            {
                'name': '本地 ClickHouse (默认)',
                'config': {
                    'host': 'localhost',
                    'port': 8123,
                    'database': 'default',
                    'username': 'default',
                    'password': '',
                    'secure': False
                }
            }
        ]

        for item in configs:
            name, config = item['name'], item['config']
            logger.info(f"  测试: {name}")
            try:
                # 尝试连接
                test_cache = DataCache(**config)

                # 测试简单查询
                result = test_cache.client.query('SELECT 1 as test')
                test_result = result.result_rows[0][0]

                if test_result == 1:
                    logger.info(f"  ✅ {name} 连接成功")
                    test_cache.close()
                    return name, config
                else:
                    logger.warning(f"  ⚠️ {name} 查询结果异常")

                test_cache.close()

            except Exception as e:
                logger.warning(f"  ❌ {name} 失败: {str(e)[:100]}...")
                continue

        logger.error("❌ 没有找到可用的 ClickHouse 配置")
        return None, None

    def run_comprehensive_test(self):
        """运行全面测试"""
        logger.info("🧪 开始运行 DataCache 模块全面测试...")

        # 找到可用配置
        config_name, config = self.find_working_config()
        if not config:
            logger.error("❌ 无法找到可用的 ClickHouse 配置")
            return

        logger.info(f"使用配置: {config_name}")

        try:
            # 初始化 DataCache
            self.cache = DataCache(**config)
            logger.info("✅ DataCache 初始化成功")

            # 运行测试套件
            tests = [
                ("基础连接测试", self.test_basic_connection),
                ("实时行情数据", self.test_realtime_quotes),
                ("批量插入", self.test_batch_insert),
                ("策略信号", self.test_strategy_signals),
                ("交易记录", self.test_trade_records),
                ("策略绩效", self.test_strategy_performance),
                ("数据查询", self.test_data_queries),
            ]

            results = []
            for test_name, test_func in tests:
                logger.info(f"\n{'='*60}")
                logger.info(f"📋 测试: {test_name}")
                logger.info(f"{'='*60}")

                try:
                    start_time = time.time()
                    result = test_func()
                    duration = time.time() - start_time

                    status = "✅ 通过" if result else "❌ 失败"
                    logger.info(f"结果: {status} (耗时: {duration:.2f}秒)")
                    results.append((test_name, result, duration))

                except Exception as e:
                    logger.error(f"❌ {test_name} 异常: {e}")
                    results.append((test_name, False, 0))

            # 输出测试总结
            self.print_test_summary(results, config_name)

        finally:
            if self.cache:
                self.cache.close()

    def test_basic_connection(self) -> bool:
        """测试基础连接"""
        try:
            # 测试数据库连接
            result = self.cache.client.query('SELECT version() as version')
            version = result.result_rows[0][0]
            logger.info(f"  ClickHouse 版本: {version}")

            # 测试表存在
            tables = self.cache.client.query("SHOW TABLES FROM pulse_trader")
            table_names = [row[0] for row in tables.result_rows]
            logger.info(f"  数据表: {', '.join(table_names)}")

            return True
        except Exception as e:
            logger.error(f"  基础连接测试失败: {e}")
            return False

    def test_realtime_quotes(self) -> bool:
        """测试实时行情数据"""
        try:
            # 插入测试数据
            quote = {
                'symbol': self.test_symbol,
                'price': 150.25,
                'change': 1.25,
                'change_pct': 0.84,
                'volume': 1000000,
                'timestamp': datetime.now(),
                'bid_price': 150.20,
                'ask_price': 150.30
            }

            self.cache.save_realtime_quote(quote)
            logger.info("  ✅ 实时行情数据保存成功")

            # 查询数据
            time.sleep(0.5)  # 等待数据写入
            result = self.cache.get_latest_quotes([self.test_symbol])

            if not result.empty:
                logger.info(f"  ✅ 查询成功，价格: {result.iloc[0]['price']}")
                return True
            else:
                logger.warning("  ⚠️ 查询结果为空")
                return False

        except Exception as e:
            logger.error(f"  实时行情测试失败: {e}")
            return False

    def test_batch_insert(self) -> bool:
        """测试批量插入"""
        try:
            quotes = []
            for i in range(10):
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

            self.cache.batch_insert_quotes(quotes)
            logger.info(f"  ✅ 批量插入 {len(quotes)} 条数据成功")
            return True

        except Exception as e:
            logger.error(f"  批量插入测试失败: {e}")
            return False

    def test_strategy_signals(self) -> bool:
        """测试策略信号"""
        try:
            self.cache.save_strategy_signal('test_strategy', 'AAPL', 1, 150.25)
            self.cache.save_strategy_signal('test_strategy', 'AAPL', -1, 152.00)
            logger.info("  ✅ 策略信号保存成功")
            return True

        except Exception as e:
            logger.error(f"  策略信号测试失败: {e}")
            return False

    def test_trade_records(self) -> bool:
        """测试交易记录"""
        try:
            self.cache.save_trade_record('test_strategy', 'AAPL', 'buy', 150.25, 100, 1.5)
            self.cache.save_trade_record('test_strategy', 'AAPL', 'sell', 152.00, 100, 1.5)
            logger.info("  ✅ 交易记录保存成功")
            return True

        except Exception as e:
            logger.error(f"  交易记录测试失败: {e}")
            return False

    def test_strategy_performance(self) -> bool:
        """测试策略绩效"""
        try:
            performance = self.cache.get_strategy_performance('test_strategy')
            logger.info(f"  ✅ 策略绩效: {performance}")

            if performance.get('total_trades', 0) > 0:
                return True
            else:
                logger.warning("  ⚠️ 没有交易记录")
                return False

        except Exception as e:
            logger.error(f"  策略绩效测试失败: {e}")
            return False

    def test_data_queries(self) -> bool:
        """测试数据查询"""
        try:
            # 测试所有股票查询
            all_quotes = self.cache.get_latest_quotes()
            logger.info(f"  ✅ 查询所有股票: {len(all_quotes)} 条记录")

            # 测试特定股票查询
            aapl_quotes = self.cache.get_latest_quotes(['AAPL'])
            logger.info(f"  ✅ 查询 AAPL: {len(aapl_quotes)} 条记录")

            return True

        except Exception as e:
            logger.error(f"  数据查询测试失败: {e}")
            return False

    def print_test_summary(self, results, config_name):
        """打印测试总结"""
        logger.info(f"\n{'='*60}")
        logger.info("🏁 测试总结")
        logger.info(f"{'='*60}")

        logger.info(f"配置: {config_name}")

        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        total_time = sum(duration for _, _, duration in results)

        logger.info(f"\n测试结果:")
        for test_name, result, duration in results:
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name:<20} {status:<10} ({duration:.2f}s)")

        logger.info(f"\n总体统计:")
        logger.info(f"  通过率: {passed}/{total} ({passed/total*100:.1f}%)")
        logger.info(f"  总耗时: {total_time:.2f}秒")

        if passed == total:
            logger.info("\n🎉 所有测试都通过了！DataCache模块工作正常。")
            logger.info("✨ 你的量化交易数据缓存系统已准备就绪！")
        else:
            failed_count = total - passed
            logger.warning(f"\n⚠️  有 {failed_count} 项测试失败，请检查相关功能。")


def main():
    """主函数"""
    print("🚀 智能 ClickHouse DataCache 测试")
    print("="*60)
    print("自动检测可用的 ClickHouse 配置并运行全面测试")
    print("="*60)

    tester = SmartClickHouseTester()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
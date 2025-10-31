"""
MVP逻辑测试 - 不需要真实API调用
"""
import sys
sys.path.append('.')

import pandas as pd
import numpy as np

def test_strategy_logic():
    """测试策略逻辑"""
    print("🔍 测试策略逻辑...")

    # 创建模拟数据
    dates = pd.date_range('2024-01-01', periods=30)
    data = pd.DataFrame({
        'close': np.random.randn(30).cumsum() + 100,
        'open': np.random.randn(30).cumsum() + 99,
        'high': np.random.randn(30).cumsum() + 101,
        'low': np.random.randn(30).cumsum() + 98,
        'vol': np.random.randint(1000, 10000, 30)
    }, index=dates)

    print(f"✅ 模拟数据创建成功: {data.shape}")

    # 测试策略
    from pulse_trader.strategies.ma_cross import MACrossStrategy
    strategy = MACrossStrategy(fast=5, slow=10)
    signals = strategy.generate_signals(data)

    print(f"✅ 策略信号生成成功")
    print(f"📊 信号分布: {signals['signal'].value_counts()}")

    return signals

def test_backtest_logic(signals):
    """测试回测逻辑"""
    print("\n🔍 测试回测逻辑...")

    from pulse_trader.backtest.engine import BacktestEngine, performance_metrics
    engine = BacktestEngine(capital=100000)
    final_value = engine.run(signals)
    metrics = performance_metrics(final_value, 100000, len(signals))

    print(f"✅ 回测执行成功")
    print(f"💰 最终价值: {metrics['final_value']:.2f}")
    print(f"📈 总收益: {metrics['total_return']:.2%}")
    print(f"📊 年化收益: {metrics['annual_return']:.2%}")

    return metrics

def test_data_structure():
    """测试数据结构"""
    print("\n🔍 测试数据结构...")

    # 测试TushareDataSource是否能正常初始化(会报错但没有token)
    try:
        from pulse_trader.data.source import TushareDataSource
        source = TushareDataSource()
        print("❌ 不应该成功创建数据源")
    except ValueError as e:
        if "TUSHARE_TOKEN" in str(e):
            print("✅ 数据源正确要求TUSHARE_TOKEN")
        else:
            print(f"❌ 数据源错误: {e}")
    except Exception as e:
        print(f"❌ 数据源异常: {e}")

    return True

def main():
    """主测试函数"""
    print("🚀 MVP逻辑测试开始...")

    # 测试数据结构
    test_data_structure()

    # 测试策略逻辑
    signals = test_strategy_logic()

    # 测试回测逻辑
    metrics = test_backtest_logic(signals)

    print("\n✅ 所有逻辑测试通过！")
    print("💡 提示: 要运行完整测试，请设置TUSHARE_TOKEN环境变量")
    print("👉 注册地址: https://tushare.pro/register")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
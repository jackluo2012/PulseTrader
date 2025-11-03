import sys
import os
sys.path.append('.')

# 首先设置字体支持，确保中文正常显示
import matplotlib.pyplot as plt
try:
    from pulse_trader.utils.font_config import setup_chinese_fonts
    setup_chinese_fonts()
    # 强制设置全局字体
    plt.rcParams['font.family'] = ['sans-serif']
    plt.rcParams['font.sans-serif'] = [
        'WenQuanYi Micro Hei',  # 中文优先字体
        'DejaVu Sans',  # 英文和数字
        'WenQuanYi Zen Hei',
        'Noto Sans CJK SC',
        'Droid Sans Fallback',
        'Arial'
    ]
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    print("✅ 字体支持配置完成")
except ImportError:
    print("⚠️ 字体配置模块未找到，使用默认设置")

from pulse_trader.data.source import TushareDataSource
from pulse_trader.strategies.ma_cross import MACrossStrategy
from pulse_trader.backtest.engine import EnhancedBacktestEngine
from pulse_trader.backtest.metrics import PerformanceMetrics
from pulse_trader.analysis.visualization import BacktestVisualizer
import pandas as pd

def test_enhanced_backtest():
    """测试增强回测系统"""
    print("🚀 测试增强回测系统...")

    # 1. 获取数据
    print("\n📈 获取数据...")
    data_source = TushareDataSource()
    data = data_source.get_data("000001.SZ", "20240101", "20240630")
    print(f"数据形状: {data.shape}")

    # 2. 生成信号
    print("\n🎯 生成策略信号...")
    strategy = MACrossStrategy(fast=5, slow=20)
    signals = strategy.generate_signals(data)
    print(f"信号统计: 买入{len(signals[signals['signal']==1])}次, 卖出{len(signals[signals['signal']==-1])}次")

    # 3. 运行增强回测
    print("\n⚙️ 运行增强回测...")
    engine = EnhancedBacktestEngine(
        capital=100000,
        commission_rate=0.001,
        slippage_rate=0.001
    )
    final_value = engine.run(signals)

    # 4. 计算绩效指标
    print("\n📊 计算绩效指标...")
    equity_curve = engine.get_equity_curve()
    trades_df = engine.get_trades_df()
    metrics = PerformanceMetrics.calculate_all_metrics(
        equity_curve, trades_df, 100000
    )

    # 5. 输出结果
    print("\n📈 回测结果:")
    print(f"初始资金: {metrics['initial_capital']:,.0f}")
    print(f"最终价值: {metrics['final_value']:,.0f}")
    print(f"总收益: {metrics['total_return_pct']}")
    print(f"年化收益: {metrics['annual_return_pct']}")
    print(f"年化波动: {metrics['annual_volatility_pct']}")
    print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"最大回撤: {metrics['max_drawdown_pct']}")
    print(f"胜率: {metrics['win_rate_pct']}")
    print(f"交易次数: {metrics['total_trades']}")

    # 6. 生成可视化报告
    print("\n📊 生成可视化报告...")
    visualizer = BacktestVisualizer()
    visualizer.generate_report(equity_curve, trades_df, metrics)

    return True

if __name__ == "__main__":
    test_enhanced_backtest()
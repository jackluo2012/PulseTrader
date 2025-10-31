import sys, os
sys.path.append('.')

# 1. 测试数据获取
from pulse_trader.data.source import TushareDataSource
data_source = TushareDataSource()
data = data_source.get_data("000001.SZ", "20240101", "20240331")
print(f"数据形状: {data.shape}")

# 2. 测试策略
from pulse_trader.strategies.ma_cross import MACrossStrategy
strategy = MACrossStrategy()
signals = strategy.generate_signals(data)
print(f"信号分布: {signals['signal'].value_counts()}")

# 3. 测试回测
from pulse_trader.backtest.engine import BacktestEngine, performance_metrics
engine = BacktestEngine()
final_value = engine.run(signals)
metrics = performance_metrics(final_value, 100000, len(data))

print(f"总收益: {metrics['total_return']:.2%}")
print(f"年化收益: {metrics['annual_return']:.2%}")
print(f"最终价值: {metrics['final_value']:.2f}")
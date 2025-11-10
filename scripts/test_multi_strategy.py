"""
多策略管理器测试脚本
"""
import sys
import os
sys.path.append('.')

from pulse_trader.strategies.manager import MultiStrategyManager, StrategyConfig
from pulse_trader.strategies.ma_cross import MACrossStrategy
import asyncio

def test_multi_strategy_manager():
    """测试多策略管理器"""
    print("🚀 测试多策略管理器...")

    # 创建管理器
    manager = MultiStrategyManager(initial_capital=100000)

    # 创建策略配置
    ma_config = StrategyConfig(
        name="ma_cross_test",
        strategy_class="pulse_trader.strategies.ma_cross.MACrossStrategy",
        parameters={"fast": 5, "slow": 20},
        symbols=["000001.SZ"],
        capital_allocation=0.5,
        enabled=True
    )

    # 添加策略
    print("\n📈 添加策略...")
    manager.add_strategy(ma_config)
    print("✅ 策略添加成功")

    # 显示策略状态
    print("\n📊 策略状态:")
    for name, status in manager.strategy_status.items():
        print(f"策略: {name}")
        print(f"  运行状态: {status.is_running}")
        print(f"  分配资金: {manager.strategy_capital[name]:,.0f}")

    # 测试配置管理
    print("\n⚙️ 测试配置管理...")
    from pulse_trader.config.manager import ConfigManager

    config_manager = ConfigManager()
    system_config = config_manager.load_system_config()
    print(f"系统配置 - 初始资金: {system_config.initial_capital:,.0f}")

    strategy_configs = config_manager.load_strategy_configs()
    print(f"策略配置数量: {len(strategy_configs)}")

    print("✅ 多策略管理器测试完成")
    return True

if __name__ == "__main__":
    test_multi_strategy_manager()
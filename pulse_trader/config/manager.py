import yaml
import json
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import logging

@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    strategy_class: str
    parameters: Dict[str, Any]
    symbols: List[str]
    capital_allocation: float
    enabled: bool = True

@dataclass
class SystemConfig:
    """系统配置"""
    initial_capital: float = 100000
    commission_rate: float = 0.001
    update_interval: int = 5
    log_level: str = "INFO"
    cache_retention_days: int = 30

@dataclass
class DataSourceConfig:
    """数据源配置"""
    tushare_token: str = ""
    akshare_enabled: bool = True
    realtime_source: str = "sina"  # sina, tencent, eastmoney

@dataclass
class TradingConfig:
    """交易配置"""
    max_position_size: float = 0.2  # 单只股票最大仓位
    stop_loss_pct: float = 0.05     # 止损比例
    take_profit_pct: float = 0.10   # 止盈比例
    max_trades_per_day: int = 10    # 每日最大交易次数

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)

        # 配置文件路径
        self.main_config_path = self.config_dir / "trading_system.yaml"
        self.strategies_config_path = self.config_dir / "strategies.yaml"

        # 默认配置
        self._create_default_configs()

    def _create_default_configs(self):
        """创建默认配置文件"""

        # 主配置文件
        main_config = {
            'system': asdict(SystemConfig()),
            'data_source': asdict(DataSourceConfig()),
            'trading': asdict(TradingConfig()),
            'monitoring': {
                'enabled': True,
                'web_port': 8050,
                'refresh_interval': 5
            }
        }

        if not self.main_config_path.exists():
            with open(self.main_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(main_config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info("创建默认主配置文件")

        # 策略配置文件
        strategies_config = {
            'strategies': [
                {
                    'name': 'ma_cross_5_20',
                    'strategy_class': 'pulse_trader.strategies.ma_cross.MACrossStrategy',
                    'parameters': {'fast': 5, 'slow': 20},
                    'symbols': ['000001.SZ', '000002.SZ'],
                    'capital_allocation': 0.5,
                    'enabled': True
                },
                {
                    'name': 'ma_cross_10_30',
                    'strategy_class': 'pulse_trader.strategies.ma_cross.MACrossStrategy',
                    'parameters': {'fast': 10, 'slow': 30},
                    'symbols': ['000001.SZ', '000002.SZ'],
                    'capital_allocation': 0.3,
                    'enabled': False
                }
            ]
        }

        if not self.strategies_config_path.exists():
            with open(self.strategies_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(strategies_config, f, default_flow_style=False, allow_unicode=True)
            self.logger.info("创建默认策略配置文件")

    def load_system_config(self) -> SystemConfig:
        """加载系统配置"""
        with open(self.main_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return SystemConfig(**config['system'])

    def load_data_source_config(self) -> DataSourceConfig:
        """加载数据源配置"""
        with open(self.main_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return DataSourceConfig(**config['data_source'])

    def load_trading_config(self) -> TradingConfig:
        """加载交易配置"""
        with open(self.main_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return TradingConfig(**config['trading'])

    def load_strategy_configs(self) -> List[StrategyConfig]:
        """加载策略配置"""
        with open(self.strategies_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return [
            StrategyConfig(**strategy_config)
            for strategy_config in config['strategies']
        ]

    def save_strategy_configs(self, strategies: List[StrategyConfig]):
        """保存策略配置"""
        config = {
            'strategies': [asdict(strategy) for strategy in strategies]
        }

        with open(self.strategies_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        self.logger.info("策略配置已保存")

    def add_strategy(self, strategy: StrategyConfig):
        """添加策略配置"""
        strategies = self.load_strategy_configs()

        # 检查是否已存在同名策略
        for i, existing in enumerate(strategies):
            if existing.name == strategy.name:
                strategies[i] = strategy
                break
        else:
            strategies.append(strategy)

        self.save_strategy_configs(strategies)

    def remove_strategy(self, strategy_name: str):
        """删除策略配置"""
        strategies = self.load_strategy_configs()
        strategies = [s for s in strategies if s.name != strategy_name]
        self.save_strategy_configs(strategies)

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        with open(self.main_config_path, 'r', encoding='utf-8') as f:
            main_config = yaml.safe_load(f)

        with open(self.strategies_config_path, 'r', encoding='utf-8') as f:
            strategies_config = yaml.safe_load(f)

        return {
            'system': main_config.get('system', {}),
            'data_source': main_config.get('data_source', {}),
            'trading': main_config.get('trading', {}),
            'monitoring': main_config.get('monitoring', {}),
            'strategies': strategies_config.get('strategies', [])
        }
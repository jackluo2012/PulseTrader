import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel

from ..data.realtime import RealtimeDataManager, RealtimeQuote
from ..data.cache import DataCache

@dataclass
class StrategyConfig:
    """策略配置"""
    name: str
    strategy_class: str
    parameters: Dict[str, Any]
    symbols: List[str]
    capital_allocation: float  # 资金分配比例
    enabled: bool = True

@dataclass
class StrategyStatus:
    """策略状态"""
    name: str
    is_running: bool
    last_signal: Optional[datetime]
    total_signals: int
    current_positions: Dict[str, int]
    unrealized_pnl: float
    last_update: datetime


class MultiStrategyManager:
    """多策略管理器"""

    def __init__(self, initial_capital: float = 100000):
        self.console = Console()
        self.logger = logging.getLogger(__name__)

        # 核心组件
        self.realtime_manager = RealtimeDataManager()
        self.cache = DataCache()

        # 策略管理
        self.strategies: Dict[str, Any] = {}
        self.strategy_configs: Dict[str, StrategyConfig] = {}
        self.strategy_status: Dict[str, StrategyStatus] = {}

        # 资金管理
        self.initial_capital = initial_capital
        self.strategy_capital: Dict[str, float] = {}

        # 监控和调度
        self.is_running = False
        self.update_interval = 5  # 5秒更新一次

        # 事件回调
        self.signal_callbacks: List[Callable] = []

    def add_strategy(self, config: StrategyConfig):
        """添加策略"""
        try:
            # 动态导入策略类
            module_name, class_name = config.strategy_class.rsplit('.', 1)
            module = __import__(module_name, fromlist=[class_name])
            strategy_class = getattr(module, class_name)

            # 创建策略实例
            strategy = strategy_class(**config.parameters)

            # 保存策略
            self.strategies[config.name] = strategy
            self.strategy_configs[config.name] = config

            # 分配资金
            allocated_capital = self.initial_capital * config.capital_allocation
            self.strategy_capital[config.name] = allocated_capital

            # 初始化状态
            self.strategy_status[config.name] = StrategyStatus(
                name=config.name,
                is_running=False,
                last_signal=None,
                total_signals=0,
                current_positions={},
                unrealized_pnl=0.0,
                last_update=datetime.now()
            )

            self.logger.info(f"添加策略: {config.name}")

        except Exception as e:
            self.logger.error(f"添加策略失败 {config.name}: {e}")
            raise

    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            # 停止策略
            if self.strategy_status[strategy_name].is_running:
                self.stop_strategy(strategy_name)

            # 清理数据
            del self.strategies[strategy_name]
            del self.strategy_configs[strategy_name]
            del self.strategy_status[strategy_name]
            del self.strategy_capital[strategy_name]

            self.logger.info(f"移除策略: {strategy_name}")

    def start_strategy(self, strategy_name: str):
        """启动单个策略"""
        if strategy_name not in self.strategies:
            raise ValueError(f"策略不存在: {strategy_name}")

        config = self.strategy_configs[strategy_name]

        # 订阅实时数据
        for symbol in config.symbols:
            self.realtime_manager.subscribe(
                symbol,
                lambda quote, name=strategy_name: self._on_quote_update(name, quote)
            )

        # 更新状态
        self.strategy_status[strategy_name].is_running = True
        self.logger.info(f"启动策略: {strategy_name}")

    def stop_strategy(self, strategy_name: str):
        """停止单个策略"""
        if strategy_name in self.strategy_configs:
            config = self.strategy_configs[strategy_name]

            # 取消订阅
            for symbol in config.symbols:
                # 注意：这里需要改进unsubscribe方法来支持指定回调
                pass

            # 更新状态
            self.strategy_status[strategy_name].is_running = False
            self.logger.info(f"停止策略: {strategy_name}")

    def _on_quote_update(self, strategy_name: str, quote: RealtimeQuote):
        """处理实时行情更新"""
        try:
            if strategy_name not in self.strategies:
                return

            strategy = self.strategies[strategy_name]
            status = self.strategy_status[strategy_name]

            # 获取历史数据用于策略计算
            historical_data = self.cache.get_daily_data(
                quote.symbol,
                start_date=(datetime.now() - pd.Timedelta(days=60)).strftime('%Y%m%d')
            )

            if len(historical_data) < 20:  # 数据不足
                return

            # 生成策略信号
            signals = strategy.generate_signals(historical_data)
            if signals.empty:
                return

            current_signal = signals['signal'].iloc[-1]

            # 信号有变化时执行交易
            if current_signal != 0:
                self._execute_signal(strategy_name, quote.symbol, current_signal, quote.price)

                # 更新状态
                status.last_signal = datetime.now()
                status.total_signals += 1

                # 保存信号到缓存
                self.cache.save_strategy_signal(
                    strategy_name, quote.symbol, current_signal, quote.price
                )

                # 触发回调
                for callback in self.signal_callbacks:
                    try:
                        callback(strategy_name, quote.symbol, current_signal, quote.price)
                    except Exception as e:
                        self.logger.error(f"信号回调执行失败: {e}")

            # 更新状态
            status.last_update = datetime.now()

        except Exception as e:
            self.logger.error(f"处理行情更新失败 {strategy_name}: {e}")

    def _execute_signal(self, strategy_name: str, symbol: str, signal: int, price: float):
        """执行交易信号"""
        try:
            status = self.strategy_status[strategy_name]
            current_position = status.current_positions.get(symbol, 0)
            capital = self.strategy_capital[strategy_name]

            if signal == 1 and current_position == 0:  # 买入信号
                # 计算可买数量（使用90%资金）
                available_capital = capital * 0.9
                quantity = int(available_capital / price / 100) * 100  # 整手

                if quantity > 0:
                    # 更新持仓
                    status.current_positions[symbol] = quantity

                    # 保存交易记录
                    self.cache.save_trade_record(
                        strategy_name, symbol, 'buy', price, quantity, price * quantity * 0.001
                    )

                    self.console.print(f"[green]买入 {symbol} {quantity}股 @ {price:.2f}[/green]")

            elif signal == -1 and current_position > 0:  # 卖出信号
                # 卖出全部持仓
                quantity = current_position

                # 计算收益
                pnl = (price - self._get_avg_cost(strategy_name, symbol)) * quantity

                # 更新持仓
                status.current_positions[symbol] = 0
                status.unrealized_pnl += pnl

                # 保存交易记录
                self.cache.save_trade_record(
                    strategy_name, symbol, 'sell', price, quantity, price * quantity * 0.001
                )

                self.console.print(f"[red]卖出 {symbol} {quantity}股 @ {price:.2f}, 盈亏: {pnl:+.2f}[/red]")

        except Exception as e:
            self.logger.error(f"执行交易信号失败 {strategy_name}: {e}")

    def _get_avg_cost(self, strategy_name: str, symbol: str) -> float:
        """获取平均成本"""
        # 简化实现，实际应该从数据库查询
        return 0.0

    def start_all_strategies(self):
        """启动所有策略"""
        for strategy_name in self.strategies:
            if self.strategy_configs[strategy_name].enabled:
                self.start_strategy(strategy_name)

        self.is_running = True
        self.logger.info("所有策略已启动")

    def stop_all_strategies(self):
        """停止所有策略"""
        for strategy_name in list(self.strategies.keys()):
            self.stop_strategy(strategy_name)

        self.is_running = False
        self.realtime_manager.stop_monitoring()
        self.logger.info("所有策略已停止")

    async def run(self, symbols: List[str]):
        """运行多策略系统"""
        self.console.print("[bold green]🚀 启动多策略交易系统[/bold green]")

        # 启动所有策略
        self.start_all_strategies()

        # 开始监控行情
        monitor_task = asyncio.create_task(
            self.realtime_manager.start_monitoring(symbols)
        )

        # 状态显示任务
        display_task = asyncio.create_task(
            self._display_status_loop()
        )

        try:
            await asyncio.gather(monitor_task, display_task)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]接收到停止信号...[/yellow]")
        finally:
            self.stop_all_strategies()

    async def _display_status_loop(self):
        """状态显示循环"""
        while self.is_running:
            await asyncio.sleep(10)  # 每10秒刷新一次状态
            self._display_status()

    def _display_status(self):
        """显示策略状态"""
        self.console.clear()

        # 创建状态表格
        table = Table(title="策略运行状态")
        table.add_column("策略名称", style="cyan")
        table.add_column("运行状态", style="green")
        table.add_column("信号数量", justify="right")
        table.add_column("持仓数量", justify="right")
        table.add_column("未实现盈亏", justify="right", style="yellow")
        table.add_column("最后更新", style="blue")

        for status in self.strategy_status.values():
            status_color = "green" if status.is_running else "red"
            status_text = "运行中" if status.is_running else "已停止"

            pnl_color = "green" if status.unrealized_pnl >= 0 else "red"
            pnl_text = f"{status.unrealized_pnl:+.2f}"

            position_count = sum(status.current_positions.values())

            table.add_row(
                status.name,
                f"[{status_color}]{status_text}[/{status_color}]",
                str(status.total_signals),
                str(position_count),
                f"[{pnl_color}]{pnl_text}[/{pnl_color}]",
                status.last_update.strftime("%H:%M:%S")
            )

        self.console.print(table)

        # 显示总资金使用情况
        total_allocated = sum(self.strategy_capital.values())
        self.console.print(f"\n总资金: {self.initial_capital:,.0f}")
        self.console.print(f"已分配: {total_allocated:,.0f} ({total_allocated/self.initial_capital:.1%})")

    def add_signal_callback(self, callback: Callable):
        """添加信号回调函数"""
        self.signal_callbacks.append(callback)

    def get_strategy_performance(self, strategy_name: str = None) -> Dict[str, Any]:
        """获取策略绩效"""
        if strategy_name:
            return self.cache.get_strategy_performance(strategy_name)
        else:
            return {
                name: self.cache.get_strategy_performance(name)
                for name in self.strategies
            }    
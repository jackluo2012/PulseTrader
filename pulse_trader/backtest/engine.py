import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

class BacktestEngine:
    def __init__(self, capital=100000):

        """
        初始化回测引擎
        参数:
            capital (float): 初始资金，默认为100000
        """
        self.capital = capital  # 当前可用资金
        self.position = 0
        self.trades = []

    def run(self, data_with_signals):
        for date, row in data_with_signals.iterrows():
            price = row['close']
            signal = row['signal']

            if signal == 1 and self.position == 0:  # 买入
                shares = int(self.capital / price)
                self.position = shares
                self.capital = 0

            elif signal == -1 and self.position > 0:  # 卖出
                self.capital = self.position * price
                self.position = 0

        return self.capital + (self.position * data_with_signals['close'].iloc[-1])

def performance_metrics(final_value, initial_capital, days):
    total_return = (final_value - initial_capital) / initial_capital
    annual_return = (1 + total_return) ** (252 / days) - 1
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'final_value': final_value
    }
@dataclass
class Trade:
    """交易记录"""
    symbol: str
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    direction: str  # 'long' or 'short'
    pnl: float = 0.0
    commission: float = 0.0

@dataclass
class Position:
    """持仓信息"""
    symbol: str          # 交易品种代码
    quantity: int        # 持仓数量
    entry_price: float   # 开仓价格
    entry_date: datetime # 开仓日期
    direction: str           # 持仓方向(多头/空头)


class EnhancedBacktestEngine:
    """增强的回测引擎"""

    def __init__(self,
                 capital: float = 100000,
                 commission_rate: float = 0.001,  # 0.1% 手续费
                 slippage_rate: float = 0.001,    # 0.1% 滑点
                 min_commission: float = 5.0):    # 最低手续费5元    
        
        self.initial_capital = capital
        self.capital = capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.min_commission = min_commission

        self.position = {}  # 当前持仓
        self.trades: List[Trade] = []  # 所有交易记录
        self.daily_capital = []  # 每日资金记录
        self.positions_history = []  # 持仓历史
    
    def calculate_commission(self, amount: float) -> float:
        """计算手续费"""
        commission = amount * self.commission_rate
        return max(commission, self.min_commission)
    
    def apply_slippage(self, price: float, direction: str) -> float:
        """应用滑点"""
        slippage = price * self.slippage_rate
        if direction == 'buy':
            return price + slippage
        else:
            return price - slippage
        
    def execute_trade(self, symbol: str, direction: str, quantity: int,
                     price: float, date: datetime):
        """执行交易"""

        # 计算实际成交价格（包含滑点）
        actual_price = self.apply_slippage(price, direction)

        # 计算交易金额和手续费
        trade_amount = actual_price * quantity
        commission = self.calculate_commission(trade_amount)

        if direction == 'buy':
            # 买入
            total_cost = trade_amount + commission
            if self.capital >= total_cost:
                self.capital -= total_cost

                # 更新或创建持仓
                if symbol in self.position:
                    # 加仓
                    old_pos = self.position[symbol]
                    new_quantity = old_pos.quantity + quantity
                    new_price = (old_pos.quantity * old_pos.entry_price +
                               quantity * actual_price) / new_quantity
                    self.position[symbol] = Position(
                        symbol, new_quantity, new_price, date, 'long'
                    )
                else:
                    # 新建持仓
                    self.position[symbol] = Position(
                        symbol, quantity, actual_price, date, 'long'
                    )

                return True

        elif direction == 'sell':
            # 卖出
            if symbol in self.position and self.position[symbol].quantity >= quantity:
                # 计算收益
                total_proceeds = trade_amount - commission
                self.capital += total_proceeds

                # 记录交易
                pos = self.position[symbol]
                pnl = (actual_price - pos.entry_price) * quantity - commission

                trade = Trade(
                    symbol=symbol,
                    entry_date=pos.entry_date,
                    exit_date=date,
                    entry_price=pos.entry_price,
                    exit_price=actual_price,
                    quantity=quantity,
                    direction='long',
                    pnl=pnl,
                    commission=commission
                )
                self.trades.append(trade)

                # 更新持仓
                remaining_quantity = pos.quantity - quantity
                if remaining_quantity > 0:
                    self.position[symbol] = Position(
                        symbol, remaining_quantity, pos.entry_price,
                        pos.entry_date, 'long'
                    )
                else:
                    del self.position[symbol]

                return True

        return False        
    
    def run(self, data_with_signals: pd.DataFrame, symbol: str = "STOCK"):
        """运行回测"""
        signals = data_with_signals['signal']
        prices = data_with_signals['close']

        for date, (signal, price) in enumerate(zip(signals, prices)):
            current_date = data_with_signals.index[date]

            # 记录当前总资产
            position_value = sum(pos.quantity * price for pos in self.position.values())
            total_value = self.capital + position_value
            self.daily_capital.append({
                'date': current_date,
                'capital': self.capital,
                'position_value': position_value,
                'total_value': total_value,
                'position_count': len(self.position)
            })

            # 交易逻辑
            if signal == 1 and symbol not in self.position:  # 买入信号
                # 计算可买数量（使用90%资金避免过度杠杆）
                available_capital = self.capital * 0.9
                quantity = int(available_capital / price)

                if quantity > 0:
                    self.execute_trade(symbol, 'buy', quantity, price, current_date)

            elif signal == -1 and symbol in self.position:  # 卖出信号
                pos = self.position[symbol]
                self.execute_trade(symbol, 'sell', pos.quantity, price, current_date)

        # 最终清仓
        final_date = data_with_signals.index[-1]
        final_price = data_with_signals['close'].iloc[-1]

        for symbol_pos in list(self.position.keys()):
            pos = self.position[symbol_pos]
            self.execute_trade(symbol_pos, 'sell', pos.quantity, final_price, final_date)

        # 计算最终资产
        final_value = self.capital

        # 转换为DataFrame便于分析
        self.daily_capital = pd.DataFrame(self.daily_capital).set_index('date')

        return final_value
    
    def get_trades_df(self) -> pd.DataFrame:
        """获取交易记录DataFrame"""
        if not self.trades:
            return pd.DataFrame()

        trades_data = []
        for trade in self.trades:
            trades_data.append({
                'symbol': trade.symbol,
                'entry_date': trade.entry_date,
                'exit_date': trade.exit_date,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'commission': trade.commission,
                'return_pct': (trade.exit_price - trade.entry_price) / trade.entry_price
            })

        return pd.DataFrame(trades_data)
    
    def get_equity_curve(self) -> pd.DataFrame:
        """获取资金曲线"""
        return self.daily_capital.copy()
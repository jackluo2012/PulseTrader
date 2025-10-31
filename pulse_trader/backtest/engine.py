import pandas as pd

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
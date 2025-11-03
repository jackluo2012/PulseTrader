import pandas as pd
import numpy as np
from typing import Dict, Any

class PerformanceMetrics:
    """策略绩效指标计算"""

    @staticmethod
    def calculate_returns(equity_curve: pd.DataFrame) -> pd.Series:
        """计算日收益率"""
        return equity_curve['total_value'].pct_change().dropna()

    @staticmethod
    def total_return(final_value: float, initial_capital: float) -> float:
        """总收益率"""
        return (final_value - initial_capital) / initial_capital

    @staticmethod
    def annual_return(returns: pd.Series) -> float:
        """年化收益率"""
        if len(returns) == 0:
            return 0.0
        # total_days = len(returns)
        return (1 + returns.mean()) ** 252 - 1

    @staticmethod
    def annual_volatility(returns: pd.Series) -> float:
        """年化波动率"""
        if len(returns) == 0:
            return 0.0
        return returns.std() * np.sqrt(252)

    @staticmethod
    def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.03) -> float:
        """夏普比率"""
        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        excess_return = returns.mean() * 252 - risk_free_rate
        return excess_return / (returns.std() * np.sqrt(252))

    @staticmethod
    def max_drawdown(equity_curve: pd.DataFrame) -> Dict[str, Any]:
        """最大回撤"""
        values = equity_curve['total_value'].values
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak
        max_dd = drawdown.min()

        # 找到最大回撤期间
        max_dd_idx = drawdown.argmin()
        peak_idx = drawdown[:max_dd_idx].argmin()

        return {
            'max_drawdown': abs(max_dd),
            'max_drawdown_pct': f"{abs(max_dd):.2%}",
            'peak_date': equity_curve.index[peak_idx],
            'trough_date': equity_curve.index[max_dd_idx]
        }

    @staticmethod
    def win_rate(trades_df: pd.DataFrame) -> Dict[str, Any]:
        """胜率统计"""
        if trades_df.empty:
            return {'win_rate': 0, 'total_trades': 0}

        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]

        return {
            'win_rate': len(winning_trades) / len(trades_df),
            'win_rate_pct': f"{len(winning_trades) / len(trades_df):.1%}",
            'total_trades': len(trades_df),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum())
                           if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else float('inf')
        }

    @staticmethod
    def calculate_all_metrics(equity_curve: pd.DataFrame,
                            trades_df: pd.DataFrame,
                            initial_capital: float) -> Dict[str, Any]:
        """计算所有指标"""

        returns = PerformanceMetrics.calculate_returns(equity_curve)
        final_value = equity_curve['total_value'].iloc[-1]

        metrics = {
            # 基础收益指标
            'initial_capital': initial_capital,
            'final_value': final_value,
            'total_return': PerformanceMetrics.total_return(final_value, initial_capital),
            'total_return_pct': f"{PerformanceMetrics.total_return(final_value, initial_capital):.2%}",
            'annual_return': PerformanceMetrics.annual_return(returns),
            'annual_return_pct': f"{PerformanceMetrics.annual_return(returns):.2%}",

            # 风险指标
            'annual_volatility': PerformanceMetrics.annual_volatility(returns),
            'annual_volatility_pct': f"{PerformanceMetrics.annual_volatility(returns):.2%}",
            'sharpe_ratio': PerformanceMetrics.sharpe_ratio(returns),

            # 回撤指标
            **PerformanceMetrics.max_drawdown(equity_curve),

            # 交易统计
            **PerformanceMetrics.win_rate(trades_df)
        }

        return metrics
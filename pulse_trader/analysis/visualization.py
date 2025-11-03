import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from typing import Dict, Any, Optional
import numpy as np
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from typing import Dict, Any, Optional
import numpy as np
import sys
import os

# 导入虚拟环境字体管理器
try:
    from pulse_trader.utils.font_config import setup_chinese_fonts
    font_setup_success = setup_chinese_fonts()
except ImportError:
    print("⚠️ 无法导入字体配置模块，使用默认字体设置")
    font_setup_success = False
    # 基础字体设置
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
    plt.rcParams['axes.unicode_minus'] = False


class BacktestVisualizer:
    """回测可视化工具"""

    def __init__(self, style: str = 'seaborn-v0_8'):
        plt.style.use(style)
        self.colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

        # 尝试加载系统中的 CJK 字体（Noto / WenQuanYi 等）
        try:
            system_fonts = fm.findSystemFonts()
        except Exception:
            system_fonts = []

        loaded = []
        for font_path in system_fonts:
            try:
                lower = os.path.basename(font_path).lower()
                if any(k in lower for k in ('noto', 'cjk', 'wqy', 'wenquan', 'droid', 'fallback')):
                    fm.fontManager.addfont(font_path)
                    fp = fm.FontProperties(fname=font_path)
                    name = fp.get_name()
                    loaded.append(name)
            except Exception:
                continue

        # 构建优先字体列表
        sans_list = []
        # 优先使用已加载的中文字体
        for n in loaded:
            if n not in sans_list:
                sans_list.append(n)

        # 常用回退字体
        for fallback in ('DejaVu Sans', 'Arial', 'Liberation Sans'):
            if fallback not in sans_list:
                sans_list.append(fallback)

        if sans_list:
            plt.rcParams['font.family'] = ['sans-serif']
            plt.rcParams['font.sans-serif'] = sans_list
            plt.rcParams['axes.unicode_minus'] = False
            print(f"✅ matplotlib 字体配置：{sans_list}")
        else:
            print("⚠️ 未找到可用的 CJK 字体，中文显示可能出问题")

    def plot_equity_curve(self, equity_curve: pd.DataFrame,
                         save_path: Optional[str] = None):
        """绘制资金曲线"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 资金曲线
        ax1.plot(equity_curve.index, equity_curve['total_value'],
                 color=self.colors[0], linewidth=2, label='总资产')
        ax1.plot(equity_curve.index, equity_curve['capital'],
                 color=self.colors[1], linewidth=1, alpha=0.7, label='可用资金')
        ax1.plot(equity_curve.index, equity_curve['position_value'],
                 color=self.colors[2], linewidth=1, alpha=0.7, label='持仓价值')

        ax1.set_title('资金曲线', fontsize=16, fontweight='bold')
        ax1.set_ylabel('资产价值', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 持仓数量
        ax2.plot(equity_curve.index, equity_curve['position_count'],
                 color=self.colors[3], linewidth=2)
        ax2.fill_between(equity_curve.index, equity_curve['position_count'],
                         alpha=0.3, color=self.colors[3])
        ax2.set_title('持仓数量', fontsize=14)
        ax2.set_ylabel('持仓数量', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_strategy_signals(self, data_with_signals: pd.DataFrame,
                              save_path: Optional[str] = None):
        """绘制策略信号"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 价格和移动平均线
        ax1.plot(data_with_signals.index, data_with_signals['close'],
                 color=self.colors[0], linewidth=2, label='收盘价')
        ax1.plot(data_with_signals.index, data_with_signals['ma_fast'],
                 color=self.colors[1], linewidth=1.5, label='快速均线')
        ax1.plot(data_with_signals.index, data_with_signals['ma_slow'],
                 color=self.colors[2], linewidth=1.5, label='慢速均线')

        # 买卖信号
        buy_signals = data_with_signals[data_with_signals['signal'] == 1]
        sell_signals = data_with_signals[data_with_signals['signal'] == -1]

        ax1.scatter(buy_signals.index, buy_signals['close'],
                    color='green', marker='^', s=100, label='买入信号', zorder=5)
        ax1.scatter(sell_signals.index, sell_signals['close'],
                    color='red', marker='v', s=100, label='卖出信号', zorder=5)

        ax1.set_title('价格与交易信号', fontsize=16, fontweight='bold')
        ax1.set_ylabel('价格', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 信号图
        ax2.plot(data_with_signals.index, data_with_signals['signal'],
                 color=self.colors[3], linewidth=1.5)
        ax2.fill_between(data_with_signals.index, data_with_signals['signal'],
                         alpha=0.3, color=self.colors[3])
        ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax2.set_title('交易信号', fontsize=14)
        ax2.set_ylabel('信号', fontsize=12)
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_yticks([-1, 0, 1])
        ax2.set_yticklabels(['卖出', '持有', '买入'])
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_drawdown(self, equity_curve: pd.DataFrame,
                      save_path: Optional[str] = None):
        """绘制回撤图"""
        # 计算回撤
        values = equity_curve['total_value'].values
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak * 100

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.fill_between(equity_curve.index, drawdown, 0,
                        color='red', alpha=0.3, label='回撤')
        ax.plot(equity_curve.index, drawdown, color='red', linewidth=1)

        # 标记最大回撤
        max_dd_idx = drawdown.argmin()
        ax.scatter(equity_curve.index[max_dd_idx], drawdown[max_dd_idx],
                   color='darkred', s=100, zorder=5)
        ax.annotate(f'最大回撤: {drawdown[max_dd_idx]:.2f}%',
                    xy=(equity_curve.index[max_dd_idx], drawdown[max_dd_idx]),
                    xytext=(10, 10), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

        ax.set_title('策略回撤分析', fontsize=16, fontweight='bold')
        ax.set_ylabel('回撤 (%)', fontsize=12)
        ax.set_xlabel('日期', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def plot_returns_distribution(self, equity_curve: pd.DataFrame,
                                  save_path: Optional[str] = None):
        """绘制收益率分布"""
        returns = equity_curve['total_value'].pct_change().dropna() * 100

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # 收益率直方图
        ax1.hist(returns, bins=30, color=self.colors[0], alpha=0.7, edgecolor='black')
        ax1.axvline(returns.mean(), color='red', linestyle='--',
                    label=f'均值: {returns.mean():.2f}%')
        ax1.set_title('日收益率分布', fontsize=14, fontweight='bold')
        ax1.set_xlabel('收益率 (%)', fontsize=12)
        ax1.set_ylabel('频次', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Q-Q图
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('收益率Q-Q图', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def generate_report(self, equity_curve: pd.DataFrame,
                        trades_df: pd.DataFrame,
                        metrics: Dict[str, Any],
                        save_dir: str = "reports"):
        """生成完整的可视化报告"""
        import os
        os.makedirs(save_dir, exist_ok=True)

        # 生成各个图表
        self.plot_equity_curve(equity_curve, f"{save_dir}/equity_curve.png")

        # 跳过策略信号图，因为原始数据不在当前范围内
        # self.plot_strategy_signals(...)  # 需要原始数据

        self.plot_drawdown(equity_curve, f"{save_dir}/drawdown.png")
        self.plot_returns_distribution(equity_curve, f"{save_dir}/returns_dist.png")

        print(f"📊 可视化报告已生成到 {save_dir}/ 目录")
        print("  - equity_curve.png: 资金曲线")
        print("  - drawdown.png: 回撤分析")
        print("  - returns_dist.png: 收益率分布")
        print("  - strategy_signals.png: 已跳过（需要原始策略数据）")
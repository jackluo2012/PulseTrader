# PulseTrader - A股量化交易系统

## 项目简介

PulseTrader是一个专注于A股市场的量化交易系统，旨在学习和实践量化交易的核心概念和技术。本项目采用**Rust+Python混合架构**，结合Rust的高性能计算能力和Python的灵活开发生态，支持从数据获取到策略回测的完整量化交易流程。

## 🚀 技术特色

### Rust+Python混合架构
- **Rust核心引擎**: 高性能数据处理、技术指标计算、风险管理
- **Python接口层**: 灵活的策略开发、数据可视化、机器学习
- **零拷贝数据传递**: 最大化性能，最小化开销
- **内存安全**: Rust提供编译时安全保证

## 核心特性

### 🔄 数据管理
- 支持多数据源（AKShare、Tushare、Yahoo Finance）
- 自动数据清洗和质量验证
- 灵活的数据存储方案
- 实时数据更新机制

### 📊 技术指标库
- 完整的技术指标实现（趋势、动量、成交量、波动率）
- 自定义指标支持
- 指标组合和信号生成
- 高效的批量计算

### 🎯 策略开发
- 灵活的策略框架
- 多种经典策略模板
- 策略组合和优化
- 参数自动调优

### 🔬 回测系统
- 向量回测引擎
- 事件回测引擎
- 详细的性能分析
- 丰富的可视化图表

### ⚠️ 风险管理
- 实时风险监控
- 仓位管理
- 止损止盈控制
- VaR风险计算

## 项目结构

```
PulseTrader/
├── core/                   # Rust核心引擎
│   ├── src/
│   │   ├── lib.rs         # 库入口
│   │   ├── data/          # 高性能数据处理
│   │   ├── indicators/    # 技术指标计算
│   │   ├── risk/          # 风险管理
│   │   ├── execution/     # 交易执行
│   │   └── ffi/           # Python FFI接口
│   ├── Cargo.toml         # Rust依赖配置
│   └── build.rs           # 构建脚本
├── python/                # Python接口层
│   ├── pulse_trader/      # Python包
│   │   ├── core/          # 核心接口封装
│   │   ├── strategies/    # 策略开发框架
│   │   ├── backtest/      # 回测系统
│   │   ├── analysis/      # 数据分析工具
│   │   └── utils/         # 工具函数
│   ├── setup.py           # 构建配置
│   ├── pyproject.toml     # 项目配置
│   └── requirements.txt   # Python依赖
├── data/                  # 数据目录
│   ├── raw/              # 原始数据
│   ├── processed/        # 处理后数据
│   └── storage/          # 数据库存储
├── config/               # 配置文件
├── tests/                # 测试模块
│   ├── rust/             # Rust单元测试
│   └── python/           # Python集成测试
├── docs/                 # 项目文档
├── notebooks/            # Jupyter研究笔记本
└── examples/             # 使用示例
```

## 快速开始

### 1. 环境准备

```bash
# 安装Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# 克隆项目
git clone https://github.com/your-username/PulseTrader.git
cd PulseTrader

# 创建Python虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装Python依赖
pip install -r python/requirements.txt
pip install maturin  # Rust+Python构建工具
```

### 2. 配置设置

```bash
# 复制配置文件模板
cp config/config.yaml.example config/config.yaml
cp config/.env.example config/.env

# 编辑配置文件
# 设置数据源API密钥（如Tushare）
# 配置数据库连接
# 设置交易参数
```

### 3. 构建项目

```bash
# 编译Rust核心模块
cd core
cargo build --release

# 构建Python扩展
cd ..
maturin develop --release
```

### 4. 运行示例

```python
# 高性能示例：使用Rust+Python混合架构
from pulse_trader.core import DataEngine, TechnicalIndicators
from pulse_trader.strategies import MACrossStrategy
from pulse_trader.backtest import BacktestEngine

# 使用Rust高性能数据引擎
data_engine = DataEngine("000001.SZ")
data_engine.load_data("data/000001.SZ.csv")

# 使用Rust计算技术指标（极高性能）
prices = data_engine.get_prices()
sma_5 = TechnicalIndicators.sma(prices, 5)
sma_20 = TechnicalIndicators.sma(prices, 20)
rsi = TechnicalIndicators.rsi(prices, 14)

# 创建Python策略（灵活开发）
strategy = MACrossStrategy(short_window=5, long_window=20)
df = data_engine.get_dataframe()
df = strategy.calculate_indicators(df)

# 运行高性能回测
engine = BacktestEngine(initial_capital=1000000)
results = engine.run_backtest(strategy, df)

# 查看结果
print(f"总收益率: {results.total_return:.2%}")
print(f"夏普比率: {results.sharpe_ratio:.2f}")
print(f"最大回撤: {results.max_drawdown:.2%}")
```

## 技术栈

### Rust核心技术
- **Rust 1.70+**: 高性能系统编程
- **tokio**: 异步运行时
- **rayon**: 数据并行计算
- **polars**: 高性能数据处理
- **ndarray**: 多维数组计算
- **pyo3**: Python绑定

### Python生态
- **Python 3.8+**: 策略开发和数据分析
- **pandas/numpy**: 数据处理和分析
- **matplotlib/plotly**: 数据可视化
- **scikit-learn**: 机器学习
- **jupyter**: 研究和开发环境

### 数据源
- **akshare**: 免费A股数据
- **tushare**: 专业金融数据
- **yfinance**: 国际市场数据

### 存储和计算
- **SQLite/MySQL**: 数据存储
- **HDF5/Parquet**: 大数据文件格式
- **Redis**: 缓存和实时数据

## 开发指南

### 1. 项目设置

详细的开发环境搭建请参考：[开发环境搭建指南](docs/03-开发环境.md)

### 2. Rust+Python混合架构

了解混合架构设计：[Rust+Python混合架构文档](docs/09-Rust-Python混合架构.md)

### 3. 数据获取

了解如何获取和管理市场数据：[数据获取指南](docs/04-数据获取.md)

### 4. 策略开发

学习如何开发自己的交易策略：[策略开发教程](docs/05-策略开发.md)

### 5. 技术指标

查看完整的技术指标库：[技术指标文档](docs/06-技术指标库.md)

### 6. 风险管理

了解风险管理框架：[风险管理文档](docs/07-风险管理.md)

### 7. 回测系统

学习如何使用回测系统：[回测系统文档](docs/08-回测系统.md)

## 使用示例

### 示例1：高性能双均线策略

```python
from pulse_trader.core import DataEngine, TechnicalIndicators
from pulse_trader.strategies import MACrossStrategy
from pulse_trader.backtest import BacktestEngine

# 使用Rust引擎加载数据（高性能）
data_engine = DataEngine("000001.SZ")
data_engine.load_data("data/000001.SZ.csv")
df = data_engine.get_dataframe()

# Rust计算技术指标（极速计算）
prices = df['close'].tolist()
indicators_df = TechnicalIndicators.calculate_all_indicators(prices)
df = pd.concat([df, indicators_df], axis=1)

# Python策略开发（灵活便捷）
strategy = MACrossStrategy(short_window=5, long_window=20)

# Rust+Python混合回测（高性能+灵活性）
engine = BacktestEngine(initial_capital=1000000, commission=0.001)
results = engine.run_backtest(strategy, df)

print(f"总收益率: {results.total_return:.2%}")
print(f"夏普比率: {results.sharpe_ratio:.2f}")
```

### 示例2：实时风险管理

```python
from pulse_trader.core import RiskManager, ExecutionEngine
from pulse_trader.strategies import RSIStrategy
import time

# Rust风险管理器（实时风险监控）
risk_manager = RiskManager(max_position_size=0.2, max_portfolio_risk=0.8)
execution_engine = ExecutionEngine()

# Python RSI策略
strategy = RSIStrategy(rsi_window=14, oversold=30, overbought=70)

# 模拟实时交易
while True:
    # 获取实时数据（Python）
    current_data = get_market_data()

    # 生成信号（Python）
    signals = strategy.generate_signals(current_data)

    # 风险检查（Rust）
    positions = execution_engine.get_all_positions()
    portfolio_value = calculate_portfolio_value(positions, current_data)

    is_safe = risk_manager.check_risk_limits(
        list(positions.values()),
        portfolio_value
    )

    # 执行交易（Rust+Python）
    if is_safe and signals:
        for signal in signals:
            if risk_manager.validate_signal(signal):
                execute_order_with_risk_control(signal, risk_manager, execution_engine)

    time.sleep(1)  # 1秒检查一次
```

### 示例3：多策略高性能回测

```python
from pulse_trader.core import DataEngine, TechnicalIndicators
from pulse_trader.strategies import MACrossStrategy, RSIStrategy, PortfolioStrategy
from pulse_trader.backtest import BacktestEngine
import concurrent.futures

# Rust并行数据加载
def load_data_parallel(symbols):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for symbol in symbols:
            engine = DataEngine(symbol)
            future = executor.submit(lambda s=engine: s.load_data(f"data/{s.symbol}.csv"))
            futures.append(future)

        results = [f.result() for f in futures]

    return results

# 批量回测
symbols = ["000001.SZ", "000002.SZ", "000858.SZ"]
data_engines = load_data_parallel(symbols)

# 创建多策略组合
strategies = [
    MACrossStrategy(short_window=5, long_window=20),
    RSIStrategy(rsi_window=14, oversold=30, overbought=70)
]

portfolio_strategy = PortfolioStrategy(strategies, weights=[0.6, 0.4])

# 高性能回测（Rust计算+Python策略）
for i, engine in enumerate(data_engines):
    df = engine.get_dataframe()

    # Rust批量计算指标
    prices = df['close'].tolist()
    indicators_df = TechnicalIndicators.calculate_all_indicators(prices)
    df = pd.concat([df, indicators_df], axis=1)

    # 运行组合策略
    backtest_engine = BacktestEngine(initial_capital=1000000)
    results = backtest_engine.run_backtest(portfolio_strategy, df)

    print(f"{symbols[i]} - 收益率: {results.total_return:.2%}, 夏普比率: {results.sharpe_ratio:.2f}")
```

## 文档结构

- [01-项目概述](docs/01-项目概述.md) - 项目简介和目标
- [02-技术架构](docs/02-技术架构.md) - 系统架构设计
- [03-开发环境](docs/03-开发环境.md) - 环境搭建指南
- [04-数据获取](docs/04-数据获取.md) - 数据获取和管理
- [05-策略开发](docs/05-策略开发.md) - 策略开发教程
- [06-技术指标库](docs/06-技术指标库.md) - 技术指标实现
- [07-风险管理](docs/07-风险管理.md) - 风险管理框架
- [08-回测系统](docs/08-回测系统.md) - 回测引擎说明
- [09-Rust+Python混合架构](docs/09-Rust-Python混合架构.md) - 混合架构设计

## 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发规范

- 遵循 PEP 8 代码规范
- 添加适当的测试
- 更新相关文档
- 确保所有测试通过

## 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=core --cov-report=html

# 运行特定测试
pytest tests/test_strategies.py
```

## 路线图

### 第一阶段（已完成）
- [x] 基础架构设计
- [x] 数据获取模块
- [x] 基础技术指标
- [x] 简单策略框架
- [x] 基础回测引擎

### 第二阶段（开发中）
- [ ] 完整技术指标库
- [ ] 高级策略模板
- [ ] 风险管理系统
- [ ] 性能分析工具
- [ ] 可视化组件

### 第三阶段（计划中）
- [ ] 实盘交易接口
- [ ] 机器学习策略
- [ ] 多资产支持
- [ ] 分布式回测
- [ ] Web界面

### 第四阶段（未来）
- [ ] 移动端应用
- [ ] 云端部署
- [ ] 社区策略市场
- [ ] 专业版功能

## 常见问题

### Q: 如何申请Tushare的token？
A: 访问 [Tushare官网](https://tushare.pro/) 注册账户后，在个人中心可以获取API token。

### Q: 支持哪些券商接口？
A: 目前支持模拟交易，实盘接口正在开发中，计划支持主流券商。

### Q: 如何自定义技术指标？
A: 继承 `Indicator` 基类并实现 `calculate` 方法即可创建自定义指标。

### Q: 回测结果是否可靠？
A: 回测结果仅供参考，实际交易中需要考虑滑点、流动性等因素。建议进行充分的样本外测试。

## 免责声明

本项目仅供学习和研究使用，不构成投资建议。量化交易存在风险，实盘交易需要谨慎。开发者不对使用本系统造成的任何损失承担责任。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页: https://github.com/your-username/PulseTrader
- 问题反馈: https://github.com/your-username/PulseTrader/issues
- 邮箱: your-email@example.com

## 致谢

感谢以下开源项目：
- [AKShare](https://github.com/akfamily/akshare) - 金融数据获取
- [pandas](https://pandas.pydata.org/) - 数据分析
- [matplotlib](https://matplotlib.org/) - 数据可视化
- [backtrader](https://www.backtrader.com/) - 回测框架参考

---

**Happy Trading! 📈**

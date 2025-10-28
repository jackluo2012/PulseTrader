# Rust+Python混合架构设计

## 架构概述

本项目采用Rust+Python混合架构，结合两种语言的优势：
- **Rust**: 提供高性能、内存安全的核心计算引擎
- **Python**: 提供灵活易用的策略开发和数据分析接口

## 技术选型

### Rust核心依赖
```toml
[dependencies]
# 性能计算
ndarray = "0.15"
rayon = "1.5"           # 并行计算
polars = "0.25"         # 高性能数据处理
tokio = "1.0"           # 异步运行时

# FFI接口
pyo3 = { version = "0.18", features = ["extension-module"] }
numpy = "0.18"

# 数据序列化
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# 网络和数据库
reqwest = { version = "0.11", features = ["json"] }
sqlx = { version = "0.6", features = ["runtime-tokio-rustls", "mysql", "sqlite"] }

# 数学计算
num-complex = "0.4"
statrs = "0.16"
```

### Python接口依赖
```python
# 数据处理
pandas >= 1.3.0
numpy >= 1.21.0
polars >= 0.15.0

# 可视化
matplotlib >= 3.4.0
plotly >= 5.0.0
seaborn >= 0.11.0

# 机器学习
scikit-learn >= 1.0.0
tensorflow >= 2.8.0

# 开发工具
jupyter >= 1.0.0
pytest >= 6.2.0
black >= 21.0.0
```

## 项目结构

```
PulseTrader/
├── core/                   # Rust核心模块
│   ├── src/
│   │   ├── lib.rs         # 库入口
│   │   ├── data/          # 数据处理模块
│   │   ├── indicators/    # 技术指标
│   │   ├── risk/          # 风险管理
│   │   ├── execution/     # 交易执行
│   │   └── ffi/           # FFI接口
│   ├── Cargo.toml
│   └── build.rs
├── python/                # Python接口层
│   ├── pulse_trader/      # Python包
│   │   ├── __init__.py
│   │   ├── core/          # 核心接口
│   │   ├── strategies/    # 策略模块
│   │   ├── backtest/      # 回测系统
│   │   ├── analysis/      # 分析工具
│   │   └── utils/         # 工具函数
│   ├── setup.py
│   ├── pyproject.toml
│   └── requirements.txt
├── data/                  # 数据目录
├── config/                # 配置文件
├── docs/                  # 文档
├── tests/                 # 测试
│   ├── rust/              # Rust测试
│   └── python/            # Python测试
└── notebooks/             # Jupyter笔记本
```

## Rust核心模块设计

### 1. 数据处理引擎

```rust
// core/src/data/mod.rs
use ndarray::{Array1, Array2};
use polars::prelude::*;
use pyo3::prelude::*;

#[pyclass]
pub struct DataEngine {
    #[pyo3(get)]
    symbol: String,
    data: DataFrame,
}

#[pymethods]
impl DataEngine {
    #[new]
    pub fn new(symbol: String) -> Self {
        Self {
            symbol,
            data: DataFrame::empty(),
        }
    }

    pub fn load_data(&mut self, csv_path: &str) -> PyResult<()> {
        let df = CsvReader::from_path(csv_path)?.finish()?;
        self.data = df;
        Ok(())
    }

    pub fn get_prices(&self) -> PyResult<Vec<f64>> {
        let prices = self.data.column("close")?
            .f64()?
            .into_no_null_iter()
            .collect();
        Ok(prices)
    }

    pub fn calculate_returns(&self) -> PyResult<Vec<f64>> {
        let prices = self.get_prices()?;
        let mut returns = Vec::with_capacity(prices.len() - 1);

        for i in 1..prices.len() {
            returns.push((prices[i] / prices[i-1]) - 1.0);
        }

        Ok(returns)
    }
}
```

### 2. 技术指标计算

```rust
// core/src/indicators/mod.rs
use ndarray::Array1;
use pyo3::prelude::*;

#[pyclass]
pub struct TechnicalIndicators;

#[pymethods]
impl TechnicalIndicators {
    pub fn sma(data: Vec<f64>, window: usize) -> PyResult<Vec<f64>> {
        let data_array = Array1::from(data);
        let mut result = Vec::with_capacity(data_array.len());

        for i in 0..data_array.len() {
            if i < window - 1 {
                result.push(f64::NAN);
            } else {
                let sum: f64 = data_array.slice(s![i-window+1..=i]).sum();
                result.push(sum / window as f64);
            }
        }

        Ok(result)
    }

    pub fn ema(data: Vec<f64>, window: usize) -> PyResult<Vec<f64>> {
        let mut result = Vec::with_capacity(data.len());
        let multiplier = 2.0 / (window as f64 + 1.0);

        if data.is_empty() {
            return Ok(result);
        }

        let mut ema_prev = data[0];
        result.push(ema_prev);

        for i in 1..data.len() {
            let ema_current = (data[i] - ema_prev) * multiplier + ema_prev;
            result.push(ema_current);
            ema_prev = ema_current;
        }

        Ok(result)
    }

    pub fn rsi(data: Vec<f64>, window: usize) -> PyResult<Vec<f64>> {
        let mut result = Vec::with_capacity(data.len());
        let mut gains = Vec::new();
        let mut losses = Vec::new();

        for i in 1..data.len() {
            let change = data[i] - data[i-1];
            if change > 0.0 {
                gains.push(change);
                losses.push(0.0);
            } else {
                gains.push(0.0);
                losses.push(-change);
            }
        }

        // 计算RSI
        for i in 0..gains.len() {
            if i < window - 1 {
                result.push(f64::NAN);
            } else {
                let avg_gain: f64 = gains[i-window+1..=i].iter().sum::<f64>() / window as f64;
                let avg_loss: f64 = losses[i-window+1..=i].iter().sum::<f64>() / window as f64;

                if avg_loss == 0.0 {
                    result.push(100.0);
                } else {
                    let rs = avg_gain / avg_loss;
                    result.push(100.0 - (100.0 / (1.0 + rs)));
                }
            }
        }

        Ok(result)
    }

    pub fn bollinger_bands(data: Vec<f64>, window: usize, num_std: f64) -> PyResult<(Vec<f64>, Vec<f64>, Vec<f64>)> {
        let mut upper = Vec::new();
        let mut middle = Vec::new();
        let mut lower = Vec::new();

        for i in 0..data.len() {
            if i < window - 1 {
                upper.push(f64::NAN);
                middle.push(f64::NAN);
                lower.push(f64::NAN);
            } else {
                let window_data: Vec<f64> = data[i-window+1..=i].to_vec();
                let mean: f64 = window_data.iter().sum::<f64>() / window as f64;

                let variance: f64 = window_data.iter()
                    .map(|x| (x - mean).powi(2))
                    .sum::<f64>() / window as f64;
                let std = variance.sqrt();

                upper.push(mean + num_std * std);
                middle.push(mean);
                lower.push(mean - num_std * std);
            }
        }

        Ok((upper, middle, lower))
    }
}
```

### 3. 风险管理模块

```rust
// core/src/risk/mod.rs
use ndarray::Array1;
use pyo3::prelude::*;

#[pyclass]
pub struct RiskManager {
    #[pyo3(get)]
    max_position_size: f64,
    #[pyo3(get)]
    max_portfolio_risk: f64,
}

#[pymethods]
impl RiskManager {
    #[new]
    pub fn new(max_position_size: f64, max_portfolio_risk: f64) -> Self {
        Self {
            max_position_size,
            max_portfolio_risk,
        }
    }

    pub fn calculate_var(&self, returns: Vec<f64>, confidence: f64) -> PyResult<f64> {
        let mut sorted_returns = returns.clone();
        sorted_returns.sort_by(|a, b| a.partial_cmp(b).unwrap());

        let index = ((1.0 - confidence) * sorted_returns.len() as f64) as usize;
        Ok(sorted_returns[index])
    }

    pub fn calculate_position_limit(&self, portfolio_value: f64, price: f64) -> PyResult<f64> {
        let max_value = portfolio_value * self.max_position_size;
        Ok(max_value / price)
    }

    pub fn check_risk_limits(&self, current_positions: Vec<f64>,
                           portfolio_value: f64) -> PyResult<bool> {
        let total_exposure: f64 = current_positions.iter().sum();
        let exposure_ratio = total_exposure / portfolio_value;

        Ok(exposure_ratio <= self.max_portfolio_risk)
    }
}
```

### 4. 交易执行引擎

```rust
// core/src/execution/mod.rs
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Order {
    #[pyo3(get)]
    id: String,
    #[pyo3(get)]
    symbol: String,
    #[pyo3(get)]
    side: String, // "buy" or "sell"
    #[pyo3(get)]
    quantity: i64,
    #[pyo3(get)]
    order_type: String, // "market" or "limit"
    #[pyo3(get)]
    price: Option<f64>,
    #[pyo3(get)]
    status: String,
}

#[pymethods]
impl Order {
    #[new]
    pub fn new(id: String, symbol: String, side: String,
               quantity: i64, order_type: String, price: Option<f64>) -> Self {
        Self {
            id,
            symbol,
            side,
            quantity,
            order_type,
            price,
            status: "pending".to_string(),
        }
    }
}

#[pyclass]
pub struct ExecutionEngine {
    orders: HashMap<String, Order>,
    positions: HashMap<String, i64>,
}

#[pymethods]
impl ExecutionEngine {
    #[new]
    pub fn new() -> Self {
        Self {
            orders: HashMap::new(),
            positions: HashMap::new(),
        }
    }

    pub fn place_order(&mut self, order: Order) -> PyResult<String> {
        let order_id = order.id.clone();
        self.orders.insert(order_id.clone(), order);
        Ok(order_id)
    }

    pub fn execute_order(&mut self, order_id: &str, fill_price: f64) -> PyResult<bool> {
        if let Some(order) = self.orders.get_mut(order_id) {
            order.status = "filled".to_string();

            let current_position = self.positions.entry(order.symbol.clone()).or_insert(0);

            match order.side.as_str() {
                "buy" => *current_position += order.quantity,
                "sell" => *current_position -= order.quantity,
                _ => return Ok(false),
            }

            Ok(true)
        } else {
            Ok(false)
        }
    }

    pub fn get_position(&self, symbol: &str) -> PyResult<i64> {
        Ok(self.positions.get(symbol).copied().unwrap_or(0))
    }

    pub fn get_all_positions(&self) -> PyResult<HashMap<String, i64>> {
        Ok(self.positions.clone())
    }
}
```

## Python接口层设计

### 1. 核心接口封装

```python
# python/pulse_trader/core/__init__.py
from .data import DataEngine
from .indicators import TechnicalIndicators
from .risk import RiskManager
from .execution import ExecutionEngine

__all__ = ['DataEngine', 'TechnicalIndicators', 'RiskManager', 'ExecutionEngine']
```

```python
# python/pulse_trader/core/data.py
from typing import List, Optional, Dict, Any
import pandas as pd
from . import pulse_trader_core  # Rust编译的模块

class DataEngine:
    def __init__(self, symbol: str):
        self._engine = pulse_trader_core.DataEngine(symbol)
        self.symbol = symbol
        self._data: Optional[pd.DataFrame] = None

    def load_data(self, csv_path: str) -> None:
        """加载数据文件"""
        self._engine.load_data(csv_path)
        self._data = pd.read_csv(csv_path, parse_dates=['date'], index_col='date')

    def get_prices(self) -> List[float]:
        """获取价格序列"""
        return self._engine.get_prices()

    def calculate_returns(self) -> List[float]:
        """计算收益率"""
        return self._engine.calculate_returns()

    def get_dataframe(self) -> pd.DataFrame:
        """获取DataFrame格式的数据"""
        return self._data if self._data is not None else pd.DataFrame()

    def resample(self, frequency: str) -> 'DataEngine':
        """重采样数据"""
        if self._data is not None:
            resampled = self._data.resample(frequency).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()

            new_engine = DataEngine(self.symbol)
            new_engine._data = resampled
            return new_engine
        return self
```

```python
# python/pulse_trader/core/indicators.py
from typing import List, Tuple
import numpy as np
import pandas as pd
from . import pulse_trader_core

class TechnicalIndicators:
    @staticmethod
    def sma(data: List[float], window: int) -> List[float]:
        """简单移动平均线"""
        return pulse_trader_core.TechnicalIndicators.sma(data, window)

    @staticmethod
    def ema(data: List[float], window: int) -> List[float]:
        """指数移动平均线"""
        return pulse_trader_core.TechnicalIndicators.ema(data, window)

    @staticmethod
    def rsi(data: List[float], window: int = 14) -> List[float]:
        """相对强弱指数"""
        return pulse_trader_core.TechnicalIndicators.rsi(data, window)

    @staticmethod
    def bollinger_bands(data: List[float], window: int = 20, num_std: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """布林带"""
        return pulse_trader_core.TechnicalIndicators.bollinger_bands(data, window, num_std)

    @staticmethod
    def macd(data: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """MACD指标 - 使用Python实现复杂逻辑"""
        exp1 = pd.Series(data).ewm(span=fast).mean()
        exp2 = pd.Series(data).ewm(span=slow).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return macd_line.tolist(), signal_line.tolist(), histogram.tolist()

    @staticmethod
    def calculate_all_indicators(prices: List[float]) -> pd.DataFrame:
        """批量计算常用指标"""
        df = pd.DataFrame({'price': prices})

        # 移动平均线
        df['sma_5'] = TechnicalIndicators.sma(prices, 5)
        df['sma_20'] = TechnicalIndicators.sma(prices, 20)
        df['ema_12'] = TechnicalIndicators.ema(prices, 12)
        df['ema_26'] = TechnicalIndicators.ema(prices, 26)

        # RSI
        df['rsi'] = TechnicalIndicators.rsi(prices)

        # 布林带
        upper, middle, lower = TechnicalIndicators.bollinger_bands(prices)
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower

        # MACD
        macd, signal, histogram = TechnicalIndicators.macd(prices)
        df['macd'] = macd
        df['macd_signal'] = signal
        df['macd_histogram'] = histogram

        return df
```

### 2. 策略开发框架

```python
# python/pulse_trader/strategies/__init__.py
from .base import Strategy, Signal
from .ma_cross import MACrossStrategy
from .rsi_strategy import RSIStrategy
from .portfolio import PortfolioStrategy

__all__ = ['Strategy', 'Signal', 'MACrossStrategy', 'RSIStrategy', 'PortfolioStrategy']
```

```python
# python/pulse_trader/strategies/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

@dataclass
class Signal:
    timestamp: datetime
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    strength: float   # 信号强度 0-1
    price: float
    reason: str
    metadata: Dict[str, Any] = None

class Strategy(ABC):
    def __init__(self, name: str, **params):
        self.name = name
        self.params = params
        self.indicators = {}

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信号"""
        pass

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        from ..core.indicators import TechnicalIndicators

        prices = data['close'].tolist()
        indicators_df = TechnicalIndicators.calculate_all_indicators(prices)

        # 合并到原数据
        result = data.copy()
        for col in indicators_df.columns:
            if col != 'price':
                result[col] = indicators_df[col]

        return result

    def validate_signal(self, signal: Signal) -> bool:
        """验证信号有效性"""
        return signal.strength > 0.1 and signal.price > 0
```

```python
# python/pulse_trader/strategies/ma_cross.py
from typing import List
import pandas as pd
from datetime import datetime
from .base import Strategy, Signal
from ..core.indicators import TechnicalIndicators

class MACrossStrategy(Strategy):
    def __init__(self, short_window: int = 5, long_window: int = 20):
        super().__init__("MA_Cross", short_window=short_window, long_window=long_window)

    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []

        # 计算指标
        prices = data['close'].tolist()
        short_ma = TechnicalIndicators.sma(prices, self.params['short_window'])
        long_ma = TechnicalIndicators.sma(prices, self.params['long_window'])

        for i in range(len(data)):
            if i < max(self.params['short_window'], self.params['long_window']):
                continue

            current_short = short_ma[i]
            current_long = long_ma[i]
            prev_short = short_ma[i-1]
            prev_long = long_ma[i-1]

            current_price = prices[i]
            timestamp = data.index[i]

            # 金叉买入信号
            if prev_short <= prev_long and current_short > current_long:
                strength = min(1.0, (current_short - current_long) / current_long)
                signal = Signal(
                    timestamp=timestamp,
                    symbol=data.iloc[i].get('symbol', 'UNKNOWN'),
                    signal_type='buy',
                    strength=strength,
                    price=current_price,
                    reason=f"MA金叉: 短均线({current_short:.2f}) > 长均线({current_long:.2f})"
                )
                if self.validate_signal(signal):
                    signals.append(signal)

            # 死叉卖出信号
            elif prev_short >= prev_long and current_short < current_long:
                strength = min(1.0, (current_long - current_short) / current_long)
                signal = Signal(
                    timestamp=timestamp,
                    symbol=data.iloc[i].get('symbol', 'UNKNOWN'),
                    signal_type='sell',
                    strength=strength,
                    price=current_price,
                    reason=f"MA死叉: 短均线({current_short:.2f}) < 长均线({current_long:.2f})"
                )
                if self.validate_signal(signal):
                    signals.append(signal)

        return signals
```

### 3. 回测系统

```python
# python/pulse_trader/backtest/__init__.py
from .engine import BacktestEngine
from .results import BacktestResults

__all__ = ['BacktestEngine', 'BacktestResults']
```

```python
# python/pulse_trader/backtest/engine.py
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime
from ..strategies.base import Strategy
from ..core.execution import ExecutionEngine
from ..core.risk import RiskManager
from ..core.data import DataEngine
from .results import BacktestResults

class BacktestEngine:
    def __init__(self, initial_capital: float = 1000000.0,
                 commission: float = 0.001,
                 slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        # 使用Rust组件
        self.execution_engine = ExecutionEngine()
        self.risk_manager = RiskManager(
            max_position_size=0.2,
            max_portfolio_risk=0.8
        )

        # 回测状态
        self.current_capital = initial_capital
        self.portfolio_history: List[Dict] = []
        self.trades: List[Dict] = []

    def run_backtest(self, strategy: Strategy, data: pd.DataFrame) -> BacktestResults:
        """运行回测"""
        print(f"开始回测策略: {strategy.name}")
        print(f"数据范围: {data.index[0]} 到 {data.index[-1]}")

        # 生成交易信号
        signals = strategy.generate_signals(data)
        print(f"生成 {len(signals)} 个交易信号")

        # 按时间排序信号
        signals.sort(key=lambda x: x.timestamp)

        # 执行回测
        for signal in signals:
            self._process_signal(signal)

            # 记录组合快照
            self._record_portfolio_snapshot(signal.timestamp, data)

        # 生成回测结果
        return BacktestResults(
            initial_capital=self.initial_capital,
            final_capital=self.current_capital,
            trades=self.trades,
            portfolio_history=self.portfolio_history,
            signals=signals
        )

    def _process_signal(self, signal):
        """处理单个交易信号"""
        # 风险检查
        position_limit = self.risk_manager.calculate_position_limit(
            self.current_capital, signal.price
        )

        if signal.signal_type == 'buy':
            quantity = int(position_limit * signal.strength / 100) * 100  # 整手

            if quantity > 0:
                order_id = f"order_{len(self.trades)}"
                order = self.execution_engine.place_order(
                    symbol=signal.symbol,
                    side='buy',
                    quantity=quantity,
                    order_type='market'
                )

                # 模拟成交
                fill_price = signal.price * (1 + self.slippage)
                commission_cost = quantity * fill_price * self.commission
                total_cost = quantity * fill_price + commission_cost

                if total_cost <= self.current_capital:
                    self.current_capital -= total_cost
                    self.execution_engine.execute_order(order_id, fill_price)

                    self.trades.append({
                        'timestamp': signal.timestamp,
                        'symbol': signal.symbol,
                        'side': 'buy',
                        'quantity': quantity,
                        'price': fill_price,
                        'commission': commission_cost,
                        'reason': signal.reason
                    })

        elif signal.signal_type == 'sell':
            current_position = self.execution_engine.get_position(signal.symbol)

            if current_position > 0:
                sell_quantity = int(current_position * signal.strength)

                order_id = f"order_{len(self.trades)}"
                order = self.execution_engine.place_order(
                    symbol=signal.symbol,
                    side='sell',
                    quantity=sell_quantity,
                    order_type='market'
                )

                # 模拟成交
                fill_price = signal.price * (1 - self.slippage)
                commission_cost = sell_quantity * fill_price * self.commission
                total_proceeds = sell_quantity * fill_price - commission_cost

                self.current_capital += total_proceeds
                self.execution_engine.execute_order(order_id, fill_price)

                self.trades.append({
                    'timestamp': signal.timestamp,
                    'symbol': signal.symbol,
                    'side': 'sell',
                    'quantity': sell_quantity,
                    'price': fill_price,
                    'commission': commission_cost,
                    'reason': signal.reason
                })

    def _record_portfolio_snapshot(self, timestamp, market_data):
        """记录组合快照"""
        positions = self.execution_engine.get_all_positions()

        # 计算持仓价值
        position_value = 0.0
        for symbol, quantity in positions.items():
            if quantity > 0 and symbol in market_data.index:
                current_price = market_data.loc[timestamp, 'close']
                position_value += quantity * current_price

        total_value = self.current_capital + position_value

        self.portfolio_history.append({
            'timestamp': timestamp,
            'cash': self.current_capital,
            'position_value': position_value,
            'total_value': total_value,
            'positions': positions.copy()
        })
```

## 构建和部署

### 1. Rust编译配置

```toml
# Cargo.toml
[package]
name = "pulse-trader-core"
version = "0.1.0"
edition = "2021"

[lib]
name = "pulse_trader_core"
crate-type = ["cdylib"]  # Python扩展

[dependencies]
pyo3 = { version = "0.18", features = ["extension-module"] }
numpy = "0.18"
ndarray = "0.15"
polars = { version = "0.25", features = ["lazy"] }
tokio = { version = "1.0", features = ["full"] }
rayon = "1.5"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sqlx = { version = "0.6", features = ["runtime-tokio-rustls", "mysql", "sqlite"] }
reqwest = { version = "0.11", features = ["json"] }

[dependencies.pyo3]
version = "0.18"
features = ["extension-module"]

# 优化配置
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
```

### 2. Python构建脚本

```python
# setup.py
from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11

ext_modules = [
    Pybind11Extension(
        "pulse_trader.core.pulse_trader_core",
        sources=[
            "core/src/lib.rs",
            "core/src/data/mod.rs",
            "core/src/indicators/mod.rs",
            "core/src/risk/mod.rs",
            "core/src/execution/mod.rs",
            "core/src/ffi/mod.rs"
        ],
        include_dirs=[
            pybind11.get_include(),
            "core/include"
        ],
        cxx_std=17,
        define_macros=[("VERSION_INFO", '"dev"')],
    ),
]

setup(
    name="pulse_trader",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    packages=["pulse_trader"],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "matplotlib>=3.4.0",
        "plotly>=5.0.0",
        "scikit-learn>=1.0.0",
    ],
)
```

### 3. 构建命令

```bash
# 1. 编译Rust核心
cd core
cargo build --release

# 2. 构建Python包
cd ../python
pip install maturin
maturin develop --release

# 3. 运行测试
pytest tests/

# 4. 使用示例
python examples/basic_strategy.py
```

## 性能优化策略

### 1. 内存管理
- **Rust**: 零拷贝数据传递
- **Python**: 使用numpy数组避免数据转换
- **共享内存**: 大数据集使用共享内存

### 2. 并行计算
- **Rust**: 使用Rayon进行数据并行
- **异步I/O**: Tokio异步运行时
- **批量处理**: 减少Python-Rust调用次数

### 3. 缓存策略
- **指标缓存**: 避免重复计算
- **数据预加载**: 预先加载常用数据
- **结果缓存**: 缓存计算结果

## 使用示例

```python
# examples/high_performance_strategy.py
import numpy as np
import pandas as pd
from pulse_trader.core import DataEngine, TechnicalIndicators
from pulse_trader.strategies import MACrossStrategy
from pulse_trader.backtest import BacktestEngine

def main():
    # 使用Rust高性能数据引擎
    data_engine = DataEngine("000001.SZ")
    data_engine.load_data("data/000001.SZ.csv")

    # 获取数据
    prices = data_engine.get_prices()
    print(f"加载了 {len(prices)} 个价格数据点")

    # 使用Rust计算技术指标
    sma_5 = TechnicalIndicators.sma(prices, 5)
    sma_20 = TechnicalIndicators.sma(prices, 20)
    rsi = TechnicalIndicators.rsi(prices)

    print(f"计算完成指标: SMA5, SMA20, RSI")

    # 创建策略并运行回测
    strategy = MACrossStrategy(short_window=5, long_window=20)

    # 准备数据
    df = data_engine.get_dataframe()
    df = strategy.calculate_indicators(df)

    # 运行回测
    backtest_engine = BacktestEngine(initial_capital=1000000)
    results = backtest_engine.run_backtest(strategy, df)

    # 显示结果
    print(f"回测完成:")
    print(f"总收益率: {results.total_return:.2%}")
    print(f"年化收益率: {results.annual_return:.2%}")
    print(f"夏普比率: {results.sharpe_ratio:.2f}")
    print(f"最大回撤: {results.max_drawdown:.2%}")

    # 可视化
    results.plot_equity_curve()
    results.plot_drawdown()

if __name__ == "__main__":
    main()
```

这个Rust+Python混合架构为您的量化交易系统提供了：
- **极致性能**: Rust处理核心计算
- **开发效率**: Python进行策略开发
- **内存安全**: Rust的内存安全保证
- **丰富生态**: Python的数据科学生态

您可以根据具体需求调整各个模块的复杂度和功能！
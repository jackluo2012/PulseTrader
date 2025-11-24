# PulseTrader - A股量化交易系统

基于 Rust + Python + ClickHouse + Akshare 的现代化A股量化交易系统。

## 技术栈

- **Python 3.12**: 主要开发语言
- **Rust**: 高性能计算模块
- **Maturin + PyO3**: 现代化Rust-Python集成方案
- **ClickHouse**: 时序数据库
- **Akshare**: A股数据源

## 快速开始

### 环境要求

- Python 3.12+
- Git
- Docker (用于ClickHouse)

### 安装步骤

1. 克隆仓库
```bash
git clone <repository-url>
cd PulseTrader
```
2. 创建虚拟环境
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行测试
```bash
python test_environment.py
```

## 项目结构

```
PulseTrader/
├── src/                    # 源代码
│   ├── data/              # 数据获取和处理
│   ├── strategies/        # 交易策略
│   ├── backtest/          # 回测引擎
│   ├── execution/         # 交易执行
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── notebooks/            # Jupyter笔记本
├── scripts/              # 脚本文件
├── config/               # 配置文件
├── rust/                 # Rust高性能模块
│   ├── src/              # Rust源代码
│   ├── python/           # Python绑定代码
│   └── Cargo.toml        # Rust项目配置
└── data/                 # 数据文件
```

## 开发进度

- [x] 第一章：环境搭建与项目初始化
- [ ] 第二章：数据获取与存储
- [ ] 第三章：基础技术指标实现
- [ ] 第四章：策略开发框架
- [ ] 第五章：回测系统构建

## 贡献

欢迎提交Issue和Pull Request。

## 许可证

MIT License
EOF
```

### 常见问题与解决方案

**Q1: `python3.12: command not found`**
```bash
# 解决方案：检查是否正确添加到PATH
echo $PATH | grep python

# 如果没有，手动添加到 ~/.bashrc 或 ~/.zshrc
export PATH="/usr/bin/python3.12:$PATH"
```

**Q2: 虚拟环境激活失败**
```bash
# 解决方案：重新创建虚拟环境
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
```

**Q3: pip安装依赖失败**
```bash
# 解决方案：升级pip并使用国内镜像
pip install --upgrade pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pandas numpy
```

**Q4: VS Code无法识别虚拟环境**
```bash
# 解决方案：在VS Code中重新选择Python解释器
# 按 Ctrl+Shift+P，输入 "Python: Select Interpreter"
# 选择 ./.venv/bin/python
```

### 步骤10：创建Rust集成基础文件

为后续的Rust高性能模块做准备，创建基础的Rust项目文件：

```bash
# 创建Rust项目配置文件
cat > rust/Cargo.toml << 'EOF'
[package]
name = "pulse-trader-rust"
version = "0.1.0"
edition = "2021"

[lib]
name = "pulse_trader_rust"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
numpy = "0.21"
polars = { version = "0.42", features = ["lazy"] }
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
EOF

# 创建基础Rust库文件
cat > rust/src/lib.rs << 'EOF'
use pyo3::prelude::*;

/// Python模块定义
#[pymodule]
fn pulse_trader_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__author__", "PulseTrader Team")?;
    Ok(())
}
EOF
```

### 关于Maturin + PyO3的说明

**为什么选择Maturin？**

1. **简化构建**: Maturin自动处理复杂的Rust-Python绑定过程
2. **无缝集成**: 与pip、poetry等Python包管理工具完美配合
3. **高性能**: 基于PyO3，提供接近原生C的性能
4. **开发友好**: 支持热重载，调试更方便

**Maturin工作流程：**
```bash
# 开发模式编译（支持热重载）
maturin develop

# 生产模式构建
maturin build --release

# 发布到PyPI
maturin publish
```

这个组合将在第三章详细讲解，现在我们先准备好基础环境。

### 本节小结

恭喜！您已经成功完成了Python 3.12开发环境的配置。在本节中，您学会了：

1. ✅ 安装Python 3.12最新稳定版
2. ✅ 创建和配置虚拟环境
3. ✅ 安装和配置专业开发工具
4. ✅ 创建标准化的项目结构
5. ✅ 验证环境配置正确性

**下一步：** 完成环境配置后，您将在下一节学习如何安装和配置ClickHouse数据库，为存储股票数据做好准备。

---

## 提示

- 每次开发前，记得先激活虚拟环境：`source .venv/bin/activate`
- 如果遇到问题，可以查看本节的"常见问题与解决方案"部分
- 保存好你的项目配置，后续章节会在此基础上继续开发

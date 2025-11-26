# PulseTrader — 全流程量化系统编写指南（CLAUDE 总纲）

欢迎来到 PulseTrader —— 一个面向 A 股市场、基于 **Python + Rust + ClickHouse + Akshare** 的现代化量化交易系统。

本指南由“量化工程师 AI 教练（Claude / ChatGPT）”带领“初学者（你）”手把手搭建整个量化系统。
你将从零开始，按章节逐步完成：**环境、数据、存储、回测、Rust 加速、实时行情、实盘模块、部署**。

本 `CLAUDE.md` 是整个文档体系的总纲，每个大章节会放在 `doc/` 子目录里，每个小章节是独立的 Markdown 文件。你按顺序阅读即可。

---

# 🎯 项目定位

PulseTrader 的目标是：

✔ **使用现代、稳定、可维护、可扩展的技术栈**
✔ **构建一个从数据 → 存储 → 策略 → 回测 → 实盘 的一体化系统**
✔ **允许逐步替换模块，如：更快的 Rust 模块、更专业的数据源、更成熟的执行系统**
✔ **适合个人、小团队、中小公司直接使用或改造**

系统是 **文档驱动（Documentation Driven Development）** 的，你只要跟着文档做，就能每一步都有代码产出。

---

# 🧱 技术栈选型（稳定 + 最新）

技术栈经过严格筛选，遵循“最新但稳定”的原则：

## **Python 3.12（主逻辑层）**

- 策略代码
- 数据处理
- 回测框架
- 实盘订单管理

## **Rust（高性能计算层）**

- 使用 **PyO3 + Maturin** 生成 Python 可 import 的 `.pyd/.so` 扩展
- 用于：指标计算、大规模数据处理、批量清洗、风控计算

## **Maturin（Rust → Python 构建工具）**

- 最稳定的 Rust-Python 打包工具
- 无缝生成 wheel 包
- 支持 Python 3.12（必须）

## **ClickHouse（数据存储层）**

- 行情、分笔、回测分钟线等全部放进 ClickHouse
- 本地使用官方 Docker 镜像
- Query + 分区 + TTL + MergeTree 支持高性能写入与查询

## **Akshare（A 股数据接口）**

- 免费 / 开放源代码
- 专为国内金融数据设计
- 直接拉取 A 股行情、指数、期货数据

## **WebSocket 系统（实时行情 + 实盘委托）**

- 使用 Python `websockets` 库
- 与行情源、模拟撮合、实盘交易通道通信

## **常用库（稳定）**

- pandas / numpy：数据处理
- polars：更快的数据框（可选）
- clickhouse-connect：Python 写入 ClickHouse
- vectorbt / backtrader / bt：回测框架可选

---

# 📁 文档目录结构（你需要严格使用）

在项目根目录创建：
doc/
├── 00_CLAUDE.md ← 你正在看的这个文件
├── 01_setup_env/ # 环境安装
├── 02_data_ingest/ # 数据采集
├── 03_storage_clickhouse/ # 数据库存储
├── 04_rust_modules/ # Rust 性能模块
├── 05_strategy_dev_python/ # 策略开发与回测
├── 06_live_trading/ # 实盘/模拟盘
├── 07_deployment_ops/ # 部署
├── 08_tests_ci_cd/ # 测试与持续集成
└── 99_appendix/ # 附录

//! PulseTrader Rust高性能数据处理模块
//!
//! 本模块提供基于Rust的高性能数据处理能力，包括：
//! - 通达信二进制数据解析
//! - 并行数据处理
//! - Python绑定接口
//! - ClickHouse高性能存储

pub mod parsers;

pub mod processors; // TODO: 并行数据处理模块
                    // 重新导出主要接口
pub use parsers::tdx_day::{TDXDayParser, TDXDayRecord, TDXStatistics};

/// 库版本信息
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// 默认日志初始化
pub fn init_logger() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();
}

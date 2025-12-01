use anyhow::Result;
use log::{debug, error, info, warn};
use pulse_trader_rust::parsers::{TDXDayParser, TDXStatistics};
use std::fs;
use std::path::PathBuf;
use tempfile::TempDir; // 引入日志功能
#[test]
/// 测试函数：验证TDXDayParser的创建功能
///
/// 此函数用于测试TDXDayParser的构造函数是否正确地将传入的路径设置为数据根目录。
fn test_parser_creation() {
    // 创建一个临时目录，用于测试
    let temp_dir = TempDir::new().unwrap();
    // 使用临时目录路径创建TDXDayParser实例
    let parser = TDXDayParser::new(temp_dir.path());

    // 验证parser的data_root属性是否与传入的路径一致
    assert_eq!(parser.data_root, temp_dir.path());
}

#[test]
/// 测试函数：测试从文件路径中提取股票代码和市场信息的功能
fn test_symbol_extraction() {
    // 创建一个临时目录，用于测试环境
    let temp_dir = TempDir::new().unwrap();
    // 基于临时目录路径创建一个新的TDXDayParser实例
    let parser = TDXDayParser::new(temp_dir.path());

    // 创建测试目录结构
    let sh_dir = temp_dir.path().join("vipdoc").join("sh").join("day");
    fs::create_dir_all(&sh_dir).unwrap();
    let test_file = sh_dir.join("600000.day");

    let (symbol, market) = parser.extract_symbol_market(&test_file).unwrap();

    assert_eq!(symbol, "600000");
    assert_eq!(market, "SH");
}

#[test]
fn test_data_validation() {
    use pulse_trader_rust::parsers::ValidationUtils;

    // 测试股票代码验证
    assert!(ValidationUtils::validate_symbol("000001").is_ok());
    assert!(ValidationUtils::validate_symbol("AAAAAA").is_err());

    // 测试市场验证
    assert!(ValidationUtils::validate_market("SH").is_ok());
    assert!(ValidationUtils::validate_market("BJ").is_err());

    // 测试价格验证
    assert!(ValidationUtils::validate_price_data(10.0, 12.0, 8.0, 11.0).is_ok());
    assert!(ValidationUtils::validate_price_data(-1.0, 12.0, 8.0, 11.0).is_err());
}

#[test]
/// 测试统计计算功能的函数
/// 用于验证在没有数据的情况下，统计信息是否正确初始化
fn test_statistics_calculation() {
    // 创建临时目录，用于测试数据存储
    let temp_dir = TempDir::new().unwrap();
    // 使用临时目录路径创建TDXDayParser实例
    let parser = TDXDayParser::new(temp_dir.path());

    // 创建测试数据目录
    let sh_dir = temp_dir.path().join("vipdoc").join("sh").join("day");
    let sz_dir = temp_dir.path().join("vipdoc").join("sz").join("day");
    fs::create_dir_all(&sh_dir).unwrap();
    fs::create_dir_all(&sz_dir).unwrap();

    // 创建空的统计信息
    let stats = parser.get_statistics().unwrap();

    assert_eq!(stats.total_stocks, 0);
    assert_eq!(stats.sh_count, 0);
    assert_eq!(stats.sz_count, 0);
}

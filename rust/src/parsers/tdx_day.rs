//! 通达信日线数据解析器

use anyhow::{Context, Result};
use chrono::{NaiveDate, Utc};
use log::{info, warn};
use serde::{Deserialize, Serialize};
use std::fs::File;
use std::io::{BufRead, BufReader, Read};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;
/// 通达信日线记录结构
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TDXDayRecord {
    /// 交易日期
    pub date: NaiveDate,
    /// 股票代码
    pub symbol: String,
    /// 开盘价（元）
    pub open: f64,
    /// 最高价（元）
    pub high: f64,
    /// 最低价（元）
    pub low: f64,
    /// 收盘价（元）
    pub close: f64,
    /// 成交量（股）
    pub volume: u64,
    /// 成交额（元）
    pub amount: f64,
    /// 市场（SH/SZ）
    pub market: String,
}

/// 二进制格式的日线记录（内存中）
#[repr(C, packed)]
#[derive(Debug)]
struct BinaryDayRecord {
    date: u32,
    open: u32,
    high: u32,
    low: u32,
    close: u32,
    amount: f32,
    volume: u32,
    reserved: u32,
}

impl BinaryDayRecord {
    /// 字节大小
    const SIZE: usize = std::mem::size_of::<BinaryDayRecord>();
}

/// 通达信解析器
#[derive(Debug)]
pub struct TDXDayParser {
    /// 数据根目录
    pub data_root: PathBuf,
}

impl TDXDayParser {
    /// 创建新的解析器
    pub fn new<P: AsRef<Path>>(data_root: P) -> Self {
        Self {
            data_root: data_root.as_ref().to_path_buf(),
        }
    }

    /// 解析单个day文件
    pub fn parse_file<P: AsRef<Path>>(&self, file_path: P) -> Result<Vec<TDXDayRecord>> {
        let file_path = file_path.as_ref();

        // 从文件路径提取股票代码和市场
        let (symbol, market) = self.extract_symbol_market(file_path)?;

        // 读取文件内容
        let mut file = File::open(file_path)
            .with_context(|| format!("无法打开文件: {}", file_path.display()))?;

        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)
            .with_context(|| format!("无法读取文件: {}", file_path.display()))?;

        // 解析二进制数据
        self.parse_binary_data(&buffer, &symbol, &market)
    }

    /// 解析二进制数据
    pub fn parse_binary_data(
        &self,
        buffer: &[u8],
        symbol: &str,
        market: &str,
    ) -> Result<Vec<TDXDayRecord>> {
        if buffer.len() % BinaryDayRecord::SIZE != 0 {
            return Err(anyhow::anyhow!(
                "文件大小不正确，期望{}的倍数，实际{}字节",
                BinaryDayRecord::SIZE,
                buffer.len()
            ));
        }

        let record_count = buffer.len() / BinaryDayRecord::SIZE;
        let mut records = Vec::with_capacity(record_count);

        for i in 0..record_count {
            let offset = i * BinaryDayRecord::SIZE;
            let record_slice = &buffer[offset..offset + BinaryDayRecord::SIZE];

            // 安全地转换字节数组到结构体
            let binary_record: BinaryDayRecord =
                unsafe { std::ptr::read_unaligned(record_slice.as_ptr() as *const _) };

            // 转换为高级数据结构
            let record = self.convert_binary_record(&binary_record, symbol, market)?;
            records.push(record);
        }

        // 按日期排序（通达信数据通常是正序的，但确保一致性）
        records.sort_by(|a, b| a.date.cmp(&b.date));

        Ok(records)
    }

    /// 转换二进制记录到结构化数据
    fn convert_binary_record(
        &self,
        binary: &BinaryDayRecord,
        symbol: &str,
        market: &str,
    ) -> Result<TDXDayRecord> {
        // 验证日期有效性
        // 安全地读取日期字段
        let date = binary.date;
        let date_str = date.to_string();
        if date_str.len() != 8 {
            return Err(anyhow::anyhow!("无效的日期格式: {}", date_str));
        }

        let year = date_str[0..4]
            .parse::<i32>()
            .with_context(|| format!("无效的年份: {}", &date_str[0..4]))?;
        let month = date_str[4..6]
            .parse::<u32>()
            .with_context(|| format!("无效的月份: {}", &date_str[4..6]))?;
        let day = date_str[6..8]
            .parse::<u32>()
            .with_context(|| format!("无效的日期: {}", &date_str[6..8]))?;

        let date = NaiveDate::from_ymd_opt(year, month, day)
            .ok_or_else(|| anyhow::anyhow!("无效的日期: {}", date_str))?;

        // 价格转换（分为单位转换为元）
        let open = binary.open as f64 / 100.0;
        let high = binary.high as f64 / 100.0;
        let low = binary.low as f64 / 100.0;
        let close = binary.close as f64 / 100.0;

        // 验证价格合理性
        self.validate_prices(open, high, low, close)?;

        Ok(TDXDayRecord {
            date,
            symbol: symbol.to_string(),
            open,
            high,
            low,
            close,
            volume: binary.volume as u64,
            amount: binary.amount as f64,
            market: market.to_string(),
        })
    }

    /// 验证价格数据合理性
    fn validate_prices(&self, open: f64, high: f64, low: f64, close: f64) -> Result<()> {
        // 检查价格是否为正数
        if open <= 0.0 || high <= 0.0 || low <= 0.0 || close <= 0.0 {
            return Err(anyhow::anyhow!("价格必须为正数"));
        }

        // 检查高低价关系
        if high < low {
            return Err(anyhow::anyhow!("最高价不能低于最低价"));
        }

        // 检查开收盘价是否在高低价范围内
        if open > high || open < low || close > high || close < low {
            return Err(anyhow::anyhow!("开收盘价超出高低价范围"));
        }

        // 检查价格是否合理（1分-10000元）
        if open < 0.01 || high > 10000.0 || low < 0.01 || close > 10000.0 {
            return Err(anyhow::anyhow!("价格超出合理范围"));
        }

        Ok(())
    }

    /// 从文件路径提取股票代码和市场
    pub fn extract_symbol_market(&self, file_path: &Path) -> Result<(String, String)> {
        let file_name = file_path
            .file_stem()
            .and_then(|s| s.to_str())
            .ok_or_else(|| anyhow::anyhow!("无效的文件名"))?;

        if file_name.len() != 6 {
            return Err(anyhow::anyhow!("股票代码长度错误"));
        }

        // 根据目录判断市场
        let path_str = file_path.to_string_lossy().to_lowercase();
        let market = if path_str.contains("/sh/") || path_str.contains("\\sh\\") {
            "SH"
        } else if path_str.contains("/sz/") || path_str.contains("\\sz\\") {
            "SZ"
        } else {
            return Err(anyhow::anyhow!("无法确定市场，路径中缺少市场信息"));
        };

        Ok((file_name.to_string(), market.to_string()))
    }

    /// 解析目录下的所有day文件
    pub fn parse_directory<P: AsRef<Path>>(&self, dir_path: P) -> Result<Vec<TDXDayRecord>> {
        let dir_path = dir_path.as_ref();
        let mut all_records = Vec::new();

        if !dir_path.exists() {
            return Err(anyhow::anyhow!("目录不存在: {}", dir_path.display()));
        }

        // 遍历目录下的所有.day文件
        for entry in WalkDir::new(dir_path).into_iter().filter_map(|e| e.ok()) {
            let path = entry.path();

            if path.extension().and_then(|s| s.to_str()) == Some("day") {
                match self.parse_file(path) {
                    Ok(mut records) => {
                        info!("解析文件成功: {}, {}条记录", path.display(), records.len());
                        all_records.append(&mut records);
                    }
                    Err(e) => {
                        warn!("解析文件失败 {}: {}", path.display(), e);
                        // 继续处理其他文件，不中断整个过程
                    }
                }
            }
        }

        // 按日期和股票代码排序
        all_records.sort_by(|a, b| {
            a.date
                .cmp(&b.date)
                .then(a.symbol.cmp(&b.symbol))
                .then(a.market.cmp(&b.market))
        });

        Ok(all_records)
    }

    /// 获取所有股票列表
    pub fn get_stock_list(&self) -> Result<Vec<(String, String)>> {
        let mut stocks = Vec::new();
        let markets = ["sh", "sz"];

        for market in &markets {
            let market_dir = self.data_root.join("vipdoc").join(market).join("day");

            if market_dir.exists() {
                for entry in std::fs::read_dir(&market_dir)? {
                    let entry = entry?;
                    let path = entry.path();

                    if path.extension().and_then(|s| s.to_str()) == Some("day") {
                        if let Some(file_stem) = path.file_stem().and_then(|s| s.to_str()) {
                            if file_stem.len() == 6 && file_stem.chars().all(|c| c.is_ascii_digit())
                            {
                                let market_str = market.to_uppercase();
                                stocks.push((file_stem.to_string(), market_str.to_string()));
                            }
                        }
                    }
                }
            }
        }

        // 排序股票列表
        stocks.sort();
        Ok(stocks)
    }

    /// 获取指定日期的数据
    pub fn get_data_by_date(&self, target_date: NaiveDate) -> Result<Vec<TDXDayRecord>> {
        let all_records =
            self.parse_directory(self.data_root.join("vipdoc").join("sh").join("day"))?;

        let sz_records =
            self.parse_directory(self.data_root.join("vipdoc").join("sz").join("day"))?;

        let mut combined_records = all_records;
        combined_records.extend(sz_records);

        // 过滤指定日期的数据
        Ok(combined_records
            .into_iter()
            .filter(|record| record.date == target_date)
            .collect())
    }

    /// 获取指定股票的历史数据
    pub fn get_data_by_symbol(&self, symbol: &str, market: &str) -> Result<Vec<TDXDayRecord>> {
        let file_path = self
            .data_root
            .join("vipdoc")
            .join(market.to_lowercase())
            .join("day")
            .join(format!("{}.day", symbol));

        self.parse_file(file_path)
    }

    /// 获取数据统计信息
    pub fn get_statistics(&self) -> Result<TDXStatistics> {
        let stocks = self.get_stock_list()?;
        let total_stocks = stocks.len();
        let mut total_records = 0;
        let mut earliest_date = None;
        let mut latest_date = None;
        let mut sh_count = 0;
        let mut sz_count = 0;

        for (symbol, market) in &stocks {
            match self.get_data_by_symbol(symbol, market) {
                Ok(records) => {
                    total_records += records.len();

                    if let Some(first_record) = records.first() {
                        match &earliest_date {
                            None => earliest_date = Some(first_record.date),
                            Some(current) => {
                                if first_record.date < *current {
                                    earliest_date = Some(first_record.date);
                                }
                            }
                        }

                        match &latest_date {
                            None => latest_date = Some(first_record.date),
                            Some(current) => {
                                if first_record.date > *current {
                                    latest_date = Some(first_record.date);
                                }
                            }
                        }
                    }

                    // match market {
                    //     "SH" => sh_count += 1,
                    //     "SZ" => sz_count += 1,
                    //     _ => {}
                    // }
                }
                Err(_) => {
                    // 忽略无法读取的股票数据
                }
            }
        }

        Ok(TDXStatistics {
            total_stocks,
            total_records,
            sh_count,
            sz_count,
            earliest_date,
            latest_date,
            data_size_bytes: self.calculate_data_size()?,
        })
    }

    /// 计算数据文件总大小
    fn calculate_data_size(&self) -> Result<u64> {
        let mut total_size = 0u64;

        for entry in WalkDir::new(&self.data_root)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            let path = entry.path();
            if path.is_file() {
                if let Some(metadata) = path.metadata().ok() {
                    total_size += metadata.len();
                }
            }
        }

        Ok(total_size)
    }
}

/// 数据统计信息
#[derive(Debug, Serialize, Deserialize)]
pub struct TDXStatistics {
    /// 总股票数
    pub total_stocks: usize,
    /// 总记录数
    pub total_records: usize,
    /// 沪市股票数
    pub sh_count: usize,
    /// 深市股票数
    pub sz_count: usize,
    /// 最早日期
    pub earliest_date: Option<NaiveDate>,
    /// 最新日期
    pub latest_date: Option<NaiveDate>,
    /// 数据文件总大小（字节）
    pub data_size_bytes: u64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use tempfile::TempDir;

    #[test]
    fn test_tdx_parser_creation() {
        let temp_dir = TempDir::new().unwrap();
        let parser = TDXDayParser::new(temp_dir.path());

        assert_eq!(parser.data_root, temp_dir.path());
    }

    #[test]
    fn test_symbol_extraction() {
        let temp_dir = TempDir::new().unwrap();
        let parser = TDXDayParser::new(temp_dir.path());

        // 创建测试路径
        let sh_path = temp_dir
            .path()
            .join("vipdoc")
            .join("sh")
            .join("day")
            .join("600000.day");
        let (symbol, market) = parser.extract_symbol_market(&sh_path).unwrap();

        assert_eq!(symbol, "600000");
        assert_eq!(market, "SH");
    }

    #[test]
    fn test_binary_record_size() {
        assert_eq!(BinaryDayRecord::SIZE, 32);
    }
}

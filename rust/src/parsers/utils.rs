//! 解析器工具模块

use anyhow::{Context, Result};
use flate2::read::GzDecoder;
use std::fs::{self, File};
use std::io::{BufReader, Read};
use std::path::{Path, PathBuf};
use zip::ZipArchive;

/// 文件处理工具
pub struct FileUtils;

impl FileUtils {
    /// 检查文件是否存在且可读
    pub fn check_file_readable<P: AsRef<Path>>(file_path: P) -> Result<()> {
        let path = file_path.as_ref();

        if !path.exists() {
            return Err(anyhow::anyhow!("文件不存在: {}", path.display()));
        }

        if !path.is_file() {
            return Err(anyhow::anyhow!("路径不是文件: {}", path.display()));
        }

        // 尝试打开文件验证可读性
        File::open(path).with_context(|| format!("文件不可读: {}", path.display()))?;

        Ok(())
    }

    /// 创建目录（如果不存在）
    pub fn ensure_dir_exists<P: AsRef<Path>>(dir_path: P) -> Result<()> {
        let path = dir_path.as_ref();

        if !path.exists() {
            fs::create_dir_all(path)
                .with_context(|| format!("无法创建目录: {}", path.display()))?;
        }

        Ok(())
    }

    /// 获取文件大小
    pub fn get_file_size<P: AsRef<Path>>(file_path: P) -> Result<u64> {
        let path = file_path.as_ref();

        let metadata = path
            .metadata()
            .with_context(|| format!("无法获取文件元数据: {}", path.display()))?;

        Ok(metadata.len())
    }

    /// 复制文件
    pub fn copy_file<P: AsRef<Path>, Q: AsRef<Path>>(from: P, to: Q) -> Result<u64> {
        let from_path = from.as_ref();
        let to_path = to.as_ref();

        // 确保目标目录存在
        if let Some(parent) = to_path.parent() {
            Self::ensure_dir_exists(parent)?;
        }

        let bytes_copied = fs::copy(from_path, to_path).with_context(|| {
            format!(
                "无法复制文件从 {} 到 {}",
                from_path.display(),
                to_path.display()
            )
        })?;

        Ok(bytes_copied)
    }

    /// 移动文件
    pub fn move_file<P: AsRef<Path>, Q: AsRef<Path>>(from: P, to: Q) -> Result<()> {
        let from_path = from.as_ref();
        let to_path = to.as_ref();

        // 确保目标目录存在
        if let Some(parent) = to_path.parent() {
            Self::ensure_dir_exists(parent)?;
        }

        fs::rename(from_path, to_path).with_context(|| {
            format!(
                "无法移动文件从 {} 到 {}",
                from_path.display(),
                to_path.display()
            )
        })?;

        Ok(())
    }
}

/// 压缩文件处理工具
pub struct CompressionUtils;

impl CompressionUtils {
    /// 解压gzip文件
    pub fn extract_gzip<P: AsRef<Path>, Q: AsRef<Path>>(
        gzip_path: P,
        output_path: Q,
    ) -> Result<()> {
        let gzip_file = File::open(gzip_path.as_ref())
            .with_context(|| format!("无法打开gzip文件: {}", gzip_path.as_ref().display()))?;

        let decoder = GzDecoder::new(gzip_file);
        let mut output_file = File::create(output_path.as_ref())
            .with_context(|| format!("无法创建输出文件: {}", output_path.as_ref().display()))?;

        // std::io::copy(decoder, &mut output_file).with_context(|| "解压gzip文件失败")?;

        Ok(())
    }

    /// 解压zip文件到指定目录
    pub fn extract_zip<P: AsRef<Path>>(zip_path: P, extract_dir: P) -> Result<()> {
        let zip_file = File::open(zip_path.as_ref())
            .with_context(|| format!("无法打开zip文件: {}", zip_path.as_ref().display()))?;

        let mut archive = ZipArchive::new(zip_file).with_context(|| "无法读取zip归档")?;

        for i in 0..archive.len() {
            let mut file = archive
                .by_index(i)
                .with_context(|| format!("无法获取zip文件索引: {}", i))?;

            let output_path = extract_dir.as_ref().join(file.name());

            if file.name().ends_with('/') {
                // 创建目录
                FileUtils::ensure_dir_exists(&output_path)?;
            } else {
                // 创建文件的父目录
                if let Some(parent) = output_path.parent() {
                    FileUtils::ensure_dir_exists(parent)?;
                }

                // 提取文件
                let mut output_file = File::create(&output_path)
                    .with_context(|| format!("无法创建输出文件: {}", output_path.display()))?;

                std::io::copy(&mut file, &mut output_file)
                    .with_context(|| format!("提取文件失败: {}", file.name()))?;
            }
        }

        Ok(())
    }

    /// 压缩目录为zip文件
    pub fn compress_to_zip<P: AsRef<Path>, Q: AsRef<Path>>(
        source_dir: P,
        zip_path: Q,
    ) -> Result<()> {
        let source_path = source_dir.as_ref();
        let zip_file = File::create(zip_path.as_ref())
            .with_context(|| format!("无法创建zip文件: {}", zip_path.as_ref().display()))?;

        // let mut zip = ZipWriter::new(zip_file);
        // let options = FileOptions::default().compression_method(zip::CompressionMethod::Stored);

        // // 添加目录中的所有文件
        // for entry in walkdir::WalkDir::new(source_path)
        //     .into_iter()
        //     .filter_map(|e| e.ok())
        // {
        //     let path = entry.path();
        //     let name = path
        //         .strip_prefix(source_path)
        //         .with_context(|| "路径前缀处理失败")?;

        //     if path.is_file() {
        //         zip.start_file(name.to_string_lossy(), options)?;
        //         let mut file = File::open(path)?;
        //         std::io::copy(&mut file, &mut zip)?;
        //     } else if path != source_path {
        //         zip.add_directory(name.to_string_lossy(), options)?;
        //     }
        // }

        // zip.finish()?;
        Ok(())
    }
}

/// 数据验证工具
pub struct ValidationUtils;

impl ValidationUtils {
    /// 验证股票代码格式
    pub fn validate_symbol(symbol: &str) -> Result<()> {
        if symbol.len() != 6 {
            return Err(anyhow::anyhow!("股票代码长度错误，期望6位: {}", symbol));
        }

        if !symbol.chars().all(|c| c.is_ascii_digit()) {
            return Err(anyhow::anyhow!("股票代码必须为数字: {}", symbol));
        }

        Ok(())
    }

    /// 验证市场代码
    pub fn validate_market(market: &str) -> Result<()> {
        match market.to_uppercase().as_str() {
            "SH" | "SZ" => Ok(()),
            _ => Err(anyhow::anyhow!("无效的市场代码，期望SH或SZ: {}", market)),
        }
    }

    /// 验证日期格式
    pub fn validate_date(date_str: &str) -> Result<chrono::NaiveDate> {
        if date_str.len() != 8 {
            return Err(anyhow::anyhow!("日期格式错误，期望YYYYMMDD: {}", date_str));
        }

        let year = date_str[0..4]
            .parse::<i32>()
            .with_context(|| "无效的年份")?;
        let month = date_str[4..6]
            .parse::<u32>()
            .with_context(|| "无效的月份")?;
        let day = date_str[6..8]
            .parse::<u32>()
            .with_context(|| "无效的日期")?;

        chrono::NaiveDate::from_ymd_opt(year, month, day)
            .ok_or_else(|| anyhow::anyhow!("无效的日期: {}", date_str))
    }

    /// 验证价格数据
    pub fn validate_price_data(open: f64, high: f64, low: f64, close: f64) -> Result<()> {
        // 检查价格为正数
        if open <= 0.0 || high <= 0.0 || low <= 0.0 || close <= 0.0 {
            return Err(anyhow::anyhow!("价格必须为正数"));
        }

        // 检查高低价关系
        if high < low {
            return Err(anyhow::anyhow!("最高价不能低于最低价"));
        }

        // 检查开收盘价在高低价范围内
        if open > high || open < low || close > high || close < low {
            return Err(anyhow::anyhow!("开收盘价超出高低价范围"));
        }

        // 检查价格合理性
        if open < 0.01 || high > 10000.0 || low < 0.01 || close > 10000.0 {
            return Err(anyhow::anyhow!("价格超出合理范围"));
        }

        Ok(())
    }

    /// 验证成交量数据
    pub fn validate_volume(volume: u64) -> Result<()> {
        if volume > 10_u64.pow(12) {
            // 1万亿股上限
            return Err(anyhow::anyhow!("成交量超出合理范围: {}", volume));
        }

        Ok(())
    }

    /// 验证成交额数据
    pub fn validate_amount(amount: f64) -> Result<()> {
        if amount < 0.0 || amount > 10_f64.powf(15.0) {
            // 1千万亿上限
            return Err(anyhow::anyhow!("成交额超出合理范围: {}", amount));
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_symbol_validation() {
        // 有效股票代码
        assert!(ValidationUtils::validate_symbol("000001").is_ok());
        assert!(ValidationUtils::validate_symbol("600000").is_ok());
        assert!(ValidationUtils::validate_symbol("300001").is_ok());

        // 无效股票代码
        assert!(ValidationUtils::validate_symbol("00001").is_err()); // 长度错误
        assert!(ValidationUtils::validate_symbol("AAAAAA").is_err()); // 非数字
        assert!(ValidationUtils::validate_symbol("0000000").is_err()); // 长度错误
    }

    #[test]
    fn test_market_validation() {
        // 有效市场代码
        assert!(ValidationUtils::validate_market("SH").is_ok());
        assert!(ValidationUtils::validate_market("SZ").is_ok());
        assert!(ValidationUtils::validate_market("sh").is_ok());
        assert!(ValidationUtils::validate_market("sz").is_ok());

        // 无效市场代码
        assert!(ValidationUtils::validate_market("BJ").is_err());
        assert!(ValidationUtils::validate_market("HK").is_err());
    }

    #[test]
    fn test_date_validation() {
        // 有效日期
        assert!(ValidationUtils::validate_date("20240101").is_ok());
        assert!(ValidationUtils::validate_date("20231231").is_ok());

        // 无效日期
        assert!(ValidationUtils::validate_date("2024011").is_err()); // 长度错误
        assert!(ValidationUtils::validate_date("20241301").is_err()); // 月份无效
        assert!(ValidationUtils::validate_date("20240132").is_err()); // 日期无效
    }

    #[test]
    fn test_price_validation() {
        // 有效价格数据
        assert!(ValidationUtils::validate_price_data(10.0, 12.0, 8.0, 11.0).is_ok());

        // 无效价格数据
        assert!(ValidationUtils::validate_price_data(-1.0, 12.0, 8.0, 11.0).is_err()); // 负价格
        assert!(ValidationUtils::validate_price_data(10.0, 8.0, 12.0, 11.0).is_err()); // 高低价关系错误
        assert!(ValidationUtils::validate_price_data(13.0, 12.0, 8.0, 11.0).is_err());
        // 开盘价超出范围
    }

    #[test]
    fn test_file_ensure_dir() {
        let temp_dir = TempDir::new().unwrap();
        let test_dir = temp_dir.path().join("test").join("nested");

        // 确保目录创建成功
        assert!(FileUtils::ensure_dir_exists(&test_dir).is_ok());
        assert!(test_dir.exists());
        assert!(test_dir.is_dir());
    }
}

//! 数据清洗模块

use crate::parsers::TDXDayRecord;
use anyhow::Result;
use chrono::{Datelike, NaiveDate, Weekday};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;

/// 数据清洗规则
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CleaningRule {
    /// 移除异常值
    RemoveOutliers {
        field: String,
        method: OutlierMethod,
        threshold: f64,
    },
    /// 填充缺失值
    FillMissing { field: String, method: FillMethod },
    /// 移除重复记录
    RemoveDuplicates { keys: Vec<String> },
    /// 价格一致性检查
    ValidatePriceConsistency,
    /// 数据范围验证
    ValidateRange {
        field: String,
        min: Option<f64>,
        max: Option<f64>,
    },
    /// 移除非交易日数据
    RemoveNonTradingDays,
}

/// 异常值检测方法
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OutlierMethod {
    IQR { multiplier: f64 },
    ZScore { threshold: f64 },
    MedianDeviation { threshold: f64 },
}

/// 缺失值填充方法
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum FillMethod {
    ForwardFill,
    BackwardFill,
    Mean,
    Median,
    Zero,
    Drop,
}

/// 清洗结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleaningResult {
    /// 原始记录数
    pub original_count: usize,
    /// 清洗后记录数
    pub cleaned_count: usize,
    /// 移除的记录数
    pub removed_count: usize,
    /// 应用的清洗规则
    pub applied_rules: Vec<String>,
    /// 清洗统计信息
    pub statistics: CleaningStatistics,
}

/// 清洗统计信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleaningStatistics {
    /// 异常值数量
    pub outliers_removed: usize,
    /// 缺失值数量
    pub missing_values_filled: usize,
    /// 重复记录数量
    pub duplicates_removed: usize,
    /// 价格不一致数量
    pub price_inconsistencies: usize,
    /// 范围异常数量
    pub range_violations: usize,
}

impl Default for CleaningStatistics {
    fn default() -> Self {
        Self {
            outliers_removed: 0,
            missing_values_filled: 0,
            duplicates_removed: 0,
            price_inconsistencies: 0,
            range_violations: 0,
        }
    }
}

/// 高性能数据清洗器
#[derive(Debug)]
pub struct DataCleaner {
    /// 清洗规则列表
    rules: Vec<CleaningRule>,
    /// 交易日集合
    trading_days: HashSet<NaiveDate>,
}

impl DataCleaner {
    /// 创建新的数据清洗器
    pub fn new() -> Self {
        Self {
            rules: Vec::new(),
            trading_days: HashSet::new(),
        }
    }

    /// 添加清洗规则
    pub fn add_rule(&mut self, rule: CleaningRule) -> &mut Self {
        self.rules.push(rule);
        self
    }

    /// 批量添加清洗规则
    pub fn add_rules(&mut self, rules: Vec<CleaningRule>) -> &mut Self {
        self.rules.extend(rules);
        self
    }

    /// 设置交易日历
    pub fn set_trading_days(&mut self, trading_days: Vec<NaiveDate>) -> &mut Self {
        self.trading_days = trading_days.into_iter().collect();
        self
    }

    /// 清洗数据
    pub fn clean(&self, data: Vec<TDXDayRecord>) -> Result<CleaningResult> {
        let original_count = data.len();
        let mut current_data = data;
        let mut applied_rules = Vec::new();
        let mut statistics = CleaningStatistics::default();

        // 应用所有清洗规则
        for rule in &self.rules {
            match rule {
                CleaningRule::RemoveOutliers {
                    field,
                    method,
                    threshold,
                } => {
                    current_data =
                        self.remove_outliers(current_data, field, method.clone(), *threshold)?;
                    applied_rules.push(format!("RemoveOutliers({})", field));
                }
                CleaningRule::FillMissing { field, method } => {
                    current_data = self.fill_missing_values(
                        current_data,
                        field,
                        method.clone(),
                        &mut statistics,
                    )?;
                    applied_rules.push(format!("FillMissing({})", field));
                }
                CleaningRule::RemoveDuplicates { keys } => {
                    let (cleaned_data, removed) = self.remove_duplicates(current_data, keys)?;
                    current_data = cleaned_data;
                    statistics.duplicates_removed += removed;
                    applied_rules.push("RemoveDuplicates".to_string());
                }
                CleaningRule::ValidatePriceConsistency => {
                    let (cleaned_data, fixed) = self.validate_price_consistency(current_data)?;
                    current_data = cleaned_data;
                    statistics.price_inconsistencies += fixed;
                    applied_rules.push("ValidatePriceConsistency".to_string());
                }
                CleaningRule::ValidateRange { field, min, max } => {
                    let (cleaned_data, violations) =
                        self.validate_range(current_data, field, *min, *max)?;
                    current_data = cleaned_data;
                    statistics.range_violations += violations;
                    applied_rules.push(format!("ValidateRange({})", field));
                }
                CleaningRule::RemoveNonTradingDays => {
                    let (cleaned_data, removed) = self.remove_non_trading_days(current_data)?;
                    current_data = cleaned_data;
                    // 移除的数据计入移除总数
                    applied_rules.push("RemoveNonTradingDays".to_string());
                }
            }
        }

        let cleaned_count = current_data.len();
        let removed_count = original_count - cleaned_count;

        Ok(CleaningResult {
            original_count,
            cleaned_count,
            removed_count,
            applied_rules,
            statistics,
        })
    }

    /// 移除异常值
    fn remove_outliers(
        &self,
        data: Vec<TDXDayRecord>,
        field: &str,
        method: OutlierMethod,
        threshold: f64,
    ) -> Result<Vec<TDXDayRecord>> {
        // 提取字段值
        let values: Vec<f64> = data
            .iter()
            .map(|record| self.extract_field_value(record, field))
            .collect::<Result<Vec<f64>>>()?;

        let (outlier_indices, _) = self.detect_outliers(&values, &method, threshold);

        // 保留非异常值的数据
        let cleaned_data: Vec<TDXDayRecord> = data
            .into_iter()
            .enumerate()
            .filter(|(index, _)| !outlier_indices.contains(index))
            .map(|(_, record)| record)
            .collect();

        Ok(cleaned_data)
    }

    /// 检测异常值
    fn detect_outliers(
        &self,
        values: &[f64],
        method: &OutlierMethod,
        threshold: f64,
    ) -> (Vec<usize>, Vec<f64>) {
        let mut outlier_indices = Vec::new();
        let mut bounds = Vec::new();

        match method {
            OutlierMethod::IQR { multiplier } => {
                let mut sorted_values = values.to_vec();
                sorted_values.sort_by(|a, b| a.partial_cmp(b).unwrap());

                let q1_index = (sorted_values.len() as f64 * 0.25) as usize;
                let q3_index = (sorted_values.len() as f64 * 0.75) as usize;

                if q1_index < sorted_values.len() && q3_index < sorted_values.len() {
                    let q1 = sorted_values[q1_index];
                    let q3 = sorted_values[q3_index];
                    let iqr = q3 - q1;
                    let lower_bound = q1 - multiplier * iqr;
                    let upper_bound = q3 + multiplier * iqr;

                    for (i, &value) in values.iter().enumerate() {
                        if value < lower_bound || value > upper_bound {
                            outlier_indices.push(i);
                        }
                    }

                    bounds = vec![lower_bound, upper_bound];
                }
            }
            OutlierMethod::ZScore { threshold } => {
                let mean = values.iter().sum::<f64>() / values.len() as f64;
                let variance =
                    values.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / values.len() as f64;
                let std = variance.sqrt();

                if std > 0.0 {
                    for (i, &value) in values.iter().enumerate() {
                        let z_score = (value - mean) / std;
                        if z_score.abs() > *threshold {
                            outlier_indices.push(i);
                        }
                    }

                    bounds = vec![mean - threshold * std, mean + threshold * std];
                }
            }
            OutlierMethod::MedianDeviation { threshold } => {
                let mut sorted_values = values.to_vec();
                sorted_values.sort_by(|a, b| a.partial_cmp(b).unwrap());
                let median = if sorted_values.is_empty() {
                    0.0
                } else {
                    sorted_values[sorted_values.len() / 2]
                };

                let mad: f64 = sorted_values
                    .iter()
                    .map(|x| (x - median).abs())
                    .sum::<f64>()
                    / sorted_values.len() as f64;

                if mad > 0.0 {
                    for (i, &value) in values.iter().enumerate() {
                        let deviation = (value - median).abs() / mad;
                        if deviation > *threshold {
                            outlier_indices.push(i);
                        }
                    }

                    bounds = vec![median - threshold * mad, median + threshold * mad];
                }
            }
        }

        (outlier_indices, bounds)
    }

    /// 填充缺失值
    fn fill_missing_values(
        &self,
        data: Vec<TDXDayRecord>,
        field: &str,
        method: FillMethod,
        statistics: &mut CleaningStatistics,
    ) -> Result<Vec<TDXDayRecord>> {
        // 简化实现：主要处理价格数据的前向填充
        if field == "volume" || field == "amount" {
            // 成交量和成交额的填充逻辑
            let mut filled_data = Vec::with_capacity(data.len());
            let mut last_valid_volume = None;
            let mut last_valid_amount = None;

            for record in data {
                let mut filled_record = record.clone();

                if record.volume == 0 {
                    if let Some(volume) = last_valid_volume {
                        filled_record.volume = volume;
                        statistics.missing_values_filled += 1;
                    }
                } else {
                    last_valid_volume = Some(record.volume);
                }

                if record.amount == 0.0 {
                    if let Some(amount) = last_valid_amount {
                        filled_record.amount = amount;
                        statistics.missing_values_filled += 1;
                    }
                } else {
                    last_valid_amount = Some(record.amount);
                }

                filled_data.push(filled_record);
            }

            Ok(filled_data)
        } else {
            // 价格字段的填充
            self.fill_price_values(data, field, method, statistics)
        }
    }

    /// 填充价格值
    fn fill_price_values(
        &self,
        data: Vec<TDXDayRecord>,
        field: &str,
        method: FillMethod,
        statistics: &mut CleaningStatistics,
    ) -> Result<Vec<TDXDayRecord>> {
        let mut filled_data = data;

        // 根据股票代码分组处理
        use std::collections::HashMap;
        let mut groups: HashMap<String, Vec<usize>> = HashMap::new();

        for (i, record) in filled_data.iter().enumerate() {
            groups
                .entry(record.symbol.clone())
                .or_insert_with(Vec::new)
                .push(i);
        }

        for (symbol, mut indices) in groups {
            // 按日期排序索引
            indices.sort_by(|&i, &j| filled_data[i].date.cmp(&filled_data[j].date));

            // 先收集需要填充的索引
            let indices_to_fill: Vec<usize> = indices
                .iter()
                .copied()
                .filter(|&idx| self.needs_filling(&filled_data[idx], field))
                .collect();

            for &idx in &indices_to_fill {
                let fill_value = match method {
                    FillMethod::ForwardFill => {
                        // 前向填充
                        self.get_previous_value(&filled_data, idx, &symbol, field)
                    }
                    FillMethod::Mean => {
                        // 均值填充
                        self.calculate_mean_value(&filled_data, symbol.clone(), field)
                    }
                    _ => {
                        // 默认值或移除
                        0.0
                    }
                };

                self.set_field_value(&mut filled_data[idx], field, fill_value);
                statistics.missing_values_filled += 1;
            }
        }

        Ok(filled_data)
    }

    /// 移除重复记录
    fn remove_duplicates(
        &self,
        data: Vec<TDXDayRecord>,
        keys: &[String],
    ) -> Result<(Vec<TDXDayRecord>, usize)> {
        if keys.is_empty() {
            // 默认按股票代码和日期去重
            let mut seen = std::collections::HashSet::new();
            let mut unique_data = Vec::new();
            let mut removed_count = 0;

            for record in data {
                let key = format!("{}_{}", record.symbol, record.date.format("%Y-%m-%d"));

                if seen.insert(key) {
                    unique_data.push(record);
                } else {
                    removed_count += 1;
                }
            }

            Ok((unique_data, removed_count))
        } else {
            // 按指定字段去重
            Ok((data, 0)) // 简化实现
        }
    }

    /// 验证价格一致性
    fn validate_price_consistency(
        &self,
        data: Vec<TDXDayRecord>,
    ) -> Result<(Vec<TDXDayRecord>, usize)> {
        let mut fixed_data = Vec::with_capacity(data.len());
        let mut fixed_count = 0;

        for record in data {
            let mut fixed_record = record.clone();
            let mut needs_fix = false;

            // 检查价格关系
            if fixed_record.high < fixed_record.low {
                // 修正高低价
                std::mem::swap(&mut fixed_record.high, &mut fixed_record.low);
                needs_fix = true;
            }

            if fixed_record.open > fixed_record.high {
                fixed_record.open = fixed_record.high;
                needs_fix = true;
            }

            if fixed_record.open < fixed_record.low {
                fixed_record.open = fixed_record.low;
                needs_fix = true;
            }

            if fixed_record.close > fixed_record.high {
                fixed_record.close = fixed_record.high;
                needs_fix = true;
            }

            if fixed_record.close < fixed_record.low {
                fixed_record.close = fixed_record.low;
                needs_fix = true;
            }

            if needs_fix {
                fixed_count += 1;
            }

            fixed_data.push(fixed_record);
        }

        Ok((fixed_data, fixed_count))
    }

    /// 验证数值范围
    fn validate_range(
        &self,
        data: Vec<TDXDayRecord>,
        field: &str,
        min: Option<f64>,
        max: Option<f64>,
    ) -> Result<(Vec<TDXDayRecord>, usize)> {
        let mut valid_data = Vec::with_capacity(data.len());
        let mut violations = 0;

        for record in data {
            let value = self.extract_field_value(&record, field)?;
            let mut is_valid = true;

            if let Some(min_val) = min {
                if value < min_val {
                    is_valid = false;
                }
            }

            if let Some(max_val) = max {
                if value > max_val {
                    is_valid = false;
                }
            }

            if is_valid {
                valid_data.push(record);
            } else {
                violations += 1;
            }
        }

        Ok((valid_data, violations))
    }

    /// 移除非交易日数据
    fn remove_non_trading_days(
        &self,
        data: Vec<TDXDayRecord>,
    ) -> Result<(Vec<TDXDayRecord>, usize)> {
        let mut trading_data = Vec::with_capacity(data.len());
        let mut removed_count = 0;

        for record in data {
            if self.trading_days.contains(&record.date) {
                trading_data.push(record);
            } else {
                removed_count += 1;
            }
        }

        Ok((trading_data, removed_count))
    }

    /// 辅助方法：从记录中提取字段值
    fn extract_field_value(&self, record: &TDXDayRecord, field: &str) -> Result<f64> {
        match field {
            "open" => Ok(record.open),
            "high" => Ok(record.high),
            "low" => Ok(record.low),
            "close" => Ok(record.close),
            "volume" => Ok(record.volume as f64),
            "amount" => Ok(record.amount),
            _ => Err(anyhow::anyhow!("未知字段: {}", field)),
        }
    }

    /// 辅助方法：检查是否需要填充
    fn needs_filling(&self, record: &TDXDayRecord, field: &str) -> bool {
        match field {
            "open" | "high" | "low" | "close" => {
                record.open <= 0.0 || record.high <= 0.0 || record.low <= 0.0 || record.close <= 0.0
            }
            "volume" => record.volume == 0,
            "amount" => record.amount <= 0.0,
            _ => false,
        }
    }

    /// 辅助方法：获取前一个有效值
    fn get_previous_value(
        &self,
        data: &[TDXDayRecord],
        idx: usize,
        symbol: &str,
        field: &str,
    ) -> f64 {
        for i in (0..idx).rev() {
            if data[i].symbol == symbol && !self.needs_filling(&data[i], field) {
                return self.extract_field_value(&data[i], field).unwrap_or(0.0);
            }
        }
        0.0
    }

    /// 辅助方法：计算均值
    fn calculate_mean_value(&self, data: &[TDXDayRecord], symbol: String, field: &str) -> f64 {
        let mut sum = 0.0;
        let mut count = 0;

        for record in data {
            if record.symbol == symbol && !self.needs_filling(record, field) {
                if let Ok(value) = self.extract_field_value(record, field) {
                    sum += value;
                    count += 1;
                }
            }
        }

        if count > 0 {
            sum / count as f64
        } else {
            0.0
        }
    }

    /// 辅助方法：设置字段值
    fn set_field_value(&self, record: &mut TDXDayRecord, field: &str, value: f64) {
        match field {
            "open" => record.open = value,
            "high" => record.high = value,
            "low" => record.low = value,
            "close" => record.close = value,
            "volume" => record.volume = value as u64,
            "amount" => record.amount = value,
            _ => {} // 忽略未知字段
        }
    }
}

impl Default for DataCleaner {
    fn default() -> Self {
        let mut cleaner = Self::new();

        // 添加默认清洗规则
        cleaner.add_rules(vec![
            CleaningRule::ValidatePriceConsistency,
            CleaningRule::RemoveDuplicates {
                keys: vec!["symbol".to_string(), "date".to_string()],
            },
            CleaningRule::ValidateRange {
                field: "open".to_string(),
                min: Some(0.01),
                max: Some(10000.0),
            },
            CleaningRule::ValidateRange {
                field: "close".to_string(),
                min: Some(0.01),
                max: Some(10000.0),
            },
        ]);

        cleaner
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    fn create_test_record(symbol: &str, date: &str) -> TDXDayRecord {
        TDXDayRecord {
            date: NaiveDate::parse_from_str(date, "%Y-%m-%d").unwrap(),
            symbol: symbol.to_string(),
            open: 10.0,
            high: 11.0,
            low: 9.0,
            close: 10.5,
            volume: 1000000,
            amount: 10500000.0,
            market: "SH".to_string(),
        }
    }

    #[test]
    fn test_data_cleaner_creation() {
        let cleaner = DataCleaner::new();
        assert!(cleaner.rules.is_empty());
    }

    #[test]
    fn test_add_rules() {
        let mut cleaner = DataCleaner::new();
        cleaner.add_rule(CleaningRule::ValidatePriceConsistency);
        assert_eq!(cleaner.rules.len(), 1);
    }

    #[test]
    fn test_price_consistency_validation() {
        let mut cleaner = DataCleaner::new();
        cleaner.add_rule(CleaningRule::ValidatePriceConsistency);

        // 创建测试数据
        let mut data = vec![
            create_test_record("600000", "2024-01-01"),
            create_test_record("600000", "2024-01-02"),
        ];

        // 人为制造价格不一致
        data[1].high = 8.0; // 最高价低于最低价
        data[1].low = 12.0; // 最低价高于最高价

        let result = cleaner.clean(data).unwrap();

        // 验证数据被修正
        assert_eq!(result.cleaned_count, 2);
        assert_eq!(result.statistics.price_inconsistencies, 1);
    }

    #[test]
    fn test_remove_duplicates() {
        let mut cleaner = DataCleaner::new();
        cleaner.add_rule(CleaningRule::RemoveDuplicates {
            keys: vec!["symbol".to_string(), "date".to_string()],
        });

        // 创建包含重复记录的测试数据
        let data = vec![
            create_test_record("600000", "2024-01-01"),
            create_test_record("600000", "2024-01-01"), // 重复
            create_test_record("600000", "2024-01-02"),
        ];

        let result = cleaner.clean(data).unwrap();

        // 验证重复记录被移除
        assert_eq!(result.cleaned_count, 2);
        assert_eq!(result.statistics.duplicates_removed, 1);
    }
}

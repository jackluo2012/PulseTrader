//! 数据聚合模块

use crate::parsers::tdx_day::TDXDayRecord;
use anyhow::Result;
use chrono::{DateTime, NaiveDate, Utc};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// 聚合规则
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AggregationRule {
    /// 按时间窗口聚合
    TimeWindow {
        window_size: usize,
        function: AggregationFunction,
    },
    /// 按股票代码分组聚合
    GroupBySymbol { function: AggregationFunction },
    /// 按日期范围聚合
    DateRange {
        start_date: NaiveDate,
        end_date: NaiveDate,
        function: AggregationFunction,
    },
    /// 自定义聚合
    Custom {
        name: String,
        rule: String, // 规则表达式或配置
        function: AggregationFunction,
    },
}

/// 聚合函数
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AggregationFunction {
    /// 求和
    Sum { field: String },
    /// 平均值
    Mean { field: String },
    /// 最大值
    Max { field: String },
    /// 最小值
    Min { field: String },
    /// 中位数
    Median { field: String },
    /// 计数
    Count,
    /// 第一个值
    First { field: String },
    /// 最后一个值
    Last { field: String },
    /// 标准差
    StdDev { field: String },
    /// 方差
    Variance { field: String },
    /// 加权平均
    WeightedMean {
        value_field: String,
        weight_field: String,
    },
    /// 自定义函数
    Custom { name: String, fields: Vec<String> },
}

/// 聚合结果
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregationResult {
    /// 聚合标识
    pub aggregation_id: String,
    /// 规则名称
    pub rule_name: String,
    /// 原始记录数
    pub original_count: usize,
    /// 聚合后记录数
    pub aggregated_count: usize,
    /// 聚合值
    pub values: Vec<AggregatedValue>,
    /// 时间戳
    pub timestamp: DateTime<Utc>,
}

/// 聚合值
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregatedValue {
    /// 聚合键（如股票代码、日期等）
    pub key: String,
    /// 聚合值
    pub value: f64,
    /// 数量（如果是计数聚合）
    pub count: Option<usize>,
    /// 额外信息
    pub metadata: HashMap<String, String>,
}

/// 高性能数据聚合器
#[derive(Debug)]
pub struct DataAggregator {
    /// 聚合规则列表
    rules: Vec<AggregationRule>,
    /// 缓存聚合结果
    cache: HashMap<String, AggregationResult>,
}

impl DataAggregator {
    /// 创建新的数据聚合器
    pub fn new() -> Self {
        Self {
            rules: Vec::new(),
            cache: HashMap::new(),
        }
    }

    /// 添加聚合规则
    pub fn add_rule(&mut self, rule: AggregationRule) -> &mut Self {
        self.rules.push(rule);
        self
    }

    /// 批量添加聚合规则
    pub fn add_rules(&mut self, rules: Vec<AggregationRule>) -> &mut Self {
        self.rules.extend(rules);
        self
    }

    /// 执行所有聚合规则
    pub fn aggregate(&self, data: &[TDXDayRecord]) -> Result<Vec<AggregationResult>> {
        let mut results = Vec::with_capacity(self.rules.len());

        for rule in &self.rules {
            let result = self.apply_rule(data, rule)?;
            results.push(result);
        }

        Ok(results)
    }

    /// 应用单个聚合规则
    fn apply_rule(
        &self,
        data: &[TDXDayRecord],
        rule: &AggregationRule,
    ) -> Result<AggregationResult> {
        match rule {
            AggregationRule::TimeWindow {
                window_size,
                function,
            } => self.aggregate_time_window(data, *window_size, function),
            AggregationRule::GroupBySymbol { function } => self.aggregate_by_symbol(data, function),
            AggregationRule::DateRange {
                start_date,
                end_date,
                function,
            } => self.aggregate_by_date_range(data, start_date, end_date, function),
            AggregationRule::Custom {
                name,
                rule: _,
                function,
            } => {
                // 简化实现：按名称调用对应的聚合方法
                self.aggregate_custom(data, name, function)
            }
        }
    }

    /// 时间窗口聚合
    fn aggregate_time_window(
        &self,
        data: &[TDXDayRecord],
        window_size: usize,
        function: &AggregationFunction,
    ) -> Result<AggregationResult> {
        let original_count = data.len();
        let mut aggregated_values = Vec::new();

        // 按股票分组后进行时间窗口聚合
        let mut symbol_groups: HashMap<String, Vec<TDXDayRecord>> = HashMap::new();
        for record in data {
            symbol_groups
                .entry(record.symbol.clone())
                .or_insert_with(Vec::new)
                .push(record.clone());
        }

        for (symbol, records) in symbol_groups {
            // 按日期排序
            let mut sorted_records: Vec<TDXDayRecord> = records.clone();
            sorted_records.sort_by(|a, b| a.date.cmp(&b.date));

            // 滑动窗口聚合
            for window in sorted_records.chunks(window_size) {
                if window.len() == window_size {
                    let value = self.apply_aggregation_function(window, function)?;
                    aggregated_values.push(AggregatedValue {
                        key: format!("{}_{}", symbol, window[0].date),
                        value,
                        count: Some(window.len()),
                        metadata: {
                            let mut meta = HashMap::new();
                            meta.insert("symbol".to_string(), symbol.clone());
                            meta.insert("window_size".to_string(), window_size.to_string());
                            meta.insert("start_date".to_string(), window[0].date.to_string());
                            meta.insert(
                                "end_date".to_string(),
                                window[window.len() - 1].date.to_string(),
                            );
                            meta
                        },
                    });
                }
            }
        }

        Ok(AggregationResult {
            aggregation_id: format!("time_window_{}", window_size),
            rule_name: "TimeWindow".to_string(),
            original_count,
            aggregated_count: aggregated_values.len(),
            values: aggregated_values,
            timestamp: Utc::now(),
        })
    }

    /// 按股票代码聚合
    fn aggregate_by_symbol(
        &self,
        data: &[TDXDayRecord],
        function: &AggregationFunction,
    ) -> Result<AggregationResult> {
        let original_count = data.len();
        let mut aggregated_values = Vec::new();

        // 按股票分组
        let mut symbol_groups: HashMap<String, Vec<TDXDayRecord>> = HashMap::new();
        for record in data {
            symbol_groups
                .entry(record.symbol.clone())
                .or_insert_with(Vec::new)
                .push(record.clone());
        }

        // 对每个股票组应用聚合函数
        for (symbol, records) in symbol_groups {
            let value = self.apply_aggregation_function(&records, function)?;
            aggregated_values.push(AggregatedValue {
                key: symbol.clone(),
                value,
                count: Some(records.len()),
                metadata: {
                    let mut meta = HashMap::new();
                    meta.insert("symbol".to_string(), symbol.clone());
                    meta.insert("record_count".to_string(), records.len().to_string());
                    meta
                },
            });
        }

        Ok(AggregationResult {
            aggregation_id: "group_by_symbol".to_string(),
            rule_name: "GroupBySymbol".to_string(),
            original_count,
            aggregated_count: aggregated_values.len(),
            values: aggregated_values,
            timestamp: Utc::now(),
        })
    }

    /// 按日期范围聚合
    fn aggregate_by_date_range(
        &self,
        data: &[TDXDayRecord],
        start_date: &NaiveDate,
        end_date: &NaiveDate,
        function: &AggregationFunction,
    ) -> Result<AggregationResult> {
        let original_count = data.len();
        let mut aggregated_values = Vec::new();

        // 过滤日期范围内的记录
        let filtered_records: Vec<TDXDayRecord> = data
            .iter()
            .filter(|record| &record.date >= start_date && &record.date <= end_date)
            .cloned()
            .collect();

        if !filtered_records.is_empty() {
            let value = self.apply_aggregation_function(&filtered_records, function)?;
            aggregated_values.push(AggregatedValue {
                key: format!("{}_{}", start_date, end_date),
                value,
                count: Some(filtered_records.len()),
                metadata: {
                    let mut meta = HashMap::new();
                    meta.insert("start_date".to_string(), start_date.to_string());
                    meta.insert("end_date".to_string(), end_date.to_string());
                    meta.insert(
                        "record_count".to_string(),
                        filtered_records.len().to_string(),
                    );
                    meta
                },
            });
        }

        Ok(AggregationResult {
            aggregation_id: format!("date_range_{}_{}", start_date, end_date),
            rule_name: "DateRange".to_string(),
            original_count,
            aggregated_count: aggregated_values.len(),
            values: aggregated_values,
            timestamp: Utc::now(),
        })
    }

    /// 自定义聚合
    fn aggregate_custom(
        &self,
        data: &[TDXDayRecord],
        name: &str,
        function: &AggregationFunction,
    ) -> Result<AggregationResult> {
        let original_count = data.len();
        let mut aggregated_values = Vec::new();

        // 简化实现：对全部数据应用聚合函数
        let value = self.apply_aggregation_function(data, function)?;
        aggregated_values.push(AggregatedValue {
            key: name.to_string(),
            value,
            count: Some(data.len()),
            metadata: {
                let mut meta = HashMap::new();
                meta.insert("aggregation_type".to_string(), "custom".to_string());
                meta.insert("record_count".to_string(), data.len().to_string());
                meta
            },
        });

        Ok(AggregationResult {
            aggregation_id: format!("custom_{}", name),
            rule_name: "Custom".to_string(),
            original_count,
            aggregated_count: aggregated_values.len(),
            values: aggregated_values,
            timestamp: Utc::now(),
        })
    }

    /// 应用聚合函数
    fn apply_aggregation_function(
        &self,
        records: &[TDXDayRecord],
        function: &AggregationFunction,
    ) -> Result<f64> {
        if records.is_empty() {
            return Ok(0.0);
        }

        match function {
            AggregationFunction::Sum { field } => {
                let sum: f64 = records
                    .iter()
                    .map(|r| self.extract_field_value(r, field))
                    .collect::<Result<Vec<f64>>>()?
                    .iter()
                    .sum();
                Ok(sum)
            }
            AggregationFunction::Mean { field } => {
                let values: Vec<f64> = records
                    .iter()
                    .map(|r| self.extract_field_value(r, &field))
                    .collect::<Result<Vec<f64>>>()?;
                let mean = values.iter().sum::<f64>() / values.len() as f64;
                Ok(mean)
            }
            AggregationFunction::Max { field } => {
                let values: Vec<f64> = records
                    .iter()
                    .map(|r| self.extract_field_value(r, &field))
                    .collect::<Result<Vec<f64>>>()?;
                let max = values.iter().fold(f64::MIN, |a, &b| a.max(b));
                Ok(max)
            }
            AggregationFunction::Min { field } => {
                let values: Vec<f64> = records
                    .iter()
                    .map(|r| self.extract_field_value(r, &field))
                    .collect::<Result<Vec<f64>>>()?;
                let min = values.iter().fold(f64::MAX, |a, &b| a.min(b));
                Ok(min)
            }
            AggregationFunction::Median { field } => {
                let mut values: Vec<f64> = records
                    .iter()
                    .map(|r| self.extract_field_value(r, field))
                    .collect::<Result<Vec<f64>>>()?;
                values.sort_by(|a, b| a.partial_cmp(b).unwrap());
                let median = if values.is_empty() {
                    0.0
                } else {
                    values[values.len() / 2]
                };
                Ok(median)
            }
            AggregationFunction::Count => Ok(records.len() as f64),
            AggregationFunction::First { field } => {
                if let Some(record) = records.first() {
                    self.extract_field_value(record, field)
                } else {
                    Ok(0.0)
                }
            }
            AggregationFunction::Last { field } => {
                if let Some(record) = records.last() {
                    self.extract_field_value(record, field)
                } else {
                    Ok(0.0)
                }
            }
            AggregationFunction::StdDev { field } => {
                let values: Vec<f64> = records
                    .iter()
                    .map(|r| self.extract_field_value(r, &field))
                    .collect::<Result<Vec<f64>>>()?;
                let mean = values.iter().sum::<f64>() / values.len() as f64;
                let variance =
                    values.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / values.len() as f64;
                Ok(variance.sqrt())
            }
            AggregationFunction::Variance { field } => {
                let values: Vec<f64> = records
                    .iter()
                    .map(|r| self.extract_field_value(r, &field))
                    .collect::<Result<Vec<f64>>>()?;
                let mean = values.iter().sum::<f64>() / values.len() as f64;
                let variance =
                    values.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / values.len() as f64;
                Ok(variance)
            }
            AggregationFunction::WeightedMean {
                value_field,
                weight_field,
            } => {
                let mut weighted_sum = 0.0;
                let mut weight_sum = 0.0;

                for record in records {
                    let value = self.extract_field_value(record, value_field)?;
                    let weight = self.extract_field_value(record, weight_field)?;
                    weighted_sum += value * weight;
                    weight_sum += weight;
                }

                Ok(if weight_sum > 0.0 {
                    weighted_sum / weight_sum
                } else {
                    0.0
                })
            }
            AggregationFunction::Custom { name: _, fields: _ } => {
                // 简化实现：返回记录数的对数
                Ok((records.len() as f64).log2())
            }
        }
    }

    /// 从记录中提取字段值
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

    /// 并行聚合多个数据集
    pub fn aggregate_parallel(
        &self,
        datasets: &[&[TDXDayRecord]],
    ) -> Result<Vec<Vec<AggregationResult>>> {
        let results: Result<Vec<_>> = datasets
            .into_par_iter()
            .map(|data| self.aggregate(data))
            .collect();

        results
    }

    /// 流式聚合（适用于大数据集）
    pub fn aggregate_stream<I>(
        &self,
        data_stream: I,
        batch_size: usize,
        rule: &AggregationRule,
    ) -> Result<Vec<AggregationResult>>
    where
        I: Iterator<Item = TDXDayRecord>,
    {
        let mut batch = Vec::with_capacity(batch_size);
        let mut results = Vec::new();

        for item in data_stream {
            batch.push(item);

            if batch.len() >= batch_size {
                let result = self.apply_rule(&batch, rule)?;
                results.push(result);
                batch.clear();
            }
        }

        // 处理最后一批
        if !batch.is_empty() {
            let result = self.apply_rule(&batch, rule)?;
            results.push(result);
        }

        Ok(results)
    }

    /// 获取聚合统计信息
    pub fn get_aggregation_stats(&self, results: &[AggregationResult]) -> AggregationStats {
        let total_original: usize = results.iter().map(|r| r.original_count).sum();
        let total_aggregated: usize = results.iter().map(|r| r.aggregated_count).sum();
        let compression_ratio = if total_original > 0 {
            total_aggregated as f64 / total_original as f64
        } else {
            1.0
        };

        AggregationStats {
            total_rules_applied: results.len(),
            total_original_records: total_original,
            total_aggregated_records: total_aggregated,
            compression_ratio,
            processing_time: Utc::now(),
        }
    }
}

/// 聚合统计信息
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregationStats {
    /// 应用的规则总数
    pub total_rules_applied: usize,
    /// 原始记录总数
    pub total_original_records: usize,
    /// 聚合后记录总数
    pub total_aggregated_records: usize,
    /// 压缩比例
    pub compression_ratio: f64,
    /// 处理时间
    pub processing_time: DateTime<Utc>,
}

impl Default for DataAggregator {
    fn default() -> Self {
        let mut aggregator = Self::new();

        // 添加默认聚合规则
        aggregator.add_rules(vec![
            AggregationRule::GroupBySymbol {
                function: AggregationFunction::Mean {
                    field: "close".to_string(),
                },
            },
            AggregationRule::TimeWindow {
                window_size: 5,
                function: AggregationFunction::Mean {
                    field: "close".to_string(),
                },
            },
            AggregationRule::TimeWindow {
                window_size: 20,
                function: AggregationFunction::Mean {
                    field: "volume".to_string(),
                },
            },
        ]);

        aggregator
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
    fn test_data_aggregator_creation() {
        let aggregator = DataAggregator::new();
        assert!(aggregator.rules.is_empty());
    }

    #[test]
    fn test_add_rules() {
        let mut aggregator = DataAggregator::new();
        aggregator.add_rule(AggregationRule::GroupBySymbol {
            function: AggregationFunction::Mean {
                field: "close".to_string(),
            },
        });
        assert_eq!(aggregator.rules.len(), 1);
    }

    #[test]
    fn test_aggregate_by_symbol() {
        let aggregator = DataAggregator::new();
        let data = vec![
            create_test_record("600000", "2024-01-01"),
            create_test_record("600000", "2024-01-02"),
            create_test_record("000001", "2024-01-01"),
        ];

        let rule = AggregationRule::GroupBySymbol {
            function: AggregationFunction::Mean {
                field: "close".to_string(),
            },
        };

        let result = aggregator.apply_rule(&data, &rule).unwrap();
        assert_eq!(result.aggregated_count, 2); // 2个不同的股票
    }

    #[test]
    fn test_time_window_aggregation() {
        let aggregator = DataAggregator::new();
        let data = vec![
            create_test_record("600000", "2024-01-01"),
            create_test_record("600000", "2024-01-02"),
            create_test_record("600000", "2024-01-03"),
            create_test_record("600000", "2024-01-04"),
            create_test_record("600000", "2024-01-05"),
        ];

        let rule = AggregationRule::TimeWindow {
            window_size: 3,
            function: AggregationFunction::Mean {
                field: "close".to_string(),
            },
        };

        let result = aggregator.apply_rule(&data, &rule).unwrap();
        assert_eq!(result.aggregated_count, 3); // 5个记录，3个窗口
    }

    #[test]
    fn test_parallel_aggregation() {
        let aggregator = DataAggregator::new();
        let dataset1 = vec![
            create_test_record("600000", "2024-01-01"),
            create_test_record("600000", "2024-01-02"),
        ];
        let dataset2 = vec![
            create_test_record("000001", "2024-01-01"),
            create_test_record("000001", "2024-01-02"),
        ];

        let datasets = vec![&dataset1[..], &dataset2[..]];
        let results = aggregator.aggregate_parallel(&datasets).unwrap();

        assert_eq!(results.len(), 2);
        for dataset_results in results {
            for result in dataset_results {
                assert!(result.aggregated_count > 0);
            }
        }
    }
}

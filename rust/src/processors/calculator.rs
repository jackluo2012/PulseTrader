//! 技术指标计算模块

use crate::parsers::TDXDayRecord;
use crate::processors::DataCleaner;
use anyhow::Result;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, VecDeque};

/// 技术指标计算器
#[derive(Debug)]
pub struct IndicatorCalculator {
    /// 计算窗口大小
    window_sizes: Vec<usize>,
}

impl IndicatorCalculator {
    /// 创建新的指标计算器
    pub fn new() -> Self {
        Self {
            window_sizes: vec![5, 10, 20, 60],
        }
    }

    /// 设置计算窗口大小
    pub fn with_window_sizes(mut self, window_sizes: Vec<usize>) -> Self {
        self.window_sizes = window_sizes;
        self
    }

    /// 计算所有指标
    pub fn calculate_all_indicators(
        &self,
        data: &[TDXDayRecord],
    ) -> Result<Vec<EnhancedDayRecord>> {
        // 按股票分组
        use std::collections::HashMap;
        let mut groups: HashMap<String, Vec<usize>> = HashMap::new();

        for (i, record) in data.iter().enumerate() {
            groups
                .entry(record.symbol.clone())
                .or_insert_with(Vec::new)
                .push(i);
        }

        // 为每只股票计算指标
        let mut enhanced_records = Vec::with_capacity(data.len());

        for (symbol, indices) in groups {
            // 按日期排序
            let mut sorted_indices = indices.clone();
            sorted_indices.sort_by(|&i, &j| data[i].date.cmp(&data[j].date));

            // 提取该股票的时间序列数据
            let time_series: Vec<&TDXDayRecord> =
                sorted_indices.iter().map(|&idx| &data[idx]).collect();

            // 计算指标
            let calculated_indicators = self.calculate_symbol_indicators(&time_series)?;

            // 合并结果
            for (i, record) in time_series.iter().enumerate() {
                if let Some(Some(indicator_values)) = calculated_indicators.get(i).cloned() {
                    let enhanced = EnhancedDayRecord::from_record(record, indicator_values);
                    enhanced_records.push(enhanced);
                }
            }
        }

        Ok(enhanced_records)
    }

    /// 计算单个股票的指标
    fn calculate_symbol_indicators(
        &self,
        time_series: &[&TDXDayRecord],
    ) -> Result<Vec<Option<IndicatorValues>>> {
        let mut indicators = Vec::with_capacity(time_series.len());

        // 预计算价格序列
        let closes: Vec<f64> = time_series.iter().map(|r| r.close).collect();
        let highs: Vec<f64> = time_series.iter().map(|r| r.high).collect();
        let lows: Vec<f64> = time_series.iter().map(|r| r.low).collect();
        let volumes: Vec<f64> = time_series.iter().map(|r| r.volume as f64).collect();
        let amounts: Vec<f64> = time_series.iter().map(|r| r.amount).collect();

        for i in 0..time_series.len() {
            let mut indicator_values = IndicatorValues::default();

            // 计算移动平均线
            for &window_size in &self.window_sizes {
                if i >= window_size - 1 {
                    let ma = self.calculate_ma(&closes[i - window_size + 1..=i]);
                    match window_size {
                        5 => indicator_values.ma5 = Some(ma),
                        10 => indicator_values.ma10 = Some(ma),
                        20 => indicator_values.ma20 = Some(ma),
                        60 => indicator_values.ma60 = Some(ma),
                        _ => {}
                    }
                }

                // 计算成交量移动平均
                if i >= window_size - 1 {
                    let vol_ma = self.calculate_ma(&volumes[i - window_size + 1..=i]);
                    match window_size {
                        5 => indicator_values.volume_ma5 = Some(vol_ma),
                        _ => {}
                    }
                }
            }

            // 计算技术指标
            if i >= 1 {
                indicator_values.change_percent =
                    Some((closes[i] - closes[i - 1]) / closes[i - 1] * 100.0);
                indicator_values.amplitude = Some((highs[i] - lows[i]) / closes[i - 1] * 100.0);
            }

            if i >= 19 {
                indicator_values.rsi = Some(self.calculate_rsi(&closes[i - 19..=i]));
            }

            if i >= 25 {
                indicator_values.macd = self.calculate_macd(&closes[i - 25..=i]);
            }

            if i >= 19 {
                indicator_values.bollinger = self.calculate_bollinger_bands(&closes[i - 19..=i]);
            }

            indicators.push(Some(indicator_values));
        }

        Ok(indicators)
    }

    /// 计算移动平均
    fn calculate_ma(&self, prices: &[f64]) -> f64 {
        if prices.is_empty() {
            return 0.0;
        }
        prices.iter().sum::<f64>() / prices.len() as f64
    }

    /// 计算RSI相对强弱指标
    fn calculate_rsi(&self, closes: &[f64]) -> f64 {
        if closes.len() < 2 {
            return 50.0;
        }

        let mut gains = Vec::new();
        let mut losses = Vec::new();

        for i in 1..closes.len() {
            let change = closes[i] - closes[i - 1];
            if change > 0.0 {
                gains.push(change);
                losses.push(0.0);
            } else {
                gains.push(0.0);
                losses.push(-change);
            }
        }

        let avg_gain = gains.iter().sum::<f64>() / gains.len() as f64;
        let avg_loss = losses.iter().sum::<f64>() / losses.len() as f64;

        if avg_loss == 0.0 {
            return 100.0;
        }

        let rs = avg_gain / avg_loss;
        100.0 - (100.0 / (1.0 + rs))
    }

    /// 计算MACD指标
    fn calculate_macd(&self, closes: &[f64]) -> Option<MACD> {
        if closes.len() < 26 {
            return None;
        }

        let ema12 = self.calculate_ema(&closes, 12);
        let ema26 = self.calculate_ema(&closes, 26);

        let dif = ema12 - ema26;

        // 计算信号线（9日EMA）
        let mut dif_values = Vec::new();
        for i in 0..closes.len() {
            let current_closes = &closes[i..];
            if current_closes.len() >= 12 {
                let current_ema12 = self.calculate_ema(current_closes, 12);
                if current_closes.len() >= 26 {
                    let current_ema26 = self.calculate_ema(current_closes, 26);
                    dif_values.push(current_ema12 - current_ema26);
                }
            }
        }

        let signal = if dif_values.len() >= 9 {
            self.calculate_ema(&dif_values, 9)
        } else {
            0.0
        };

        Some(MACD {
            dif,
            signal,
            histogram: dif - signal,
        })
    }

    /// 计算指数移动平均
    fn calculate_ema(&self, values: &[f64], period: usize) -> f64 {
        if values.is_empty() {
            return 0.0;
        }

        let multiplier = 2.0 / (period as f64 + 1.0);
        let mut ema = values[0];

        for &value in &values[1..] {
            ema = value * multiplier + ema * (1.0 - multiplier);
        }

        ema
    }

    /// 计算布林带
    fn calculate_bollinger_bands(&self, closes: &[f64]) -> Option<BollingerBands> {
        if closes.len() < 20 {
            return None;
        }

        let ma = self.calculate_ma(closes);
        let variance: f64 =
            closes.iter().map(|price| (price - ma).powi(2)).sum::<f64>() / closes.len() as f64;
        let std_dev = variance.sqrt();

        Some(BollingerBands {
            upper: ma + 2.0 * std_dev,
            middle: ma,
            lower: ma - 2.0 * std_dev,
            width: 4.0 * std_dev,
        })
    }

    /// 并行计算指标（多股票）
    pub fn calculate_parallel(&self, data: &[TDXDayRecord]) -> Result<Vec<EnhancedDayRecord>> {
        // 按股票分组进行并行处理
        use std::collections::HashMap;
        let mut symbol_groups: HashMap<String, Vec<TDXDayRecord>> = HashMap::new();

        for record in data {
            symbol_groups
                .entry(record.symbol.clone())
                .or_insert_with(Vec::new)
                .push(record.clone());
        }

        let mut all_records = Vec::new();

        // 并行处理每个股票的数据
        let results: Result<Vec<_>> = symbol_groups
            .into_par_iter()
            .map(|(symbol, records)| {
                // 按日期排序
                let mut sorted_records = records;
                sorted_records.sort_by(|a, b| a.date.cmp(&b.date));

                // 计算指标
                let time_series: Vec<&TDXDayRecord> = sorted_records.iter().collect();
                let indicators = self.calculate_symbol_indicators(&time_series)?;

                // 组合结果
                let mut enhanced_records = Vec::with_capacity(sorted_records.len());
                for (i, record) in sorted_records.into_iter().enumerate() {
                    if let Some(Some(indicator_values)) = indicators.get(i).cloned() {
                        let enhanced = EnhancedDayRecord::from_record(&record, indicator_values);
                        enhanced_records.push(enhanced);
                    }
                }

                Ok((symbol, enhanced_records))
            })
            .collect();

        // 合并所有结果
        for (_, records) in results? {
            all_records.extend(records);
        }

        // 按日期和股票重新排序
        all_records.sort_by(|a, b| a.date().cmp(&b.date()).then(a.symbol().cmp(b.symbol())));

        Ok(all_records)
    }
}

/// 增强的日线记录（包含技术指标）
#[derive(Debug, Clone)]
pub struct EnhancedDayRecord {
    /// 基础数据
    pub base_record: TDXDayRecord,
    /// 技术指标值
    pub indicators: IndicatorValues,
}

impl EnhancedDayRecord {
    /// 从基础记录创建增强记录
    pub fn from_record(record: &TDXDayRecord, indicators: IndicatorValues) -> Self {
        Self {
            base_record: record.clone(),
            indicators,
        }
    }

    /// 获取基础字段
    pub fn date(&self) -> chrono::NaiveDate {
        self.base_record.date
    }

    pub fn symbol(&self) -> &str {
        &self.base_record.symbol
    }

    pub fn open(&self) -> f64 {
        self.base_record.open
    }

    pub fn high(&self) -> f64 {
        self.base_record.high
    }

    pub fn low(&self) -> f64 {
        self.base_record.low
    }

    pub fn close(&self) -> f64 {
        self.base_record.close
    }

    pub fn volume(&self) -> u64 {
        self.base_record.volume
    }

    pub fn amount(&self) -> f64 {
        self.base_record.amount
    }

    pub fn market(&self) -> &str {
        &self.base_record.market
    }
}

/// 技术指标类型
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TechnicalIndicator {
    /// 移动平均线
    MovingAverage { periods: Vec<usize> },
    /// 指数移动平均线
    ExponentialMovingAverage { periods: Vec<usize> },
    /// MACD指标
    MACD,
    /// RSI指标
    RSI { period: usize },
    /// 布林带
    BollingerBands { period: usize, std_dev: f64 },
    /// 随机指标
    Stochastic { k_period: usize, d_period: usize },
    /// 成交量指标
    Volume { periods: Vec<usize> },
    /// 价格变化
    PriceChange,
    /// 自定义指标
    Custom {
        name: String,
        parameters: HashMap<String, f64>,
    },
}

/// 技术指标值集合
#[derive(Debug, Clone, Default)]
pub struct IndicatorValues {
    /// 5日移动平均
    pub ma5: Option<f64>,
    /// 10日移动平均
    pub ma10: Option<f64>,
    /// 20日移动平均
    pub ma20: Option<f64>,
    /// 60日移动平均
    pub ma60: Option<f64>,
    /// 5日成交量移动平均
    pub volume_ma5: Option<f64>,
    /// 涨跌幅（%）
    pub change_percent: Option<f64>,
    /// 振幅（%）
    pub amplitude: Option<f64>,
    /// RSI相对强弱指标
    pub rsi: Option<f64>,
    /// MACD指标
    pub macd: Option<MACD>,
    /// 布林带
    pub bollinger: Option<BollingerBands>,
    /// 技术指标列表
    pub indicators: Vec<TechnicalIndicator>,
}

/// MACD指标
#[derive(Debug, Clone)]
pub struct MACD {
    /// DIF线
    pub dif: f64,
    /// 信号线
    pub signal: f64,
    /// MACD柱状图
    pub histogram: f64,
}

/// 布林带指标
#[derive(Debug, Clone)]
pub struct BollingerBands {
    /// 上轨
    pub upper: f64,
    /// 中轨（移动平均）
    pub middle: f64,
    /// 下轨
    pub lower: f64,
    /// 带宽
    pub width: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::NaiveDate;

    fn create_test_data() -> Vec<TDXDayRecord> {
        vec![
            TDXDayRecord {
                date: NaiveDate::from_ymd_opt(2024, 1, 1).unwrap(),
                symbol: "600000".to_string(),
                open: 10.0,
                high: 11.0,
                low: 9.0,
                close: 10.5,
                volume: 1000000,
                amount: 10500000.0,
                market: "SH".to_string(),
            },
            TDXDayRecord {
                date: NaiveDate::from_ymd_opt(2024, 1, 2).unwrap(),
                symbol: "600000".to_string(),
                open: 10.5,
                high: 12.0,
                low: 10.0,
                close: 11.5,
                volume: 1200000,
                amount: 13800000.0,
                market: "SH".to_string(),
            },
        ]
    }

    #[test]
    fn test_indicator_calculator_creation() {
        let calculator = IndicatorCalculator::new();
        assert_eq!(calculator.window_sizes, vec![5, 10, 20, 60]);
    }

    #[test]
    fn test_ma_calculation() {
        let calculator = IndicatorCalculator::new();
        let prices = vec![10.0, 11.0, 12.0, 13.0, 14.0, 15.0];
        let ma = calculator.calculate_ma(&prices[1..6]); // 5日均线
        assert_eq!(ma, 13.0);
    }

    #[test]
    fn test_rsi_calculation() {
        let calculator = IndicatorCalculator::new();
        let closes = vec![10.0, 11.0, 9.0, 12.0, 8.0, 13.0, 7.0, 14.0, 6.0, 15.0];
        let rsi = calculator.calculate_rsi(&closes);
        assert!(rsi > 0.0 && rsi <= 100.0);
    }

    #[test]
    fn test_calculate_all_indicators() {
        let calculator = IndicatorCalculator::new();
        let data = create_test_data();

        let result = calculator.calculate_all_indicators(&data).unwrap();

        assert_eq!(result.len(), 2);

        // 检查指标是否被计算
        for enhanced_record in result {
            assert_eq!(enhanced_record.symbol(), "600000");
            // 第一条记录的指标可能为None，因为数据不足
            // 第二条记录应该有一些指标值
        }
    }

    #[test]
    fn test_parallel_calculation() {
        let calculator = IndicatorCalculator::new();

        // 创建多只股票的测试数据
        let mut data = create_test_data();

        // 添加第二只股票
        let mut record2 = create_test_data()[0].clone();
        record2.symbol = "000001".to_string();
        record2.market = "SZ".to_string();
        data.push(record2);

        let result = calculator.calculate_parallel(&data).unwrap();

        assert_eq!(result.len(), 4); // 每只股票2条记录
    }
}

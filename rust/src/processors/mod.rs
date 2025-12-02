//! 数据处理模块

pub mod aggregator;
pub mod calculator;
pub mod cleaner;
pub mod transformer;

pub use aggregator::{AggregationRule, DataAggregator};
pub use calculator::{IndicatorCalculator, TechnicalIndicator};
pub use cleaner::{CleaningResult, CleaningRule, DataCleaner};
pub use transformer::DataTransformer;

use anyhow::Result;
use rayon::prelude::*;
use std::sync::Arc;
use tokio::sync::Semaphore;

/// 高性能数据处理器
#[derive(Debug)]
pub struct DataProcessor {
    /// 并发限制
    concurrency_limit: usize,
    /// 内存限制（字节）
    memory_limit: usize,
    /// 信号量控制并发
    semaphore: Arc<Semaphore>,
}

impl DataProcessor {
    /// 创建新的数据处理器
    pub fn new(concurrency_limit: usize, memory_limit: usize) -> Self {
        Self {
            concurrency_limit,
            memory_limit,
            semaphore: Arc::new(Semaphore::new(concurrency_limit)),
        }
    }

    /// 并行处理数据集
    pub async fn process_parallel<T, R, F>(&self, data: Vec<T>, processor: F) -> Result<Vec<R>>
    where
        T: Send + Sync + Clone + 'static,
        R: Send + 'static,
        F: Fn(T) -> Result<R> + Send + Sync + 'static,
    {
        // 分块处理以控制内存使用
        let chunk_size = (data.len() + self.concurrency_limit - 1) / self.concurrency_limit;
        let chunks: Vec<_> = data.chunks(chunk_size).collect();

        let mut results = Vec::with_capacity(data.len());

        for chunk in chunks {
            // 获取信号量许可
            let _permit = self.semaphore.acquire().await?;

            // 并行处理当前块
            let chunk_results: Result<Vec<_>> = chunk
                .par_iter()
                .map(|item| {
                    let result = processor(item.to_owned())?;
                    Ok(result)
                })
                .collect();

            let chunk_results = chunk_results?;
            results.extend(chunk_results);

            // 释放许可
            drop(_permit);
        }

        Ok(results)
    }

    /// 流式处理大数据集
    pub async fn process_stream<T, R, F>(
        &self,
        data_stream: impl Iterator<Item = T>,
        batch_size: usize,
        processor: F,
    ) -> Result<Vec<R>>
    where
        T: Send + Sync + Clone + 'static,
        R: Send + 'static,
        F: Fn(Vec<T>) -> Result<Vec<R>> + Send + Sync + 'static,
    {
        let mut results = Vec::new();
        let mut batch = Vec::with_capacity(batch_size);

        for item in data_stream {
            batch.push(item);

            if batch.len() >= batch_size {
                let _permit = self.semaphore.acquire().await?;
                let batch_results = processor(batch.clone())?;
                results.extend(batch_results);
                batch.clear();
                drop(_permit);
            }
        }

        // 处理最后一批
        if !batch.is_empty() {
            let _permit = self.semaphore.acquire().await?;
            let batch_results = processor(batch)?;
            results.extend(batch_results);
        }

        Ok(results)
    }
}

impl Default for DataProcessor {
    fn default() -> Self {
        Self::new(
            num_cpus::get(),
            1024 * 1024 * 1024, // 1GB内存限制
        )
    }
}

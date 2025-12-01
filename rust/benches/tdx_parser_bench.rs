use criterion::{black_box, criterion_group, criterion_main, Criterion};
use pulse_trader_rust::parsers::TDXDayParser;
use std::fs;
use tempfile::TempDir;

fn create_test_data(temp_dir: &TempDir) -> Vec<u8> {
    // 创建测试二进制数据 - 每条记录8个u32字段
    let test_records = vec![
        // 记录1: 日期, 开盘价, 最高价, 最低价, 收盘价, 成交额, 成交量, 保留
        20240101u32, 100000u32, 105000u32, 98000u32, 102000u32, 1000000u32, 1000000u32, 0u32,
        // 记录2: 日期, 开盘价, 最高价, 最低价, 收盘价, 成交额, 成交量, 保留
        20240102u32, 102000u32, 108000u32, 100000u32, 106000u32, 1200000u32, 1200000u32, 0u32,
        // 记录3: 日期, 开盘价, 最高价, 最低价, 收盘价, 成交额, 成交量, 保留
        20240103u32, 106000u32, 112000u32, 104000u32, 110000u32, 1400000u32, 1400000u32, 0u32,
    ];

    // 转换为字节数组
    unsafe {
        std::slice::from_raw_parts(
            test_records.as_ptr() as *const u8,
            test_records.len() * std::mem::size_of::<u32>(),
        )
        .to_vec()
    }
}

fn bench_parse_binary_data(c: &mut Criterion) {
    let temp_dir = TempDir::new().unwrap();
    let parser = TDXDayParser::new(temp_dir.path());

    // 创建测试数据
    let test_data = create_test_data(&temp_dir);

    c.bench_function("parse_binary_data", |b| {
        b.iter(|| {
            let _ = parser
                .parse_binary_data(black_box(&test_data), black_box("600000"), black_box("SH"))
                .unwrap();
        })
    });
}

fn bench_parse_large_dataset(c: &mut Criterion) {
    let temp_dir = TempDir::new().unwrap();
    let parser = TDXDayParser::new(temp_dir.path());

    // 创建较大的测试数据集 - 使用固定有效日期
    let mut large_data = Vec::new();
    for i in 0..10000 {
        // 10000条记录，每条记录8个u32字段
        // 使用固定有效日期20240101，简单且有效
        large_data.extend_from_slice(&20240101u32.to_le_bytes());          // 日期
        large_data.extend_from_slice(&100000u32.to_le_bytes());                // 开盘价(分为元)
        large_data.extend_from_slice(&105000u32.to_le_bytes());                // 最高价
        large_data.extend_from_slice(&98000u32.to_le_bytes());                 // 最低价
        large_data.extend_from_slice(&102000u32.to_le_bytes());                // 收盘价
        large_data.extend_from_slice(&1000000u32.to_le_bytes());               // 成交额
        large_data.extend_from_slice(&1000000u32.to_le_bytes());               // 成交量
        large_data.extend_from_slice(&0u32.to_le_bytes());                     // 保留
    }

    c.bench_function("parse_large_dataset", |b| {
        b.iter(|| {
            let _ = parser
                .parse_binary_data(black_box(&large_data), black_box("600000"), black_box("SH"))
                .unwrap();
        })
    });
}

criterion_group!(benches, bench_parse_binary_data, bench_parse_large_dataset);
criterion_main!(benches);

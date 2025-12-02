#!/usr/bin/env python3
"""
数据处理流程综合测试脚本
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from src.data.processors.cleaner import DataCleaner
from src.data.processors.transformer import DataTransformer
from src.data.processors.validator import DataValidator


def create_test_data():
    """创建包含各种数据质量问题的测试数据"""

    # 生成30天的测试数据
    dates = pd.date_range("2024-01-01", periods=30, freq="D")

    # 模拟股票数据，包含各种问题
    np.random.seed(42)
    base_price = 100.0
    price_changes = np.random.normal(0, 0.03, 30)
    prices = [base_price]
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1.0))  # 确保价格为正

    test_data = pd.DataFrame(
        {
            "symbol": ["000001"] * 30 + ["000001"] + ["000002"] * 30,  # 包含重复
            "date": list(dates) + [dates[5]] + list(dates),  # 包含重复日期
            "open": prices + [None] + [p * 0.95 for p in prices],  # 包含缺失值
            "high": [p * 1.05 for p in prices]
            + [80.0]
            + [p * 1.08 for p in prices],  # 包含异常值
            "low": [p * 0.95 for p in prices]
            + [120.0]
            + [p * 0.92 for p in prices],  # 包含异常值
            "close": prices + [105.0] + prices,  # 包含异常值
            "volume": np.random.randint(1000000, 5000000, 61),  # 正常成交量
        }
    )

    # 添加一些额外的问题
    test_data.loc[10, "volume"] = -1000000  # 负成交量
    test_data.loc[15, "open"] = None  # 缺失开盘价
    test_data.loc[20, "close"] = 0.01  # 异常低价

    return test_data


def main():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("🚀 开始测试数据处理流程...\n")

    # 1. 创建测试数据
    print("=== 1. 创建测试数据 ===")
    test_data = create_test_data()
    print(f"原始测试数据：{len(test_data)} 行 x {len(test_data.columns)} 列")
    print("数据预览：")
    print(test_data.head(10))
    print()

    # 2. 数据验证
    print("=== 2. 数据验证 ===")
    validator = DataValidator()

    validation_result = validator.validate(
        test_data, "price_data", check_completeness=True
    )

    print(f"验证结果：{'通过' if validation_result['is_valid'] else '失败'}")
    print(f"错误数量：{validation_result['summary']['total_errors']}")
    print(f"警告数量：{validation_result['summary']['total_warnings']}")

    if validation_result["structure"]["errors"]:
        print("结构错误：", validation_result["structure"]["errors"])

    if validation_result["content"]["errors"]:
        print("内容错误：", validation_result["content"]["errors"])

    if validation_result["content"]["warnings"]:
        print("内容警告：", validation_result["content"]["warnings"])

    print()

    # 3. 数据清洗
    print("=== 3. 数据清洗 ===")
    cleaner = DataCleaner()

    cleaning_steps = [
        "remove_duplicates",
        "standardize_types",
        "handle_missing",
        "handle_outliers",
        "validate_consistency",
    ]

    cleaned_data, cleaning_report = cleaner.clean_data(
        test_data, "price_data", cleaning_steps
    )

    print(f"清洗前：{test_data.shape}")
    print(f"清洗后：{cleaned_data.shape}")
    print(f"删除行数：{cleaning_report['total_removed_rows']}")

    # 显示各步骤的清洗结果
    for step_info in cleaning_report["steps_performed"]:
        if "removed_count" in step_info:
            print(f"- {step_info['operation']}: 删除 {step_info['removed_count']} 行")
        elif "handled_missing" in step_info:
            print(
                f"- {step_info['operation']}: 处理 {step_info['handled_missing']} 个缺失值"
            )
        elif "total_corrections" in step_info:
            print(
                f"- {step_info['operation']}: 修正 {step_info['total_corrections']} 个异常"
            )

    print()

    # 4. 验证清洗后的数据
    print("=== 4. 清洗后数据验证 ===")
    post_cleaning_validation = validator.validate(cleaned_data, "price_data")

    print(f"清洗后验证：{'通过' if post_cleaning_validation['is_valid'] else '失败'}")
    print(f"剩余错误：{post_cleaning_validation['summary']['total_errors']}")
    print(f"剩余警告：{post_cleaning_validation['summary']['total_warnings']}")

    if post_cleaning_validation["content"]["quality_metrics"]:
        quality_metrics = post_cleaning_validation["content"]["quality_metrics"]
        print("质量指标：")
        print(f"  缺失值比例：{sum(quality_metrics['missing_ratio'].values()):.4f}")
        print(f"  重复行比例：{quality_metrics['duplicate_ratio']:.4f}")

    print()

    # 5. 数据转换
    print("=== 5. 数据转换 ===")
    transformer = DataTransformer()

    # 确保有足够的数据进行技术指标计算
    if len(cleaned_data) >= 20:
        transformations = ["normalize", "indicators", "features"]
        transformed_data, transformation_report = transformer.transform_data(
            cleaned_data, "price_data", transformations
        )

        print(f"转换前：{cleaned_data.shape}")
        print(f"转换后：{transformed_data.shape}")

        # 统计新增的特征
        original_columns = set(cleaned_data.columns)
        new_columns = set(transformed_data.columns) - original_columns
        print(f"新增特征数量：{len(new_columns)}")
        print("部分新增特征：", list(new_columns)[:10])

        print()

    # 6. 最终数据质量报告
    print("=== 6. 最终数据质量报告 ===")

    final_data = transformed_data if "transformed_data" in locals() else cleaned_data
    final_validation = validator.validate(final_data, "price_data")

    print("📊 数据处理总结：")
    print(f"  原始数据量：{len(test_data)} 行")
    print(f"  最终数据量：{len(final_data)} 行")
    print(f"  数据保留率：{len(final_data)/len(test_data):.2%}")
    print(f"  最终验证状态：{'✅ 通过' if final_validation['is_valid'] else '❌ 失败'}")
    print(f"  最终特征数：{len(final_data.columns)}")

    if final_validation["content"]["quality_metrics"]:
        metrics = final_validation["content"]["quality_metrics"]
        print(f"  数据完整性：{(1-sum(metrics['missing_ratio'].values())):.2%}")
        print(
            f"  数据一致性：{'✅' if not final_validation['content']['errors'] else '❌'}"
        )

    print("\n🎉 数据处理流程测试完成！")

    # 7. 保存处理后的样本数据（可选）
    output_path = "data/processed/cleaned_sample_data.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        final_data.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"\n💾 处理后数据已保存到：{output_path}")
    except Exception as e:
        print(f"\n❌ 保存数据失败：{e}")


if __name__ == "__main__":
    main()

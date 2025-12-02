"""
数据验证器
提供各种数据质量检查和验证功能
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""

    def __init__(self):
        """初始化验证器"""
        self.validation_rules = self._load_validation_rules()
        self.validation_results = {}

    def _load_validation_rules(self) -> Dict[str, Dict]:
        """加载验证规则配置"""
        return {
            "price_data": {
                "required_columns": [
                    "symbol",
                    "date",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                ],
                "numeric_columns": ["open", "high", "low", "close", "volume"],
                "positive_columns": ["open", "high", "low", "close", "volume"],
                "price_relations": {
                    "high_ge_low": lambda df: (df["high"] >= df["low"]).all(),
                    "high_ge_close": lambda df: (df["high"] >= df["close"]).all(),
                    "low_le_close": lambda df: (df["low"] <= df["close"]).all(),
                    "high_ge_open": lambda df: (df["high"] >= df["open"]).all(),
                    "low_le_open": lambda df: (df["low"] <= df["open"]).all(),
                },
                "reasonable_ranges": {
                    "price": (0.01, 10000),  # 股价合理范围
                    "volume": (0, 1e12),  # 成交量合理范围
                    "change_percent": (-0.21, 0.21),  # 涨跌幅限制（考虑ST股）
                },
            },
            "stock_info": {
                "required_columns": ["symbol", "stock_name"],
                "string_columns": ["symbol", "stock_name"],
                "symbol_pattern": r"^\d{6}$",  # 6位数字股票代码
                "max_string_length": {"symbol": 6, "stock_name": 20},
            },
        }

    def validate_structure(self, data: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """
        验证数据结构

        Args:
            data: 待验证的数据
            data_type: 数据类型

        Returns:
            验证结果
        """
        results = {"is_valid": True, "errors": [], "warnings": [], "info": {}}

        try:
            # 检查是否为DataFrame
            if not isinstance(data, pd.DataFrame):
                results["is_valid"] = False
                results["errors"].append(
                    f"数据类型错误：期望DataFrame，实际{type(data)}"
                )
                return results

            # 检查是否为空
            if data.empty:
                results["is_valid"] = False
                results["errors"].append("数据为空")
                return results

            # 获取验证规则
            rules = self.validation_rules.get(data_type, {})

            # 检查必需列
            if "required_columns" in rules:
                missing_columns = set(rules["required_columns"]) - set(data.columns)
                if missing_columns:
                    results["is_valid"] = False
                    results["errors"].append(f"缺少必需列：{missing_columns}")

            # 检查额外列
            extra_columns = set(data.columns) - set(rules.get("required_columns", []))
            if extra_columns:
                results["warnings"].append(f"发现额外列：{extra_columns}")

            # 基本信息
            results["info"] = {
                "rows": len(data),
                "columns": len(data.columns),
                "column_names": list(data.columns),
                "data_types": data.dtypes.to_dict(),
                "memory_usage": data.memory_usage(deep=True).sum(),
            }

        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"结构验证异常：{e}")

        return results

    def validate_content(self, data: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """
        验证数据内容

        Args:
            data: 待验证的数据
            data_type: 数据类型

        Returns:
            验证结果
        """
        results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "quality_metrics": {},
        }

        try:
            rules = self.validation_rules.get(data_type, {})

            # 检查数据类型
            if "numeric_columns" in rules:
                for col in rules["numeric_columns"]:
                    if col in data.columns:
                        non_numeric = data[col].apply(
                            lambda x: not pd.api.types.is_numeric_dtype(type(x))
                        )
                        if non_numeric.any():
                            results["warnings"].append(
                                f"列 '{col}' 包含非数值数据：{non_numeric.sum()} 个"
                            )

            # 检查正数约束
            if "positive_columns" in rules:
                for col in rules["positive_columns"]:
                    if col in data.columns:
                        negative_count = (data[col] <= 0).sum()
                        if negative_count > 0:
                            results["errors"].append(
                                f"列 '{col}' 包含非正数：{negative_count} 个"
                            )

            # 检查价格关系
            if "price_relations" in rules:
                for relation_name, relation_func in rules["price_relations"].items():
                    try:
                        if not relation_func(data):
                            results["errors"].append(
                                f"价格关系验证失败：{relation_name}"
                            )
                    except Exception as e:
                        results["warnings"].append(
                            f"价格关系检查异常 {relation_name}：{e}"
                        )

            # 检查合理范围
            if "reasonable_ranges" in rules:
                for range_name, (min_val, max_val) in rules[
                    "reasonable_ranges"
                ].items():
                    if range_name == "price":
                        price_columns = ["open", "high", "low", "close"]
                        for col in price_columns:
                            if col in data.columns:
                                out_of_range = (
                                    (data[col] < min_val) | (data[col] > max_val)
                                ).sum()
                                if out_of_range > 0:
                                    results["warnings"].append(
                                        f"列 '{col}' 有 {out_of_range} 个值超出合理范围 [{min_val}, {max_val}]"
                                    )
                    elif (
                        range_name == "change_percent"
                        and "change_percent" in data.columns
                    ):
                        out_of_range = (
                            (data["change_percent"] < min_val)
                            | (data["change_percent"] > max_val)
                        ).sum()
                        if out_of_range > 0:
                            results["warnings"].append(
                                f"涨跌幅有 {out_of_range} 个值超出合理范围"
                            )

            # 检查股票代码格式
            if data_type == "stock_info" and "symbol_pattern" in rules:
                if "symbol" in data.columns:
                    pattern = re.compile(rules["symbol_pattern"])
                    invalid_symbols = data[
                        ~data["symbol"].astype(str).str.match(pattern)
                    ]
                    if not invalid_symbols.empty:
                        results["errors"].append(
                            f"发现 {len(invalid_symbols)} 个无效股票代码格式"
                        )

            # 计算质量指标
            results["quality_metrics"] = self._calculate_quality_metrics(data)

        except Exception as e:
            results["is_valid"] = False
            results["errors"].append(f"内容验证异常：{e}")

        return results

    def _calculate_quality_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """计算数据质量指标"""
        metrics = {}

        # 缺失值统计
        missing_stats = data.isnull().sum()
        metrics["missing_values"] = missing_stats.to_dict()
        metrics["missing_ratio"] = (missing_stats / len(data)).to_dict()

        # 重复值统计
        metrics["duplicate_rows"] = data.duplicated().sum()
        metrics["duplicate_ratio"] = metrics["duplicate_rows"] / len(data)

        # 数值列统计
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            metrics["numeric_summary"] = data[numeric_columns].describe().to_dict()

        # 异常值检测（IQR方法）
        outliers = {}
        for col in numeric_columns:
            if col in data.columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outlier_count = (
                    (data[col] < lower_bound) | (data[col] > upper_bound)
                ).sum()
                outliers[col] = outlier_count

        metrics["outliers"] = outliers

        return metrics

    def validate_completeness(
        self, data: pd.DataFrame, date_column: str = "date"
    ) -> Dict[str, Any]:
        """
        验证数据完整性（主要是时间序列完整性）

        Args:
            data: 待验证的数据
            date_column: 日期列名

        Returns:
            完整性验证结果
        """
        results = {
            "is_complete": True,
            "missing_dates": [],
            "gaps": [],
            "completeness_ratio": 1.0,
        }

        try:
            if date_column not in data.columns:
                results["is_complete"] = False
                results["missing_dates"].append(f"缺少日期列：{date_column}")
                return results

            # 转换日期列
            dates = pd.to_datetime(data[date_column]).sort_values()

            # 检查日期范围
            date_range = (dates.max() - dates.min()).days
            unique_dates = dates.dt.date.unique()

            # 生成完整的日期序列（排除周末）
            full_date_range = pd.date_range(
                start=dates.min(), end=dates.max(), freq="D"  # 每日频率
            )

            # 过滤周末（A股不在周末交易）
            trading_days = [d for d in full_date_range if d.weekday() < 5]
            trading_dates = [d.date() for d in trading_days]

            # 找出缺失的交易日
            missing_dates = set(trading_dates) - set(unique_dates)

            if missing_dates:
                results["is_complete"] = False
                results["missing_dates"] = sorted(list(missing_dates))
                results["completeness_ratio"] = len(unique_dates) / len(trading_dates)

                # 检查连续缺失的日期段
                sorted_missing = sorted(missing_dates)
                gaps = []
                if sorted_missing:
                    current_gap = [sorted_missing[0]]
                    for i in range(1, len(sorted_missing)):
                        if sorted_missing[i] == sorted_missing[i - 1] + timedelta(
                            days=1
                        ):
                            current_gap.append(sorted_missing[i])
                        else:
                            if len(current_gap) > 1:  # 只记录连续多天的缺失
                                gaps.append((current_gap[0], current_gap[-1]))
                            current_gap = [sorted_missing[i]]

                    if len(current_gap) > 1:
                        gaps.append((current_gap[0], current_gap[-1]))

                    results["gaps"] = gaps

        except Exception as e:
            results["is_complete"] = False
            results["missing_dates"].append(f"完整性验证异常：{e}")

        return results

    def validate(
        self,
        data: pd.DataFrame,
        data_type: str,
        check_completeness: bool = False,
        date_column: str = "date",
    ) -> Dict[str, Any]:
        """
        综合验证

        Args:
            data: 待验证的数据
            data_type: 数据类型
            check_completeness: 是否检查完整性
            date_column: 日期列名

        Returns:
            综合验证结果
        """
        logger.info(f"开始验证数据：{data_type}, 数据量：{len(data)}")

        # 结构验证
        structure_result = self.validate_structure(data, data_type)

        # 内容验证
        content_result = self.validate_content(data, data_type)

        # 完整性验证
        completeness_result = {}
        if check_completeness and date_column in data.columns:
            completeness_result = self.validate_completeness(data, date_column)

        # 汇总结果
        overall_result = {
            "is_valid": structure_result["is_valid"] and content_result["is_valid"],
            "validation_time": datetime.now().isoformat(),
            "data_type": data_type,
            "structure": structure_result,
            "content": content_result,
            "completeness": completeness_result,
            "summary": {
                "total_errors": len(structure_result["errors"])
                + len(content_result["errors"]),
                "total_warnings": len(structure_result["warnings"])
                + len(content_result["warnings"]),
                "recommendations": [],
            },
        }

        # 生成建议
        if overall_result["summary"]["total_errors"] > 0:
            overall_result["summary"]["recommendations"].append(
                "存在数据错误，建议清洗后再使用"
            )

        if overall_result["summary"]["total_warnings"] > 0:
            overall_result["summary"]["recommendations"].append(
                "存在数据警告，建议检查数据质量"
            )

        if completeness_result.get("completeness_ratio", 1.0) < 0.95:
            overall_result["summary"]["recommendations"].append(
                "数据完整性不足，建议补充缺失数据"
            )

        # 缓存验证结果
        self.validation_results[f"{data_type}_{datetime.now().isoformat()}"] = (
            overall_result
        )

        logger.info(
            f"验证完成：有效={overall_result['is_valid']}, "
            f"错误={overall_result['summary']['total_errors']}, "
            f"警告={overall_result['summary']['total_warnings']}"
        )

        return overall_result


def test_data_validator():
    """测试数据验证器"""
    validator = DataValidator()

    # 测试正常数据
    print("=== 测试正常价格数据 ===")
    normal_data = pd.DataFrame(
        {
            "symbol": ["000001"] * 5,
            "date": pd.date_range("2024-01-01", periods=5),
            "open": [10.0, 10.1, 10.2, 10.1, 10.3],
            "high": [10.2, 10.3, 10.4, 10.2, 10.5],
            "low": [9.8, 9.9, 10.0, 9.9, 10.1],
            "close": [10.1, 10.2, 10.1, 10.0, 10.4],
            "volume": [1000000, 1200000, 800000, 900000, 1100000],
        }
    )

    result = validator.validate(normal_data, "price_data")
    print(f"验证结果：{result['is_valid']}")
    print(f"错误数：{result['summary']['total_errors']}")
    print(f"警告数：{result['summary']['total_warnings']}")

    # 测试异常数据
    print("\n=== 测试异常价格数据 ===")
    abnormal_data = pd.DataFrame(
        {
            "symbol": ["000001"] * 3,
            "date": pd.date_range("2024-01-01", periods=3),
            "open": [10.0, 10.1, -5.0],  # 负价格
            "high": [9.5, 10.3, 10.2],  # 最高价低于开盘价
            "low": [10.2, 9.9, 10.1],  # 最低价高于开盘价
            "close": [10.1, 10.2, 10.0],
            "volume": [1000000, 1200000, -100000],  # 负成交量
        }
    )

    result = validator.validate(abnormal_data, "price_data")
    print(f"验证结果：{result['is_valid']}")
    print(f"错误：{result['content']['errors']}")
    print(f"警告：{result['content']['warnings']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_data_validator()

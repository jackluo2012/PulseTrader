"""
数据清洗器
提供各种数据清洗和预处理功能
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from .validator import DataValidator

logger = logging.getLogger(__name__)


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        """初始化清洗器"""
        self.validator = DataValidator()
        self.cleaning_log = []

    def remove_duplicates(
        self, data: pd.DataFrame, subset: List[str] = None, keep: str = "first"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        去除重复数据

        Args:
            data: 输入数据
            subset: 用于判断重复的列
            keep: 保留策略（first, last, False）

        Returns:
            清洗后的数据和清洗信息
        """
        original_count = len(data)

        if subset is None:
            # 默认使用所有列
            duplicates = data.duplicated(keep=keep)
        else:
            duplicates = data.duplicated(subset=subset, keep=keep)

        cleaned_data = data[~duplicates].copy()
        removed_count = duplicates.sum()

        cleaning_info = {
            "operation": "remove_duplicates",
            "original_count": original_count,
            "cleaned_count": len(cleaned_data),
            "removed_count": removed_count,
            "removal_ratio": (
                removed_count / original_count if original_count > 0 else 0
            ),
            "subset_columns": subset,
            "timestamp": datetime.now().isoformat(),
        }

        self.cleaning_log.append(cleaning_info)
        logger.info(
            f"去除重复数据：{removed_count}/{original_count} ({cleaning_info['removal_ratio']:.2%})"
        )

        return cleaned_data, cleaning_info

    def handle_missing_values(
        self,
        data: pd.DataFrame,
        strategy: str = "drop",
        columns: List[str] = None,
        fill_value: Any = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        处理缺失值

        Args:
            data: 输入数据
            strategy: 处理策略（drop, fill, interpolate, forward_fill, backward_fill）
            columns: 指定处理的列，None表示所有列
            fill_value: 填充值（当strategy='fill'时使用）

        Returns:
            清洗后的数据和清洗信息
        """
        if columns is None:
            columns = data.columns.tolist()

        cleaned_data = data.copy()
        missing_info = {}

        # 统计原始缺失值
        original_missing = cleaned_data[columns].isnull().sum()
        total_missing_original = original_missing.sum()

        if total_missing_original == 0:
            cleaning_info = {
                "operation": "handle_missing_values",
                "strategy": strategy,
                "original_missing": 0,
                "handled_missing": 0,
                "timestamp": datetime.now().isoformat(),
            }
            self.cleaning_log.append(cleaning_info)
            logger.info("数据无缺失值，跳过处理")
            return cleaned_data, cleaning_info

        # 根据策略处理缺失值
        if strategy == "drop":
            # 删除包含缺失值的行
            cleaned_data = cleaned_data.dropna(subset=columns)

        elif strategy == "fill":
            # 使用指定值填充
            for col in columns:
                if col in cleaned_data.columns:
                    if fill_value is not None:
                        cleaned_data[col] = cleaned_data[col].fillna(fill_value)
                    else:
                        # 数值列用中位数，字符串列用众数
                        if pd.api.types.is_numeric_dtype(cleaned_data[col]):
                            fill_val = cleaned_data[col].median()
                        else:
                            fill_val = (
                                cleaned_data[col].mode().iloc[0]
                                if not cleaned_data[col].mode().empty
                                else "Unknown"
                            )
                        cleaned_data[col] = cleaned_data[col].fillna(fill_val)

        elif strategy == "interpolate":
            # 线性插值（仅适用于数值列）
            for col in columns:
                if col in cleaned_data.columns and pd.api.types.is_numeric_dtype(
                    cleaned_data[col]
                ):
                    cleaned_data[col] = cleaned_data[col].interpolate(method="linear")

        elif strategy == "forward_fill":
            # 前向填充
            cleaned_data[columns] = cleaned_data[columns].fillna(method="ffill")

        elif strategy == "backward_fill":
            # 后向填充
            cleaned_data[columns] = cleaned_data[columns].fillna(method="bfill")

        # 统计处理后的缺失值
        final_missing = cleaned_data[columns].isnull().sum()
        total_missing_final = final_missing.sum()

        cleaning_info = {
            "operation": "handle_missing_values",
            "strategy": strategy,
            "columns": columns,
            "original_missing": total_missing_original,
            "handled_missing": total_missing_original - total_missing_final,
            "remaining_missing": total_missing_final,
            "original_missing_by_column": original_missing.to_dict(),
            "final_missing_by_column": final_missing.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }

        self.cleaning_log.append(cleaning_info)
        logger.info(
            f"处理缺失值：{strategy}, 处理 {cleaning_info['handled_missing']} 个缺失值"
        )

        return cleaned_data, cleaning_info

    def detect_and_handle_outliers(
        self,
        data: pd.DataFrame,
        columns: List[str] = None,
        method: str = "iqr",
        action: str = "cap",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        检测和处理异常值

        Args:
            data: 输入数据
            columns: 指定处理的列，None表示所有数值列
            method: 检测方法（iqr, zscore, isolation_forest）
            action: 处理方式（remove, cap, transform）

        Returns:
            清洗后的数据和处理信息
        """
        if columns is None:
            columns = data.select_dtypes(include=[np.number]).columns.tolist()

        cleaned_data = data.copy()
        outlier_info = {
            "outliers_by_column": {},
            "total_outliers": 0,
            "handled_outliers": 0,
        }

        for col in columns:
            if col not in cleaned_data.columns:
                continue

            original_values = cleaned_data[col].copy()
            outlier_mask = pd.Series(False, index=cleaned_data.index)

            if method == "iqr":
                Q1 = cleaned_data[col].quantile(0.25)
                Q3 = cleaned_data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outlier_mask = (cleaned_data[col] < lower_bound) | (
                    cleaned_data[col] > upper_bound
                )

            elif method == "zscore":
                z_scores = np.abs(
                    (cleaned_data[col] - cleaned_data[col].mean())
                    / cleaned_data[col].std()
                )
                outlier_mask = z_scores > 3

            outlier_count = outlier_mask.sum()
            outlier_info["outliers_by_column"][col] = outlier_count
            outlier_info["total_outliers"] += outlier_count

            if outlier_count > 0:
                if action == "remove":
                    # 删除异常值
                    cleaned_data = cleaned_data[~outlier_mask]
                    outlier_info["handled_outliers"] += outlier_count

                elif action == "cap":
                    # 盖帽法处理
                    if method == "iqr":
                        cleaned_data[col] = cleaned_data[col].clip(
                            lower_bound, upper_bound
                        )
                    else:
                        # Z-score方法使用3倍标准差作为边界
                        mean_val = cleaned_data[col].mean()
                        std_val = cleaned_data[col].std()
                        cleaned_data[col] = cleaned_data[col].clip(
                            mean_val - 3 * std_val, mean_val + 3 * std_val
                        )
                    outlier_info["handled_outliers"] += outlier_count

                elif action == "transform":
                    # 对数变换（仅适用于正值）
                    if (original_values > 0).all():
                        cleaned_data[col] = np.log1p(original_values)
                        outlier_info["handled_outliers"] += outlier_count

        cleaning_info = {
            "operation": "handle_outliers",
            "method": method,
            "action": action,
            "columns": columns,
            **outlier_info,
            "timestamp": datetime.now().isoformat(),
        }

        self.cleaning_log.append(cleaning_info)
        logger.info(
            f"异常值处理：{method}-{action}, "
            f"检测到 {outlier_info['total_outliers']} 个异常值，"
            f"处理了 {outlier_info['handled_outliers']} 个"
        )

        return cleaned_data, cleaning_info

    def standardize_data_types(
        self, data: pd.DataFrame, type_mapping: Dict[str, str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        标准化数据类型

        Args:
            data: 输入数据
            type_mapping: 类型映射字典 {列名: 目标类型}

        Returns:
            标准化后的数据和转换信息
        """
        cleaned_data = data.copy()
        conversion_info = {"conversions": {}, "failed_conversions": {}}

        # 默认的价格数据类型映射
        if type_mapping is None:
            type_mapping = {
                "symbol": "string",
                "stock_name": "string",
                "date": "datetime64[ns]",
                "datetime": "datetime64[ns]",
                "open": "float64",
                "high": "float64",
                "low": "float64",
                "close": "float64",
                "volume": "int64",
                "amount": "float64",
                "change_percent": "float64",
            }

        for col, target_type in type_mapping.items():
            if col not in cleaned_data.columns:
                continue

            try:
                original_type = str(cleaned_data[col].dtype)

                if target_type == "datetime64[ns]":
                    # 日期时间转换
                    cleaned_data[col] = pd.to_datetime(cleaned_data[col])
                elif target_type == "string":
                    # 字符串转换
                    cleaned_data[col] = cleaned_data[col].astype("string")
                else:
                    # 数值转换
                    cleaned_data[col] = pd.to_numeric(
                        cleaned_data[col], errors="coerce"
                    )

                conversion_info["conversions"][col] = {
                    "from": original_type,
                    "to": str(cleaned_data[col].dtype),
                    "success": True,
                }

            except Exception as e:
                conversion_info["failed_conversions"][col] = {
                    "target_type": target_type,
                    "error": str(e),
                }
                logger.warning(f"类型转换失败 {col} -> {target_type}: {e}")

        cleaning_info = {
            "operation": "standardize_data_types",
            "conversions": conversion_info["conversions"],
            "failed_conversions": conversion_info["failed_conversions"],
            "timestamp": datetime.now().isoformat(),
        }

        self.cleaning_log.append(cleaning_info)
        logger.info(
            f"数据类型标准化：成功 {len(conversion_info['conversions'])} 个，失败 {len(conversion_info['failed_conversions'])} 个"
        )

        return cleaned_data, cleaning_info

    def validate_price_consistency(
        self, data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        验证和修正价格一致性

        Args:
            data: 包含价格数据的DataFrame

        Returns:
            修正后的数据和修正信息
        """
        cleaned_data = data.copy()
        price_columns = ["open", "high", "low", "close"]
        price_columns = [col for col in price_columns if col in cleaned_data.columns]

        if len(price_columns) < 4:
            cleaning_info = {
                "operation": "validate_price_consistency",
                "status": "skipped",
                "reason": "缺少必要的价格列",
                "timestamp": datetime.now().isoformat(),
            }
            return cleaned_data, cleaning_info

        corrections = []
        total_corrections = 0

        # 检查每行的价格一致性
        for idx, row in cleaned_data.iterrows():
            row_corrections = 0

            # 确保高价不低于低价
            if row["high"] < row["low"]:
                corrected_high = max(row["high"], row["low"], row["open"], row["close"])
                corrected_low = min(row["high"], row["low"], row["open"], row["close"])

                cleaned_data.at[idx, "high"] = corrected_high
                cleaned_data.at[idx, "low"] = corrected_low

                corrections.append(
                    {
                        "row": idx,
                        "type": "high_low_swap",
                        "original": {"high": row["high"], "low": row["low"]},
                        "corrected": {"high": corrected_high, "low": corrected_low},
                    }
                )
                row_corrections += 2

            # 确保开盘价在高低价范围内
            if not (row["low"] <= row["open"] <= row["high"]):
                corrected_open = np.clip(row["open"], row["low"], row["high"])
                corrections.append(
                    {
                        "row": idx,
                        "type": "open_range",
                        "original": {"open": row["open"]},
                        "corrected": {"open": corrected_open},
                    }
                )
                cleaned_data.at[idx, "open"] = corrected_open
                row_corrections += 1

            # 确保收盘价在高低价范围内
            if not (row["low"] <= row["close"] <= row["high"]):
                corrected_close = np.clip(row["close"], row["low"], row["high"])
                corrections.append(
                    {
                        "row": idx,
                        "type": "close_range",
                        "original": {"close": row["close"]},
                        "corrected": {"close": corrected_close},
                    }
                )
                cleaned_data.at[idx, "close"] = corrected_close
                row_corrections += 1

            total_corrections += row_corrections

        cleaning_info = {
            "operation": "validate_price_consistency",
            "total_corrections": total_corrections,
            "corrected_rows": len(set([c["row"] for c in corrections])),
            "corrections": corrections[:10],  # 只记录前10个修正
            "timestamp": datetime.now().isoformat(),
        }

        self.cleaning_log.append(cleaning_info)
        logger.info(
            f"价格一致性检查：修正了 {total_corrections} 个价格异常，涉及 {cleaning_info['corrected_rows']} 行"
        )

        return cleaned_data, cleaning_info

    def clean_data(
        self,
        data: pd.DataFrame,
        data_type: str = "price_data",
        cleaning_steps: List[str] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        执行完整的数据清洗流程

        Args:
            data: 输入数据
            data_type: 数据类型
            cleaning_steps: 清洗步骤列表

        Returns:
            清洗后的数据和清洗报告
        """
        if cleaning_steps is None:
            cleaning_steps = [
                "remove_duplicates",
                "standardize_types",
                "handle_missing",
                "handle_outliers",
                "validate_consistency",
            ]

        logger.info(f"开始数据清洗：{data_type}, 原始数据量：{len(data)}")

        cleaned_data = data.copy()
        cleaning_report = {
            "data_type": data_type,
            "original_shape": data.shape,
            "final_shape": None,
            "steps_performed": [],
            "total_removed_rows": 0,
            "cleaning_time_start": datetime.now().isoformat(),
        }

        for step in cleaning_steps:
            if step == "remove_duplicates":
                # 对于价格数据，使用日期和股票代码作为重复判断依据
                subset = ["symbol", "date"] if data_type == "price_data" else None
                cleaned_data, step_info = self.remove_duplicates(
                    cleaned_data, subset=subset
                )

            elif step == "standardize_types":
                cleaned_data, step_info = self.standardize_data_types(cleaned_data)

            elif step == "handle_missing":
                # 对于时间序列数据，使用插值处理缺失值
                strategy = "interpolate" if data_type == "price_data" else "fill"
                cleaned_data, step_info = self.handle_missing_values(
                    cleaned_data, strategy=strategy
                )

            elif step == "handle_outliers":
                # 只对价格数据使用IQR方法盖帽处理
                if data_type == "price_data":
                    price_columns = ["open", "high", "low", "close"]
                    cleaned_data, step_info = self.detect_and_handle_outliers(
                        cleaned_data, columns=price_columns, action="cap"
                    )
                else:
                    step_info = {"operation": "handle_outliers", "skipped": True}

            elif step == "validate_consistency":
                if data_type == "price_data":
                    cleaned_data, step_info = self.validate_price_consistency(
                        cleaned_data
                    )
                else:
                    step_info = {"operation": "validate_consistency", "skipped": True}
            else:
                step_info = {"operation": step, "skipped": True}

            cleaning_report["steps_performed"].append(step_info)

        # 最终验证
        final_validation = self.validator.validate(cleaned_data, data_type)
        cleaning_report["final_validation"] = final_validation

        cleaning_report["final_shape"] = cleaned_data.shape
        cleaning_report["total_removed_rows"] = data.shape[0] - cleaned_data.shape[0]
        cleaning_report["cleaning_time_end"] = datetime.now().isoformat()

        logger.info(
            f"数据清洗完成：{data_type}, 最终数据量：{len(cleaned_data)}, "
            f"删除行数：{cleaning_report['total_removed_rows']}"
        )

        return cleaned_data, cleaning_report


def test_data_cleaner():
    """测试数据清洗器"""
    cleaner = DataCleaner()

    # 创建包含各种问题的测试数据
    print("=== 测试数据清洗器 ===")

    test_data = pd.DataFrame(
        {
            "symbol": [
                "000001",
                "000001",
                "000001",
                "000002",
                "000002",
                "000001",
            ],  # 包含重复
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-01",
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
            ],
            "open": [10.0, 10.1, 10.0, None, 20.0, 10.2],  # 包含重复和缺失值
            "high": [9.5, 10.3, 10.2, 20.5, 20.8, 10.4],  # 包含价格异常
            "low": [10.2, 9.9, 9.8, 19.8, 19.5, 9.9],  # 包含价格异常
            "close": [10.1, 10.2, 10.1, 20.2, 20.3, 10.3],
            "volume": [1000000, 1200000, 1000000, -500000, 2000000, 800000],  # 包含负值
        }
    )

    print("原始数据：")
    print(test_data)
    print(f"原始数据形状：{test_data.shape}")

    # 执行清洗
    cleaned_data, report = cleaner.clean_data(test_data, "price_data")

    print(f"\n清洗后数据形状：{cleaned_data.shape}")
    print("清洗后数据：")
    print(cleaned_data)

    print(f"\n清洗报告：")
    print(f"删除行数：{report['total_removed_rows']}")
    for step_info in report["steps_performed"]:
        if "removed_count" in step_info:
            print(f"- {step_info['operation']}: 删除 {step_info['removed_count']} 行")
        if "handled_missing" in step_info:
            print(
                f"- {step_info['operation']}: 处理 {step_info['handled_missing']} 个缺失值"
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_data_cleaner()

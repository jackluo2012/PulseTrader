"""
数据转换器
提供数据格式转换和特征工程功能
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Optional TA-Lib import
try:
    import talib

    TALIB_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("TA-Lib is available for technical indicators")
except ImportError:
    TALIB_AVAILABLE = False
    talib = None
    logger = logging.getLogger(__name__)
    logger.warning("TA-Lib is not available. Technical indicators will be disabled.")

logger = logging.getLogger(__name__)


class DataTransformer:
    """数据转换器"""

    def __init__(self):
        """初始化转换器"""
        self.transformation_log = []

    def normalize_price_data(
        self, data: pd.DataFrame, method: str = "minmax"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        价格数据标准化

        Args:
            data: 价格数据
            method: 标准化方法（minmax, zscore, robust）

        Returns:
            标准化后的数据和转换信息
        """
        if data.empty:
            return data.copy(), {}

        price_columns = ["open", "high", "low", "close"]
        price_columns = [col for col in price_columns if col in data.columns]

        if not price_columns:
            logger.warning("没有找到价格列，跳过标准化")
            return data.copy(), {}

        transformed_data = data.copy()
        scaling_params = {}

        for col in price_columns:
            if method == "minmax":
                min_val = transformed_data[col].min()
                max_val = transformed_data[col].max()
                if max_val > min_val:
                    transformed_data[f"{col}_normalized"] = (
                        transformed_data[col] - min_val
                    ) / (max_val - min_val)
                else:
                    transformed_data[f"{col}_normalized"] = 0

                scaling_params[col] = {"min": min_val, "max": max_val}

            elif method == "zscore":
                mean_val = transformed_data[col].mean()
                std_val = transformed_data[col].std()
                if std_val > 0:
                    transformed_data[f"{col}_normalized"] = (
                        transformed_data[col] - mean_val
                    ) / std_val
                else:
                    transformed_data[f"{col}_normalized"] = 0

                scaling_params[col] = {"mean": mean_val, "std": std_val}

            elif method == "robust":
                median_val = transformed_data[col].median()
                mad_val = (
                    (transformed_data[col] - median_val).abs().median()
                )  # Median Absolute Deviation
                if mad_val > 0:
                    transformed_data[f"{col}_normalized"] = (
                        transformed_data[col] - median_val
                    ) / mad_val
                else:
                    transformed_data[f"{col}_normalized"] = 0

                scaling_params[col] = {"median": median_val, "mad": mad_val}

        transformation_info = {
            "operation": "normalize_price_data",
            "method": method,
            "columns": price_columns,
            "scaling_params": scaling_params,
            "timestamp": datetime.now().isoformat(),
        }

        self.transformation_log.append(transformation_info)
        logger.info(f"价格数据标准化完成：{method}, 处理了 {len(price_columns)} 列")

        return transformed_data, transformation_info

    def calculate_technical_indicators(
        self, data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        计算技术指标

        Args:
            data: OHLCV数据

        Returns:
            包含技术指标的数据和计算信息
        """
        if not TALIB_AVAILABLE:
            logger.warning(
                "TA-Lib is not available. Skipping technical indicators calculation."
            )
            return data.copy(), {
                "operation": "calculate_technical_indicators",
                "skipped": True,
                "reason": "TA-Lib not available",
                "timestamp": datetime.now().isoformat(),
            }

        if data.empty or len(data) < 20:
            logger.warning("数据不足，跳过技术指标计算")
            return data.copy(), {
                "operation": "calculate_technical_indicators",
                "skipped": True,
            }

        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            logger.warning(f"缺少必要列 {missing_columns}，跳过技术指标计算")
            return data.copy(), {
                "operation": "calculate_technical_indicators",
                "missing_columns": missing_columns,
            }

        transformed_data = data.copy()
        indicators_calculated = []

        try:
            # 移动平均线
            for period in [5, 10, 20, 60]:
                if len(data) >= period:
                    transformed_data[f"ma_{period}"] = talib.SMA(
                        data["close"].values, timeperiod=period
                    )
                    indicators_calculated.append(f"ma_{period}")

            # 指数移动平均线
            for period in [12, 26]:
                if len(data) >= period:
                    transformed_data[f"ema_{period}"] = talib.EMA(
                        data["close"].values, timeperiod=period
                    )
                    indicators_calculated.append(f"ema_{period}")

            # MACD
            if len(data) >= 26:
                macd, macd_signal, macd_hist = talib.MACD(data["close"].values)
                transformed_data["macd"] = macd
                transformed_data["macd_signal"] = macd_signal
                transformed_data["macd_histogram"] = macd_hist
                indicators_calculated.extend(["macd", "macd_signal", "macd_histogram"])

            # RSI
            if len(data) >= 14:
                rsi = talib.RSI(data["close"].values)
                transformed_data["rsi"] = rsi
                indicators_calculated.append("rsi")

            # 布林带
            if len(data) >= 20:
                bb_upper, bb_middle, bb_lower = talib.BBANDS(data["close"].values)
                transformed_data["bb_upper"] = bb_upper
                transformed_data["bb_middle"] = bb_middle
                transformed_data["bb_lower"] = bb_lower
                transformed_data["bb_width"] = (bb_upper - bb_lower) / bb_middle
                transformed_data["bb_position"] = (data["close"] - bb_lower) / (
                    bb_upper - bb_lower
                )
                indicators_calculated.extend(
                    ["bb_upper", "bb_middle", "bb_lower", "bb_width", "bb_position"]
                )

            # KDJ
            if len(data) >= 14:
                high_values = data["high"].values
                low_values = data["low"].values
                close_values = data["close"].values

                k, d = talib.STOCH(high_values, low_values, close_values)
                transformed_data["stoch_k"] = k
                transformed_data["stoch_d"] = d
                transformed_data["stoch_j"] = 3 * k - 2 * d
                indicators_calculated.extend(["stoch_k", "stoch_d", "stoch_j"])

            # 成交量指标
            if len(data) >= 20:
                transformed_data["volume_sma_20"] = talib.SMA(
                    data["volume"].values, timeperiod=20
                )
                transformed_data["volume_ratio"] = (
                    data["volume"] / transformed_data["volume_sma_20"]
                )
                indicators_calculated.extend(["volume_sma_20", "volume_ratio"])

            # 价格变化指标
            transformed_data["price_change"] = data["close"].pct_change()
            if len(data) >= 5:
                transformed_data["price_change_5"] = data["close"].pct_change(5)
            transformed_data["high_low_ratio"] = data["high"] / data["low"]
            transformed_data["open_close_ratio"] = data["open"] / data["close"]
            indicators_calculated.extend(
                ["price_change", "high_low_ratio", "open_close_ratio"]
            )
            if len(data) >= 5:
                indicators_calculated.append("price_change_5")

            transformation_info = {
                "operation": "calculate_technical_indicators",
                "indicators_calculated": indicators_calculated,
                "data_points": len(data),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"技术指标计算失败：{e}")
            transformation_info = {
                "operation": "calculate_technical_indicators",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        self.transformation_log.append(transformation_info)
        logger.info(
            f"技术指标计算完成：{len(indicators_calculated) if 'indicators_calculated' in locals() else 0} 个指标"
        )

        return transformed_data, transformation_info

    def resample_data(
        self, data: pd.DataFrame, timeframe: str = "D", date_column: str = "date"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        数据重采样（时间周期转换）

        Args:
            data: 输入数据
            timeframe: 目标时间周期（T=分钟, H=小时, D=天, W=周, M=月）
            date_column: 日期列名

        Returns:
            重采样后的数据和转换信息
        """
        if date_column not in data.columns:
            logger.error(f"日期列 '{date_column}' 不存在")
            return data.copy(), {"error": f"Missing date column: {date_column}"}

        if data.empty:
            return data.copy(), {"operation": "resample_data", "skipped": "Empty data"}

        # 确保日期列是datetime类型
        data_copy = data.copy()
        data_copy[date_column] = pd.to_datetime(data_copy[date_column])
        data_copy = data_copy.set_index(date_column)

        # 定义重采样规则
        resample_rules = {
            "T": "1T",  # 1分钟
            "5T": "5T",  # 5分钟
            "15T": "15T",  # 15分钟
            "30T": "30T",  # 30分钟
            "H": "1H",  # 1小时
            "D": "1D",  # 1天
            "W": "1W",  # 1周
            "M": "1M",  # 1月
        }

        rule = resample_rules.get(timeframe, timeframe)

        try:
            # OHLCV重采样
            if all(
                col in data_copy.columns for col in ["open", "high", "low", "close"]
            ):
                resampled = data_copy.resample(rule).agg(
                    {
                        "open": "first",
                        "high": "max",
                        "low": "min",
                        "close": "last",
                        "volume": "sum",
                    }
                )
            else:
                # 通用重采样
                numeric_columns = data_copy.select_dtypes(include=[np.number]).columns
                resampled = data_copy[numeric_columns].resample(rule).mean()

            # 移除空行
            resampled = resampled.dropna()

            # 重置索引
            resampled = resampled.reset_index()

            transformation_info = {
                "operation": "resample_data",
                "original_timeframe": "original",
                "target_timeframe": timeframe,
                "original_rows": len(data),
                "resampled_rows": len(resampled),
                "compression_ratio": len(resampled) / len(data) if len(data) > 0 else 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"数据重采样失败：{e}")
            resampled = data.reset_index()
            transformation_info = {
                "operation": "resample_data",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        self.transformation_log.append(transformation_info)
        logger.info(f"数据重采样完成：{len(data)} -> {len(resampled)} 行")

        return resampled, transformation_info

    def create_features(
        self, data: pd.DataFrame, feature_types: List[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        特征工程

        Args:
            data: 输入数据
            feature_types: 特征类型列表

        Returns:
            包含新特征的数据和特征信息
        """
        if feature_types is None:
            feature_types = ["lag", "rolling", "time", "interaction"]

        if data.empty:
            return data.copy(), {
                "operation": "create_features",
                "skipped": "Empty data",
            }

        transformed_data = data.copy()
        features_created = []

        try:
            # 滞后特征
            if "lag" in feature_types and "close" in transformed_data.columns:
                for lag in [1, 2, 3, 5, 10]:
                    if len(data) > lag:
                        transformed_data[f"close_lag_{lag}"] = transformed_data[
                            "close"
                        ].shift(lag)
                        features_created.append(f"close_lag_{lag}")

            # 滚动窗口特征
            if "rolling" in feature_types and "close" in transformed_data.columns:
                for window in [5, 10, 20]:
                    if len(data) > window:
                        transformed_data[f"close_mean_{window}"] = (
                            transformed_data["close"].rolling(window).mean()
                        )
                        transformed_data[f"close_std_{window}"] = (
                            transformed_data["close"].rolling(window).std()
                        )
                        transformed_data[f"close_max_{window}"] = (
                            transformed_data["close"].rolling(window).max()
                        )
                        transformed_data[f"close_min_{window}"] = (
                            transformed_data["close"].rolling(window).min()
                        )

                        features_created.extend(
                            [
                                f"close_mean_{window}",
                                f"close_std_{window}",
                                f"close_max_{window}",
                                f"close_min_{window}",
                            ]
                        )

            # 时间特征
            if "time" in feature_types and "date" in transformed_data.columns:
                transformed_data["date"] = pd.to_datetime(transformed_data["date"])
                transformed_data["day_of_week"] = transformed_data["date"].dt.dayofweek
                transformed_data["month"] = transformed_data["date"].dt.month
                transformed_data["quarter"] = transformed_data["date"].dt.quarter
                transformed_data["is_month_end"] = transformed_data[
                    "date"
                ].dt.is_month_end.astype(int)

                features_created.extend(
                    ["day_of_week", "month", "quarter", "is_month_end"]
                )

            # 交互特征
            if "interaction" in feature_types:
                if all(
                    col in transformed_data.columns for col in ["high", "low", "close"]
                ):
                    transformed_data["price_range"] = (
                        transformed_data["high"] - transformed_data["low"]
                    )
                    transformed_data["price_position"] = (
                        transformed_data["close"] - transformed_data["low"]
                    ) / (transformed_data["high"] - transformed_data["low"])
                    transformed_data["body_size"] = (
                        abs(transformed_data["close"] - transformed_data["open"])
                        / transformed_data["open"]
                    )

                    features_created.extend(
                        ["price_range", "price_position", "body_size"]
                    )

            transformation_info = {
                "operation": "create_features",
                "feature_types": feature_types,
                "features_created": features_created,
                "total_features": len(features_created),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"特征创建失败：{e}")
            transformation_info = {
                "operation": "create_features",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        self.transformation_log.append(transformation_info)
        logger.info(
            f"特征创建完成：{len(features_created) if 'features_created' in locals() else 0} 个特征"
        )

        return transformed_data, transformation_info

    def transform_data(
        self,
        data: pd.DataFrame,
        transformations: List[str] = None,
        data_type: str = "price_data",
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        执行完整的数据转换流程

        Args:
            data: 输入数据
            transformations: 转换步骤列表
            data_type: 数据类型

        Returns:
            转换后的数据和转换报告
        """
        if transformations is None:
            transformations = ["normalize", "indicators", "features"]

        logger.info(f"开始数据转换：{data_type}, 数据量：{len(data)}")

        transformed_data = data.copy()
        transformation_report = {
            "data_type": data_type,
            "original_shape": data.shape,
            "final_shape": None,
            "transformations_performed": [],
            "transformation_time_start": datetime.now().isoformat(),
        }

        for transform in transformations:
            if transform == "normalize" and data_type == "price_data":
                transformed_data, step_info = self.normalize_price_data(
                    transformed_data
                )

            elif transform == "indicators" and data_type == "price_data":
                transformed_data, step_info = self.calculate_technical_indicators(
                    transformed_data
                )

            elif transform == "features":
                feature_types = ["lag", "rolling", "time", "interaction"]
                transformed_data, step_info = self.create_features(
                    transformed_data, feature_types
                )

            elif transform.startswith("resample_"):
                timeframe = transform.split("_")[1]
                transformed_data, step_info = self.resample_data(
                    transformed_data, timeframe
                )

            else:
                step_info = {"operation": transform, "skipped": True}

            transformation_report["transformations_performed"].append(step_info)

        transformation_report["final_shape"] = transformed_data.shape
        transformation_report["transformation_time_end"] = datetime.now().isoformat()

        logger.info(f"数据转换完成：{data_type}, 最终数据量：{len(transformed_data)}")

        return transformed_data, transformation_report


def test_data_transformer():
    """测试数据转换器"""
    transformer = DataTransformer()

    # 创建测试数据
    print("=== 测试数据转换器 ===")

    # 生成60天的模拟股票数据
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    np.random.seed(42)

    # 模拟价格走势
    base_price = 100
    returns = np.random.normal(0, 0.02, 60)
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    test_data = pd.DataFrame(
        {
            "symbol": ["000001"] * 60,
            "date": dates,
            "open": prices,
            "high": [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            "low": [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            "close": prices,
            "volume": np.random.randint(1000000, 5000000, 60),
        }
    )

    print(f"测试数据：{len(test_data)} 行")
    print(test_data.head())

    # 执行转换
    transformed_data, report = transformer.transform_data(test_data, "price_data")

    print(
        f"\n转换后数据：{len(transformed_data)} 行 x {len(transformed_data.columns)} 列"
    )
    print(
        "新增列：",
        [col for col in transformed_data.columns if col not in test_data.columns][:10],
    )

    if not transformed_data.empty:
        print("\n技术指标示例：")
        if "rsi" in transformed_data.columns:
            print(
                f"RSI范围：{transformed_data['rsi'].min():.2f} - {transformed_data['rsi'].max():.2f}"
            )
        if "ma_20" in transformed_data.columns:
            print(
                f"MA20范围：{transformed_data['ma_20'].min():.2f} - {transformed_data['ma_20'].max():.2f}"
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_data_transformer()

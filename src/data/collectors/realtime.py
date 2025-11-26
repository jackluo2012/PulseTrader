"""
实时行情数据采集器
获取A股实时报价、分时数据等
"""

import logging
from datetime import datetime, time
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class RealtimeCollector(BaseCollector):
    """实时行情数据采集器"""

    def __init__(
        self, delay: float = None, max_retries: int = None, use_config: bool = True
    ):
        super().__init__(max_retries=max_retries, delay=delay, use_config=use_config)

    def is_trading_time(self) -> bool:
        """判断是否为交易时间"""
        now = datetime.now().time()

        # A股交易时间
        morning_start = time(9, 30)
        morning_end = time(11, 30)
        afternoon_start = time(13, 0)
        afternoon_end = time(15, 0)

        return (morning_start <= now <= morning_end) or (
            afternoon_start <= now <= afternoon_end
        )

    def collect_realtime_quote(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取个股实时行情

        Args:
            symbol: 股票代码

        Returns:
            实时行情数据
        """
        if not self.is_trading_time():
            logger.warning(f"非交易时间，跳过实时行情获取: {symbol}")
            return pd.DataFrame()

        logger.info(f"获取实时行情: {symbol}")

        # 使用Akshare获取实时行情
        realtime_data = self._call_api(ak.stock_zh_a_spot_em)

        if realtime_data is not None:
            # 筛选指定股票
            if "代码" in realtime_data.columns:
                stock_data = realtime_data[realtime_data["代码"] == symbol]
                if not stock_data.empty:
                    # 添加时间戳
                    stock_data["timestamp"] = datetime.now()
                    stock_data["symbol"] = symbol
                    logger.info(f"获取到实时行情: {symbol}")
                    return stock_data

        return pd.DataFrame()

    def collect_batch_quotes(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """
        批量获取实时行情

        Args:
            symbols: 股票代码列表

        Returns:
            批量行情数据
        """
        if not self.is_trading_time():
            logger.warning("非交易时间，跳过批量实时行情获取")
            return pd.DataFrame()

        logger.info(f"批量获取实时行情: {len(symbols)} 只股票")

        # 获取全市场实时行情
        all_quotes = self._call_api(ak.stock_zh_a_spot_em)

        if all_quotes is not None and not all_quotes.empty:
            # 筛选目标股票
            if "代码" in all_quotes.columns:
                filtered_quotes = all_quotes[all_quotes["代码"].isin(symbols)]

                if not filtered_quotes.empty:
                    # 添加时间戳和标准化列名
                    filtered_quotes["timestamp"] = datetime.now()
                    filtered_quotes["symbol"] = filtered_quotes["代码"]
                    filtered_quotes["stock_name"] = filtered_quotes["名称"]

                    logger.info(f"获取到 {len(filtered_quotes)} 只股票的实时行情")
                    return filtered_quotes

        return pd.DataFrame()

    def collect_intraday_data(
        self, symbol: str, period: str = "1"
    ) -> Optional[pd.DataFrame]:
        """
        获取分时数据

        Args:
            symbol: 股票代码
            period: 周期，1=1分钟，5=5分钟

        Returns:
            分时数据
        """
        if not self.is_trading_time() and period == "1":
            logger.warning(f"非交易时间，分钟线数据可能不完整: {symbol}")

        logger.info(f"获取分时数据: {symbol}, 周期: {period}分钟")

        # 使用Akshare获取分钟K线数据
        if period == "1":
            intraday_data = self._call_api(
                ak.stock_zh_a_hist_min_em, symbol=symbol, period="1", adjust="qfq"
            )
        elif period == "5":
            intraday_data = self._call_api(
                ak.stock_zh_a_hist_min_em, symbol=symbol, period="5", adjust="qfq"
            )
        else:
            logger.error(f"不支持的周期: {period}")
            return None

        if intraday_data is not None and not intraday_data.empty:
            # 添加股票代码
            intraday_data["symbol"] = symbol
            intraday_data["period"] = period
            intraday_data["collected_at"] = datetime.now()

            # 标准化列名（根据实际返回的列名调整）
            column_mapping = {
                "时间": "datetime",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
            }

            # 应用列名映射（存在的列才映射）
            for old_name, new_name in column_mapping.items():
                if old_name in intraday_data.columns:
                    intraday_data[new_name] = intraday_data[old_name]

            logger.info(f"获取到 {len(intraday_data)} 条分时数据")

        return intraday_data

    def collect_market_overview(self) -> Optional[pd.DataFrame]:
        """
        获取市场概览数据

        Returns:
            市场概览信息
        """
        logger.info("获取市场概览数据")

        try:
            # 使用更稳定的接口获取主要指数数据
            # 方法1: 使用 stock_zh_a_spot_em 获取实时行情，然后筛选指数
            market_data = self._call_api(ak.stock_zh_a_spot_em)

            if market_data is not None and not market_data.empty:
                # 筛选主要指数
                major_indices = [
                    "上证指数",
                    "深证成指",
                    "创业板指",
                    "沪深300",
                    "中证500",
                ]
                indices_data = []

                for index_name in major_indices:
                    if "名称" in market_data.columns:
                        index_row = market_data[market_data["名称"] == index_name]
                        if not index_row.empty:
                            index_info = {
                                "index_name": index_name,
                                "timestamp": datetime.now(),
                                "collected_at": datetime.now(),
                            }

                            # 提取价格信息
                            if "最新价" in index_row.columns:
                                index_info["latest_price"] = index_row["最新价"].iloc[0]
                            if "涨跌额" in index_row.columns:
                                index_info["change_amount"] = index_row["涨跌额"].iloc[
                                    0
                                ]
                            if "涨跌幅" in index_row.columns:
                                index_info["change_percent"] = index_row["涨跌幅"].iloc[
                                    0
                                ]
                            if "代码" in index_row.columns:
                                index_info["symbol"] = index_row["代码"].iloc[0]

                            indices_data.append(index_info)

                if indices_data:
                    logger.info(f"获取到 {len(indices_data)} 个主要指数数据")
                    return pd.DataFrame(indices_data)

            # 方法2: 备用方案 - 使用单只指数接口
            logger.info("尝试备用方案获取指数数据")
            index_codes = ["000001", "399001", "399006"]  # 上证指数、深证成指、创业板指
            index_names = ["上证指数", "深证成指", "创业板指"]

            indices_data = []
            for code, name in zip(index_codes, index_names):
                try:
                    # 使用 stock_zh_a_hist 获取最新交易日数据
                    index_data = self._call_api(
                        ak.stock_zh_a_hist,
                        symbol=code,
                        period="daily",
                        start_date=datetime.now().strftime("%Y%m%d"),
                        end_date=datetime.now().strftime("%Y%m%d"),
                        adjust="",
                    )

                    if index_data is not None and not index_data.empty:
                        index_info = {
                            "index_name": name,
                            "symbol": code,
                            "timestamp": datetime.now(),
                            "collected_at": datetime.now(),
                        }

                        if "收盘" in index_data.columns:
                            index_info["latest_price"] = index_data["收盘"].iloc[0]
                        if "涨跌额" in index_data.columns:
                            index_info["change_amount"] = index_data["涨跌额"].iloc[0]
                        if "涨跌幅" in index_data.columns:
                            index_info["change_percent"] = index_data["涨跌幅"].iloc[0]

                        indices_data.append(index_info)
                        logger.info(f"获取指数数据成功: {name}")

                except Exception as e:
                    logger.warning(f"获取指数数据失败 {name}: {e}")
                    continue

            if indices_data:
                return pd.DataFrame(indices_data)

        except Exception as e:
            logger.error(f"获取市场概览数据失败: {e}")

        # 返回空DataFrame而不是None，保持接口一致性
        logger.warning("未能获取市场概览数据，返回空DataFrame")
        return pd.DataFrame()

    def collect(
        self, data_type: str = "realtime_quote", **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        统一数据采集接口

        Args:
            data_type: 数据类型
            **kwargs: 其他参数

        Returns:
            采集的数据
        """
        if data_type == "realtime_quote":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取实时行情需要提供symbol参数")
                return None
            return self.collect_realtime_quote(symbol)

        elif data_type == "batch_quotes":
            symbols = kwargs.get("symbols", [])
            if not symbols:
                logger.error("批量获取行情需要提供symbols参数")
                return None
            return self.collect_batch_quotes(symbols)

        elif data_type == "intraday":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取分时数据需要提供symbol参数")
                return None
            period = kwargs.get("period", "1")
            return self.collect_intraday_data(symbol, period)

        elif data_type == "market_overview":
            return self.collect_market_overview()

        else:
            logger.error(f"不支持的数据类型: {data_type}")
            return None


def test_realtime_collector():
    """测试实时行情采集器"""
    collector = RealtimeCollector()

    print("=== 测试市场概览 ===")
    overview = collector.collect_market_overview()
    if overview is not None:
        print(overview)

    print("\n=== 测试个股实时行情 ===")
    # 测试一些知名股票
    test_symbols = ["000001", "000002", "600000"]
    for symbol in test_symbols:
        quote = collector.collect_realtime_quote(symbol)
        if quote is not None and not quote.empty:
            print(f"{symbol} 实时行情获取成功")
        else:
            print(f"{symbol} 实时行情获取失败或非交易时间")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    test_realtime_collector()

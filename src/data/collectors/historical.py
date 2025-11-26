"""
历史数据采集器
获取A股历史K线、财务数据等
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class HistoricalCollector(BaseCollector):
    """历史数据采集器"""

    def __init__(
        self, delay: float = None, max_retries: int = None, use_config: bool = True
    ):
        super().__init__(max_retries=max_retries, delay=delay, use_config=use_config)

    def collect_daily_kline(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq",
    ) -> Optional[pd.DataFrame]:
        """
        获取日线历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            adjust: 复权方式，qfq前复权，hfq后复权，不复权

        Returns:
            日线数据DataFrame
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        if not start_date:
            # 默认获取最近一年的数据
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        logger.info(
            f"获取日线数据: {symbol}, {start_date} ~ {end_date}, 复权: {adjust}"
        )

        # 使用Akshare获取历史数据
        historical_data = self._call_api(
            ak.stock_zh_a_hist,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )

        if historical_data is not None and not historical_data.empty:
            # 添加元数据
            historical_data["symbol"] = symbol
            historical_data["adjust_type"] = adjust
            historical_data["data_source"] = "akshare"
            historical_data["collected_at"] = datetime.now()

            # 标准化列名
            column_mapping = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_percent",
                "涨跌额": "change_amount",
                "换手率": "turnover",
            }

            # 应用列名映射
            for old_name, new_name in column_mapping.items():
                if old_name in historical_data.columns:
                    historical_data[new_name] = historical_data[old_name]

            logger.info(f"获取到 {len(historical_data)} 条日线数据")

        return historical_data

    def collect_weekly_kline(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq",
    ) -> Optional[pd.DataFrame]:
        """
        获取周线历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式

        Returns:
            周线数据DataFrame
        """
        logger.info(f"获取周线数据: {symbol}")

        # Akshare的周线数据接口
        weekly_data = self._call_api(
            ak.stock_zh_a_hist,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
            period="weekly",
        )

        if weekly_data is not None and not weekly_data.empty:
            weekly_data["symbol"] = symbol
            weekly_data["period"] = "weekly"
            weekly_data["adjust_type"] = adjust
            weekly_data["collected_at"] = datetime.now()

        return weekly_data

    def collect_financial_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取财务数据

        Args:
            symbol: 股票代码

        Returns:
            财务数据DataFrame
        """
        logger.info(f"获取财务数据: {symbol}")

        # 获取主要财务指标
        financial_indicators = self._call_api(
            ak.stock_financial_analysis_indicator, symbol=symbol
        )

        if financial_indicators is not None and not financial_indicators.empty:
            financial_indicators["symbol"] = symbol
            financial_indicators["collected_at"] = datetime.now()

        return financial_indicators

    def collect_batch_historical(
        self,
        symbols: List[str],
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq",
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取历史数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式

        Returns:
            股票代码到数据的映射
        """
        logger.info(f"批量获取历史数据: {len(symbols)} 只股票")

        results = {}

        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"处理进度: {i+1}/{len(symbols)} - {symbol}")

                data = self.collect_daily_kline(symbol, start_date, end_date, adjust)
                if data is not None and not data.empty:
                    results[symbol] = data
                else:
                    logger.warning(f"获取历史数据失败: {symbol}")

                # 批量获取时增加间隔
                if i < len(symbols) - 1:
                    time.sleep(self.delay)

            except Exception as e:
                logger.error(f"获取历史数据异常 {symbol}: {e}")
                continue

        logger.info(f"批量获取完成，成功: {len(results)}/{len(symbols)}")
        return results

    def collect_stock_dividends(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取股票分红数据

        Args:
            symbol: 股票代码

        Returns:
            分红数据DataFrame
        """
        logger.info(f"获取分红数据: {symbol}")

        # 获取分红数据
        dividend_data = self._call_api(ak.stock_dividend_cninfo, symbol=symbol)

        if dividend_data is not None and not dividend_data.empty:
            dividend_data["symbol"] = symbol
            dividend_data["collected_at"] = datetime.now()

        return dividend_data

    def collect(
        self, data_type: str = "daily_kline", **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        统一数据采集接口

        Args:
            data_type: 数据类型
            **kwargs: 其他参数

        Returns:
            采集的数据
        """
        if data_type == "daily_kline":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取日线数据需要提供symbol参数")
                return None
            return self.collect_daily_kline(
                symbol,
                kwargs.get("start_date"),
                kwargs.get("end_date"),
                kwargs.get("adjust", "qfq"),
            )

        elif data_type == "weekly_kline":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取周线数据需要提供symbol参数")
                return None
            return self.collect_weekly_kline(
                symbol,
                kwargs.get("start_date"),
                kwargs.get("end_date"),
                kwargs.get("adjust", "qfq"),
            )

        elif data_type == "financial_data":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取财务数据需要提供symbol参数")
                return None
            return self.collect_financial_data(symbol)

        elif data_type == "dividends":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取分红数据需要提供symbol参数")
                return None
            return self.collect_stock_dividends(symbol)

        elif data_type == "batch_historical":
            symbols = kwargs.get("symbols", [])
            if not symbols:
                logger.error("批量获取历史数据需要提供symbols参数")
                return None
            results = self.collect_batch_historical(
                symbols,
                kwargs.get("start_date"),
                kwargs.get("end_date"),
                kwargs.get("adjust", "qfq"),
            )
            # 返回第一个结果作为示例，实际应用中可能需要不同的处理方式
            return list(results.values())[0] if results else pd.DataFrame()

        else:
            logger.error(f"不支持的数据类型: {data_type}")
            return None


def test_historical_collector():
    """测试历史数据采集器"""
    collector = HistoricalCollector()

    print("=== 测试日线数据获取 ===")
    # 测试获取平安银行的历史数据
    daily_data = collector.collect_daily_kline("000001", "20240101", "20241201")
    if daily_data is not None:
        print(f"获取到 {len(daily_data)} 条日线数据")
        print(daily_data.head())
        print(f"列名: {list(daily_data.columns)}")

    print("\n=== 测试财务数据获取 ===")
    financial_data = collector.collect_financial_data("000001")
    if financial_data is not None:
        print(f"获取到 {len(financial_data)} 条财务数据")
        print(financial_data.head())


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    test_historical_collector()

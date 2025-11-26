"""
股票基础信息采集器
获取A股股票列表、基础信息等数据
"""

import logging
from datetime import datetime
from typing import List, Optional

import akshare as ak
import pandas as pd

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class StockInfoCollector(BaseCollector):
    """股票基础信息采集器"""

    def __init__(self, delay: float = 2.0):
        super().__init__(delay=delay)

    def collect_stock_list(self) -> Optional[pd.DataFrame]:
        """
        获取A股股票列表

        Returns:
            股票列表DataFrame
        """
        logger.info("开始获取A股股票列表...")

        # 获取沪市股票列表
        sh_stocks = self._call_api(ak.stock_info_a_code_name)
        if sh_stocks is not None:
            sh_stocks["market"] = "SH"
            sh_stocks["exchange"] = "上海证券交易所"

        # 获取深市股票列表
        sz_stocks = self._call_api(ak.stock_info_a_code_name)
        if sz_stocks is not None:
            sz_stocks["market"] = "SZ"
            sz_stocks["exchange"] = "深圳证券交易所"

        # 合并数据（这里简化处理，实际需要分别获取）
        all_stocks = sh_stocks if sh_stocks is not None else pd.DataFrame()

        if not all_stocks.empty:
            # 标准化列名
            if "code" in all_stocks.columns and "name" in all_stocks.columns:
                all_stocks = all_stocks.rename(
                    columns={"code": "symbol", "name": "stock_name"}
                )

            # 添加采集时间
            all_stocks["collected_at"] = datetime.now()
            all_stocks["is_active"] = 1

            logger.info(f"成功获取股票列表，共 {len(all_stocks)} 只股票")

        return all_stocks

    def collect_stock_detail(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        获取单只股票详细信息

        Args:
            symbol: 股票代码

        Returns:
            股票详细信息DataFrame
        """
        logger.info(f"获取股票详细信息: {symbol}")

        # 获取股票基本信息
        stock_info = self._call_api(ak.stock_individual_info_em, symbol=symbol)

        if stock_info is not None and not stock_info.empty:
            # 添加股票代码
            stock_info["symbol"] = symbol
            stock_info["collected_at"] = datetime.now()

            # 转置数据，使item列为字段名
            if "item" in stock_info.columns and "value" in stock_info.columns:
                stock_info = stock_info.set_index("item")["value"].to_frame().T
                stock_info["symbol"] = symbol
                stock_info["collected_at"] = datetime.now()

        return stock_info

    def collect_industry_stocks(self, industry_name: str) -> Optional[pd.DataFrame]:
        """
        获取行业股票列表

        Args:
            industry_name: 行业名称

        Returns:
            行业股票列表DataFrame
        """
        logger.info(f"获取行业股票列表: {industry_name}")

        # 这里使用概念股板块接口作为示例
        concept_stocks = self._call_api(
            ak.stock_board_concept_cons_em, symbol=industry_name
        )

        if concept_stocks is not None:
            concept_stocks["industry"] = industry_name
            concept_stocks["collected_at"] = datetime.now()

        return concept_stocks

    def collect(
        self, data_type: str = "stock_list", **kwargs
    ) -> Optional[pd.DataFrame]:
        """
        统一数据采集接口

        Args:
            data_type: 数据类型
            **kwargs: 其他参数

        Returns:
            采集的数据
        """
        if data_type == "stock_list":
            return self.collect_stock_list()
        elif data_type == "stock_detail":
            symbol = kwargs.get("symbol")
            if not symbol:
                logger.error("获取股票详情需要提供symbol参数")
                return None
            return self.collect_stock_detail(symbol)
        elif data_type == "industry_stocks":
            industry = kwargs.get("industry_name")
            if not industry:
                logger.error("获取行业股票需要提供industry_name参数")
                return None
            return self.collect_industry_stocks(industry)
        else:
            logger.error(f"不支持的数据类型: {data_type}")
            return None


def test_stock_info_collector():
    """测试股票信息采集器"""
    collector = StockInfoCollector()

    print("=== 测试股票列表获取 ===")
    stock_list = collector.collect_stock_list()
    if stock_list is not None:
        print(f"获取到 {len(stock_list)} 只股票")
        print(stock_list.head())

    print("\n=== 测试个股详情获取 ===")
    if stock_list is not None and len(stock_list) > 0:
        sample_symbol = stock_list.iloc[0]["symbol"]
        detail = collector.collect_stock_detail(sample_symbol)
        if detail is not None:
            print(f"股票 {sample_symbol} 详情:")
            print(detail.head())


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 运行测试
    test_stock_info_collector()

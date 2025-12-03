"""
ClickHouse批量数据插入工具
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from queue import Queue
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class BatchInserter:
    """批量数据插入器"""

    def __init__(self, db_client, batch_size: int = 10000, max_workers: int = 4):
        """
        初始化批量插入器

        Args:
            db_client: ClickHouse客户端
            batch_size: 批量大小
            max_workers: 最大并发线程数
        """
        self.db_client = db_client
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.insert_queue = Queue()
        self.error_count = 0
        self.success_count = 0
        self.lock = threading.Lock()

    def insert_dataframe(
        self, df: pd.DataFrame, table_name: str, columns_mapping: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        批量插入DataFrame数据

        Args:
            df: 要插入的数据
            table_name: 目标表名
            columns_mapping: 列名映射

        Returns:
            插入结果统计
        """
        if df.empty:
            logger.warning("数据为空，跳过插入")
            return {"inserted_rows": 0, "success": True, "message": "No data to insert"}

        start_time = time.time()

        # 应用列名映射
        if columns_mapping:
            df = df.rename(columns=columns_mapping)

        # 添加元数据
        if "created_at" not in df.columns:
            df["created_at"] = datetime.now()

        # 分批插入
        total_rows = len(df)
        inserted_rows = 0

        try:
            for i in range(0, total_rows, self.batch_size):
                batch_df = df.iloc[i : i + self.batch_size]

                try:
                    # 转换为ClickHouse格式
                    batch_data = self._prepare_data_for_clickhouse(batch_df)

                    # 构建插入SQL
                    columns_str = ", ".join(batch_df.columns)
                    placeholders = ", ".join(["%s"] * len(batch_df.columns))

                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES"

                    # 执行插入
                    self.db_client.execute_query(sql, batch_data)

                    inserted_rows += len(batch_df)
                    logger.info(f"插入进度: {inserted_rows}/{total_rows}")

                except Exception as e:
                    logger.error(f"批次插入失败 {table_name}: {e}")
                    with self.lock:
                        self.error_count += 1

            duration = time.time() - start_time
            success_rate = inserted_rows / total_rows

            result = {
                "inserted_rows": inserted_rows,
                "total_rows": total_rows,
                "success_rate": success_rate,
                "duration": duration,
                "rows_per_second": inserted_rows / duration if duration > 0 else 0,
                "success": success_rate > 0.9,  # 90%以上成功率视为成功
            }

            logger.info(
                f"插入完成 {table_name}: {inserted_rows}/{total_rows} 行, "
                f"成功率: {success_rate:.2%}, 耗时: {duration:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(f"批量插入失败 {table_name}: {e}")
            return {
                "inserted_rows": inserted_rows,
                "total_rows": total_rows,
                "error": str(e),
                "success": False,
            }

    def _prepare_data_for_clickhouse(self, df: pd.DataFrame) -> List[tuple]:
        """
        为ClickHouse准备数据

        Args:
            df: 输入DataFrame

        Returns:
            ClickHouse格式的数据列表
        """
        # 处理空值
        df = df.fillna("")

        # 转换日期时间格式
        for col in df.columns:
            if df[col].dtype == "datetime64[ns]":
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
            elif df[col].dtype == "object":
                # 处理字符串类型的空值
                df[col] = df[col].astype(str)
                df[col] = df[col].replace("nan", "")

        # 转换为元组列表
        return [tuple(row) for row in df.values]

    def insert_with_retry(self, data, table_name: str, max_retries: int = 3) -> bool:
        """
        带重试机制的数据插入

        Args:
            data: 要插入的数据
            table_name: 目标表名
            max_retries: 最大重试次数

        Returns:
            是否插入成功
        """
        for attempt in range(max_retries):
            try:
                self.db_client.execute_query(f"INSERT INTO {table_name} VALUES", data)
                return True

            except Exception as e:
                logger.warning(f"插入重试 {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # 指数退避
                else:
                    logger.error(f"插入最终失败 {table_name}: {e}")
                    return False

    def parallel_insert(
        self, data_batches: List[tuple], table_name: str
    ) -> Dict[str, Any]:
        """
        并行插入数据

        Args:
            data_batches: 数据批次列表
            table_name: 目标表名

        Returns:
            插入结果统计
        """
        start_time = time.time()
        success_count = 0
        error_count = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有插入任务
            future_to_batch = {
                executor.submit(self.insert_with_retry, batch, table_name): batch
                for batch in data_batches
            }

            # 收集结果
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    if future.result():
                        success_count += len(batch)
                    else:
                        error_count += len(batch)
                except Exception as e:
                    logger.error(f"并行插入异常: {e}")
                    error_count += len(batch)

        duration = time.time() - start_time
        total_rows = sum(len(batch) for batch in data_batches)

        result = {
            "success_rows": success_count,
            "error_rows": error_count,
            "total_rows": total_rows,
            "success_rate": success_count / total_rows if total_rows > 0 else 0,
            "duration": duration,
            "parallel_workers": self.max_workers,
        }

        logger.info(
            f"并行插入完成 {table_name}: {success_count}/{total_rows} 行, "
            f"成功率: {result['success_rate']:.2%}, 耗时: {duration:.2f}s"
        )

        return result

    def insert_daily_quotes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        插入日线行情数据（专用方法）

        Args:
            df: 日线数据DataFrame

        Returns:
            插入结果
        """
        # 列名映射
        columns_mapping = {
            "symbol": "symbol",
            "date": "date",
            "open": "open_price",
            "high": "high_price",
            "low": "low_price",
            "close": "close_price",
            "volume": "volume",
            "amount": "amount",
            "change": "change_amount",
            "pct_chg": "change_percent",
            "amplitude": "amplitude",
            "turnover": "turnover_rate",
        }

        # 数据验证
        required_columns = ["symbol", "date", "open", "high", "low", "close", "volume"]
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"缺少必需列: {missing_columns}")

        # 专用插入逻辑
        return self.insert_dataframe(df, "daily_quotes", columns_mapping)

    def insert_realtime_snapshot(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        插入实时快照数据

        Args:
            df: 实时数据DataFrame

        Returns:
            插入结果
        """
        # 添加更新时间
        if "updated_at" not in df.columns:
            df["updated_at"] = datetime.now()

        # 增加更新计数（简单实现）
        df["update_count"] = 1

        return self.insert_dataframe(df, "realtime_snapshot")


def test_batch_inserter():
    """测试批量插入器"""
    from src.data.database import db_manager

    inserter = BatchInserter(db_manager, batch_size=1000)

    # 创建测试数据
    test_data = pd.DataFrame(
        {
            "symbol": ["000001"] * 100,
            "date": pd.date_range("2024-01-01", periods=100),
            "open": [10.0] * 100,
            "high": [10.5] * 100,
            "low": [9.5] * 100,
            "close": [10.2] * 100,
            "volume": [1000000] * 100,
            "amount": [10200000] * 100,
        }
    )

    print("=== 测试批量插入 ===")
    result = inserter.insert_daily_quotes(test_data)
    print(f"插入结果: {result}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_batch_inserter()

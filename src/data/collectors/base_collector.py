"""
基础数据采集器
提供统一的Akshare接口调用和错误处理机制
"""

import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import akshare as ak
import pandas as pd

# 导入配置管理器
try:
    from ...config.config_manager import get_config_manager
except ImportError:
    # 如果在独立脚本中使用，尝试从相对路径导入
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    try:
        from src.config.config_manager import get_config_manager
    except ImportError:
        get_config_manager = None

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """数据采集器基类"""

    def __init__(
        self, max_retries: int = None, delay: float = None, use_config: bool = True
    ):
        """
        初始化采集器

        Args:
            max_retries: 最大重试次数，如果为None则从配置文件读取
            delay: 请求间隔时间（秒），如果为None则从配置文件读取
            use_config: 是否使用配置文件，默认为True
        """
        # 从配置文件读取参数
        if use_config and get_config_manager:
            config = get_config_manager()
            self.max_retries = (
                max_retries if max_retries is not None else config.get_max_retries()
            )
            self.delay = delay if delay is not None else config.get_delay()
        else:
            self.max_retries = max_retries if max_retries is not None else 3
            self.delay = delay if delay is not None else 1.0

        self.last_request_time = 0
        logger.info(
            f"初始化采集器: max_retries={self.max_retries}, delay={self.delay}s"
        )

    def _rate_limit(self):
        """请求频率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            logger.debug(f"请求频率限制，等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _call_api(self, func, *args, **kwargs) -> Optional[pd.DataFrame]:
        """
        安全调用Akshare API

        Args:
            func: Akshare函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            DataFrame或None（如果失败）
        """
        self._rate_limit()

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"调用API: {func.__name__}, 尝试次数: {attempt + 1}")

                # 调用API
                result = func(*args, **kwargs)

                # 验证结果
                if isinstance(result, pd.DataFrame):
                    if result.empty:
                        logger.warning(f"API返回空数据: {func.__name__}")
                        return pd.DataFrame()

                    logger.info(
                        f"成功获取数据: {len(result)} 行 x {len(result.columns)} 列"
                    )
                    return result
                else:
                    logger.error(f"API返回非DataFrame类型: {type(result)}")
                    return pd.DataFrame()

            except Exception as e:
                logger.error(
                    f"API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                )

                if attempt < self.max_retries - 1:
                    # 指数退避策略
                    wait_time = self.delay * (2**attempt)
                    logger.info(f"等待 {wait_time:.2f} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API调用最终失败: {func.__name__}")
                    return None

        return None

    @abstractmethod
    def collect(self, **kwargs) -> Optional[pd.DataFrame]:
        """抽象方法：子类必须实现数据采集逻辑"""
        pass

    def save_data(self, data: pd.DataFrame, filepath: str) -> bool:
        """
        保存数据到文件

        Args:
            data: 要保存的数据
            filepath: 文件路径

        Returns:
            是否保存成功
        """
        try:
            data.to_csv(filepath, index=False, encoding="utf-8-sig")
            logger.info(f"数据已保存到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            return False

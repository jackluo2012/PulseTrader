"""
配置管理器
统一管理数据采集相关的配置参数
"""

import logging
import os
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器类"""

    def __init__(self, config_path: str = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为项目根目录下的config/data_collection.yaml
        """
        if config_path is None:
            # 获取项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            config_path = os.path.join(project_root, "config", "data_collection.yaml")

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                logger.info(f"成功加载配置文件: {self.config_path}")
                return config
            else:
                logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "akshare": {
                "timeout": 30,
                "max_retries": 3,
                "delay": 1.0,
                "data_types": {
                    "stock_info": {
                        "enabled": True,
                        "update_interval": "1d",
                        "retry_on_error": True,
                    },
                    "realtime": {
                        "enabled": True,
                        "update_interval": "10s",
                        "trading_hours_only": True,
                    },
                    "historical": {
                        "enabled": True,
                        "update_interval": "1d",
                        "batch_size": 50,
                        "max_days_per_request": 365,
                    },
                    "financial": {
                        "enabled": True,
                        "update_interval": "1d",
                        "quarterly_update": True,
                    },
                },
            },
            "storage": {
                "clickhouse": {"batch_size": 1000, "connection_timeout": 30},
                "cache": {"redis": {"ttl": 3600, "max_memory": "100MB"}},
            },
            "error_handling": {
                "max_consecutive_errors": 5,
                "error_backoff_factor": 2,
                "notification_enabled": False,
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/data_collection.log",
                "max_size": "10MB",
                "backup_count": 5,
            },
            "performance": {
                "concurrent_workers": 4,
                "memory_limit": "1GB",
                "rate_limiting": True,
            },
            "data_quality": {
                "enable_validation": True,
                "duplicate_check": True,
                "missing_data_threshold": 0.1,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项，支持点号分隔的嵌套键

        Args:
            key: 配置键，如 'akshare.timeout' 或 'storage.clickhouse.batch_size'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_akshare_config(self) -> Dict[str, Any]:
        """获取 Akshare 相关配置"""
        return self.get("akshare", {})

    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储相关配置"""
        return self.get("storage", {})

    def get_error_handling_config(self) -> Dict[str, Any]:
        """获取错误处理相关配置"""
        return self.get("error_handling", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志相关配置"""
        return self.get("logging", {})

    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能相关配置"""
        return self.get("performance", {})

    def get_data_type_config(self, data_type: str) -> Optional[Dict[str, Any]]:
        """
        获取特定数据类型的配置

        Args:
            data_type: 数据类型，如 'stock_info', 'realtime', 'historical', 'financial'

        Returns:
            数据类型配置字典
        """
        return self.get(f"akshare.data_types.{data_type}")

    def is_data_type_enabled(self, data_type: str) -> bool:
        """检查数据类型是否启用"""
        config = self.get_data_type_config(data_type)
        return config.get("enabled", False) if config else False

    def get_timeout(self) -> int:
        """获取请求超时时间"""
        return self.get("akshare.timeout", 30)

    def get_max_retries(self) -> int:
        """获取最大重试次数"""
        return self.get("akshare.max_retries", 3)

    def get_delay(self) -> float:
        """获取请求间隔时间"""
        return self.get("akshare.delay", 1.0)

    def get_batch_size(self, data_type: str = "default") -> int:
        """获取批量处理大小"""
        if data_type == "historical":
            return self.get("akshare.data_types.historical.batch_size", 50)
        elif data_type == "clickhouse":
            return self.get("storage.clickhouse.batch_size", 1000)
        else:
            return 50

    def get_cache_ttl(self) -> int:
        """获取缓存过期时间"""
        return self.get("storage.cache.redis.ttl", 3600)

    def get_concurrent_workers(self) -> int:
        """获取并发工作线程数"""
        return self.get("performance.concurrent_workers", 4)

    def setup_logging(self):
        """根据配置设置日志"""
        log_config = self.get_logging_config()

        # 确保日志目录存在
        log_file = log_config.get("file")
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

        # 配置日志
        logging.basicConfig(
            level=getattr(logging, log_config.get("level", "INFO")),
            format=log_config.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            handlers=[
                logging.FileHandler(log_file) if log_file else logging.StreamHandler(),
                logging.StreamHandler(),
            ],
        )

    def reload(self):
        """重新加载配置"""
        self.config = self._load_config()
        logger.info("配置已重新加载")

    def validate_config(self) -> bool:
        """验证配置的有效性"""
        required_keys = [
            "akshare.timeout",
            "akshare.max_retries",
            "akshare.delay",
            "storage.clickhouse.batch_size",
        ]

        for key in required_keys:
            if self.get(key) is None:
                logger.error(f"缺少必需的配置项: {key}")
                return False

        return True

    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return f"ConfigManager(config_path={self.config_path})"


# 全局配置实例
_config_manager = None


def get_config_manager(config_path: str = None) -> ConfigManager:
    """
    获取全局配置管理器实例

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigManager实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """便捷的配置获取函数"""
    return get_config_manager().get(key, default)


def is_enabled(data_type: str) -> bool:
    """检查数据类型是否启用的便捷函数"""
    return get_config_manager().is_data_type_enabled(data_type)

"""
应用配置管理模块
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DatabaseConfig:
    """数据库配置"""

    host: str = "localhost"
    port: int = 8123
    user: str = "quant_user"
    password: str = "Quant@2024"
    database: str = "pulse_trader"


@dataclass
class RedisConfig:
    """Redis配置"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


@dataclass
class AppSettings:
    """应用设置"""

    env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # 数据路径
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    config_dir: Path = project_root / "config"
    logs_dir: Path = project_root / "data" / "logs"

    # 交易设置
    default_capital: float = 1000000.0
    max_position_size: float = 0.1
    commission_rate: float = 0.0003


class ConfigManager:
    """配置管理器"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self._load_env()

    def _load_env(self):
        """加载环境变量"""
        if os.path.exists(self.env_file):
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value.strip()

    def get_database_config(self) -> DatabaseConfig:
        """获取数据库配置"""
        return DatabaseConfig(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            user=os.getenv("CLICKHOUSE_USER", "quant_user"),
            password=os.getenv("CLICKHOUSE_PASSWORD", "Quant@2024"),
            database=os.getenv("CLICKHOUSE_DATABASE", "pulse_trader"),
        )

    def get_redis_config(self) -> RedisConfig:
        """获取Redis配置"""
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
        )

    def get_app_settings(self) -> AppSettings:
        """获取应用设置"""
        return AppSettings(
            env=os.getenv("APP_ENV", "development"),
            debug=os.getenv("DEBUG", "True").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            default_capital=float(os.getenv("DEFAULT_CAPITAL", "1000000.0")),
            max_position_size=float(os.getenv("MAX_POSITION_SIZE", "0.1")),
            commission_rate=float(os.getenv("COMMISSION_RATE", "0.0003")),
        )


# 全局配置管理器实例
config_manager = ConfigManager()
app_settings = config_manager.get_app_settings()
db_config = config_manager.get_database_config()
redis_config = config_manager.get_redis_config()

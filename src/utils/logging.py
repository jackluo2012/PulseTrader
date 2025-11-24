"""
日志管理工具
"""

import logging
import logging.config
import os
from pathlib import Path

import yaml

from src.config import app_settings


def setup_logging():
    """设置日志配置"""
    # 确保日志目录存在
    log_dirs = [
        app_settings.logs_dir / "app",
        app_settings.logs_dir / "database",
        app_settings.logs_dir / "system",
    ]

    for log_dir in log_dirs:
        log_dir.mkdir(parents=True, exist_ok=True)

    # 加载日志配置
    config_path = app_settings.config_dir / "logging" / "logging.yaml"

    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        # 如果配置文件不存在，使用基础配置
        logging.basicConfig(
            level=getattr(logging, app_settings.log_level),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)


# 初始化日志
setup_logging()

# 导出常用日志记录器
app_logger = get_logger("app")
db_logger = get_logger("database")
system_logger = get_logger("system")

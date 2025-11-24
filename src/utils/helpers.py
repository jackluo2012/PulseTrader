"""
通用工具函数
"""

import json
import os
import pickle
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def ensure_dir(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(file_path: Union[str, Path]) -> Dict:
    """加载JSON文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """保存JSON文件"""
    ensure_dir(Path(file_path).parent)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_pickle(file_path: Union[str, Path]) -> Any:
    """加载pickle文件"""
    with open(file_path, "rb") as f:
        return pickle.load(f)


def save_pickle(data: Any, file_path: Union[str, Path]) -> None:
    """保存pickle文件"""
    ensure_dir(Path(file_path).parent)
    with open(file_path, "wb") as f:
        pickle.dump(data, f)


def format_number(num: float, decimal_places: int = 2) -> str:
    """格式化数字显示"""
    if abs(num) >= 1e9:
        return f"{num/1e9:.{decimal_places}f}B"
    elif abs(num) >= 1e6:
        return f"{num/1e6:.{decimal_places}f}M"
    elif abs(num) >= 1e3:
        return f"{num/1e3:.{decimal_places}f}K"
    else:
        return f"{num:.{decimal_places}f}"


def format_percentage(num: float, decimal_places: int = 2) -> str:
    """格式化百分比显示"""
    return f"{num*100:.{decimal_places}f}%"


def validate_stock_symbol(symbol: str) -> bool:
    """验证股票代码格式"""
    import re

    # A股代码格式：6位数字+.+交易所(SH/SZ/BJ)
    pattern = r"^\d{6}\.(SH|SZ|BJ)$"
    return bool(re.match(pattern, symbol))


def parse_stock_symbol(symbol: str) -> Optional[tuple]:
    """解析股票代码"""
    if validate_stock_symbol(symbol):
        code, exchange = symbol.split(".")
        return code, exchange
    return None


def trading_days_between(
    start_date: Union[str, date], end_date: Union[str, date]
) -> int:
    """计算两个日期之间的交易日数量（简单计算，不包含节假日）"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 简单计算，假设每周5个交易日
    total_days = (end_date - start_date).days
    weeks = total_days // 7
    remaining_days = total_days % 7

    # 计算剩余天数中的工作日
    work_days = 0
    start_weekday = start_date.weekday()

    for i in range(remaining_days + 1):
        current_weekday = (start_weekday + i) % 7
        if current_weekday < 5:  # 周一到周五
            work_days += 1

    return weeks * 5 + work_days


def is_trading_day(date_check: Union[str, date]) -> bool:
    """检查是否为交易日（简单检查，不考虑节假日）"""
    if isinstance(date_check, str):
        date_check = datetime.strptime(date_check, "%Y-%m-%d").date()

    return date_check.weekday() < 5  # 周一到周五

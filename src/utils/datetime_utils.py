"""
日期时间工具函数
"""

from datetime import date, datetime, timedelta
from typing import List, Tuple, Union

import pandas as pd


def get_trading_dates(
    start_date: Union[str, date], end_date: Union[str, date]
) -> List[date]:
    """获取指定日期范围内的所有交易日（排除周末）"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    trading_dates = []
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() < 5:  # 周一到周五
            trading_dates.append(current_date)
        current_date += timedelta(days=1)

    return trading_dates


def get_last_trading_date(reference_date: Union[str, date] = None) -> date:
    """获取最近的交易日"""
    if reference_date is None:
        reference_date = date.today()
    elif isinstance(reference_date, str):
        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

    # 如果今天是交易日，返回今天；否则往前推
    if reference_date.weekday() < 5:
        return reference_date

    # 往前找最近的交易日
    days_back = 1
    while True:
        last_date = reference_date - timedelta(days=days_back)
        if last_date.weekday() < 5:
            return last_date
        days_back += 1


def date_range(
    start_date: Union[str, date], end_date: Union[str, date], freq: str = "D"
) -> List[date]:
    """生成日期范围"""
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)

    date_list = pd.date_range(start=start_date, end=end_date, freq=freq)
    return [d.date() for d in date_list]


def get_year_month_dates(year: int, month: int) -> Tuple[date, date]:
    """获取指定年月的开始和结束日期"""
    start_date = date(year, month, 1)

    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    return start_date, end_date


def format_date(dt: Union[str, date, datetime], format_str: str = "%Y-%m-%d") -> str:
    """格式化日期"""
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d")

    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    elif isinstance(dt, date):
        return dt.strftime(format_str)

    return str(dt)


def parse_date(dt_str: str, format_str: str = "%Y-%m-%d") -> date:
    """解析日期字符串"""
    return datetime.strptime(dt_str, format_str).date()

"""
测试工具函数
"""

import pytest

from src.utils.helpers import (
    format_number,
    format_percentage,
    is_trading_day,
    parse_stock_symbol,
    trading_days_between,
    validate_stock_symbol,
)


class TestStockSymbol:
    """测试股票符号相关函数"""

    def test_validate_valid_symbols(self):
        """测试有效的股票代码"""
        valid_symbols = ["000001.SZ", "600000.SH", "600036.SH", "688001.SH"]

        for symbol in valid_symbols:
            assert validate_stock_symbol(symbol) is True

    def test_validate_invalid_symbols(self):
        """测试无效的股票代码"""
        invalid_symbols = [
            "000001",  # 缺少交易所
            "SZ000001",  # 格式错误
            "000001SZ",  # 缺少点
            "000001.SZ1",  # 交易所错误
            "ABC.SZ",  # 非数字代码
            "12345.SZ",  # 代码长度错误
            "",  # 空字符串
        ]

        for symbol in invalid_symbols:
            assert validate_stock_symbol(symbol) is False

    def test_parse_stock_symbol(self):
        """测试股票代码解析"""
        result = parse_stock_symbol("000001.SZ")
        assert result == ("000001", "SZ")

        result = parse_stock_symbol("600036.SH")
        assert result == ("600036", "SH")

        result = parse_stock_symbol("invalid")
        assert result is None


class TestFormatFunctions:
    """测试格式化函数"""

    def test_format_number(self):
        """测试数字格式化"""
        assert format_number(1234) == "1.23K"
        assert format_number(1234567) == "1.23M"
        assert format_number(1234567890) == "1.23B"
        assert format_number(123) == "123.00"

    def test_format_percentage(self):
        """测试百分比格式化"""
        assert format_percentage(0.1234) == "12.34%"
        assert format_percentage(0.5) == "50.00%"
        assert format_percentage(1.0) == "100.00%"


class TestTradingUtils:
    """测试交易工具函数"""

    def test_trading_days_between(self):
        """测试交易日计算"""
        # 同一周
        days = trading_days_between("2024-01-01", "2024-01-05")
        assert days == 5  # 周一到周五

    def test_is_trading_day(self):
        """测试交易日判断"""
        import datetime

        # 周一应该是交易日
        monday = datetime.date(2024, 1, 8)  # 2024年1月8日是周一
        assert is_trading_day(monday) is True

        # 周六不应该交易日
        saturday = datetime.date(2024, 1, 6)  # 2024年1月6日是周六
        assert is_trading_day(saturday) is False

        # 周日不应该交易日
        sunday = datetime.date(2024, 1, 7)  # 2024年1月7日是周日
        assert is_trading_day(sunday) is False

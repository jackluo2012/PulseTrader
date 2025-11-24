"""
pytest配置和共享fixtures
"""

import os
import sys
from pathlib import Path

import pytest

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_stock_data():
    """提供示例股票数据"""
    return {
        "symbol": "000001.SZ",
        "name": "平安银行",
        "market": "SZ",
        "industry": "银行",
        "trade_date": "2024-01-15",
        "open": 10.50,
        "high": 10.80,
        "low": 10.40,
        "close": 10.65,
        "volume": 1000000,
        "amount": 10500000.0,
    }


@pytest.fixture
def sample_stock_list():
    """提供示例股票列表"""
    return [
        {"symbol": "000001.SZ", "name": "平安银行", "market": "SZ"},
        {"symbol": "600000.SH", "name": "浦发银行", "market": "SH"},
        {"symbol": "600036.SH", "name": "招商银行", "market": "SH"},
    ]


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """设置测试环境变量"""
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("CLICKHOUSE_PORT", "8123")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")
    monkeypatch.setenv("CLICKHOUSE_DATABASE", "test_pulse_trader")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "1")

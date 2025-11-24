"""
测试配置管理
"""

import os

import pytest

from src.config import AppSettings, ConfigManager, DatabaseConfig, RedisConfig


class TestConfigManager:
    """测试配置管理器"""

    def test_get_database_config(self):
        """测试数据库配置获取"""
        # 创建临时配置文件
        with open(".test_env", "w") as f:
            f.write("CLICKHOUSE_HOST=test-host\n")
            f.write("CLICKHOUSE_PORT=9999\n")
            f.write("CLICKHOUSE_USER=test-user\n")
            f.write("CLICKHOUSE_PASSWORD=test-pass\n")
            f.write("CLICKHOUSE_DATABASE=test-db\n")

        try:
            config = ConfigManager(".test_env")
            db_config = config.get_database_config()

            assert db_config.host == "test-host"
            assert db_config.port == 9999
            assert db_config.user == "test-user"
            assert db_config.password == "test-pass"
            assert db_config.database == "test-db"
        finally:
            os.remove(".test_env")

    def test_default_config_values(self):
        """测试默认配置值"""
        config = ConfigManager(".nonexistent_env")

        db_config = config.get_database_config()
        assert db_config.host == "localhost"
        assert db_config.port == 8123

        app_settings = config.get_app_settings()
        assert app_settings.env == "development"
        assert app_settings.debug is True

    def test_app_settings_paths(self):
        """测试应用设置路径"""
        settings = AppSettings()

        assert settings.project_root.exists()
        assert settings.data_dir.name == "data"
        assert settings.config_dir.name == "config"
        assert settings.logs_dir.name == "logs"

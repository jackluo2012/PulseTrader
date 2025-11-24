#!/usr/bin/env python3
"""
项目设置验证脚本
"""

import os
import sys
from pathlib import Path


def check_directory_structure():
    """检查目录结构"""
    print("=== 检查项目目录结构 ===")

    required_dirs = [
        "src",
        "src/data",
        "src/strategies",
        "src/backtest",
        "src/execution",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "notebooks",
        "scripts",
        "config",
        "docs",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "data/cache",
        "rust",
        "rust/src",
        "rust/python",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✓ {dir_path}")

    if missing_dirs:
        print(f"✗ 缺少目录: {missing_dirs}")
        return False

    return True


def check_required_files():
    """检查必需文件"""
    print("\n=== 检查必需文件 ===")

    required_files = [
        "pyproject.toml",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        "docker/docker-compose.yml",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")

    if missing_files:
        print(f"✗ 缺少文件: {missing_files}")
        return False

    return True


def check_python_modules():
    """检查Python模块"""
    print("\n=== 检查Python模块 ===")

    try:
        # 检查是否可以导入项目模块
        sys.path.insert(0, "src")

        from config import app_settings, config_manager

        print("✓ 配置模块导入成功")

        from utils.logging import get_logger

        logger = get_logger("test")
        print("✓ 日志模块导入成功")

        from utils.helpers import validate_stock_symbol

        print("✓ 工具函数模块导入成功")

        return True

    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False


def check_environment():
    """检查环境变量"""
    print("\n=== 检查环境变量 ===")

    if Path(".env").exists():
        print("✓ .env文件存在")

        # 加载并检查环境变量
        with open(".env", "r") as f:
            env_vars = {}
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value.strip()

        required_vars = ["CLICKHOUSE_HOST", "CLICKHOUSE_USER", "CLICKHOUSE_PASSWORD"]
        missing_vars = []

        for var in required_vars:
            if var in env_vars:
                print(f"✓ {var}")
            else:
                missing_vars.append(var)

        if missing_vars:
            print(f"✗ 缺少环境变量: {missing_vars}")
            return False

        return True
    else:
        print("✗ .env文件不存在")
        return False


def main():
    """主验证函数"""
    print("PulseTrader 项目设置验证\n")

    checks = [
        check_directory_structure,
        check_required_files,
        check_python_modules,
        check_environment,
    ]

    all_passed = True
    for check in checks:
        if not check():
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有检查通过！项目设置完成。")
        return 0
    else:
        print("❌ 部分检查失败，请查看上述错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

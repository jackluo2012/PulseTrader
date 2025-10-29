#!/usr/bin/env python3
"""
MVP环境验证脚本
"""
import sys
import subprocess
import importlib
import os
from pathlib import Path

def check_rust():
    """检查 Rust 环境"""
    try:
        result = subprocess.run(['cargo', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Rust: {result.stdout.strip()}")
            return True
        else:
            print("❌ Rust 未正确安装")
            return False
    except FileNotFoundError:
        print("❌ Rust 未安装")
        return False

def check_python():
    """检查 Python 环境"""
    version = sys.version_info
    if version >= (3, 11):
        print(f"✅ Python: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"⚠️  Python 版本: {version.major}.{version.minor}")
        return True

def check_venv():
    """检查虚拟环境"""
    venv_path = Path('.venv')
    if not venv_path.exists():
        print("❌ 虚拟环境: .venv 目录不存在")
        return False

    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 虚拟环境: 已激活")
        return True
    else:
        print("⚠️  虚拟环境: 未激活")
        return False

def check_packages():
    """检查核心包"""
    required_packages = ['pandas', 'numpy', 'maturin', 'tushare', 'fastapi']

    all_ok = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} 未安装")
            all_ok = False

    return all_ok

def check_project_structure():
    """检查项目结构"""
    required_dirs = ['engine/src', 'pulse_trader', 'data', 'config']

    all_ok = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ {directory}/")
        else:
            print(f"❌ {directory}/ 不存在")
            all_ok = False

    return all_ok

def main():
    """主验证函数"""
    print("🔍 MVP环境验证...")
    print("=" * 40)

    checks = [
        ("Rust 环境", check_rust),
        ("Python 环境", check_python),
        ("虚拟环境", check_venv),
        ("核心包", check_packages),
        ("项目结构", check_project_structure),
    ]

    all_passed = True
    for name, check_func in checks:
        print(f"\n📋 检查 {name}:")
        if not check_func():
            all_passed = False

    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 MVP环境验证通过！")
    else:
        print("⚠️  环境验证失败，请检查上述问题")

if __name__ == "__main__":
    main()

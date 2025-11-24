#!/usr/bin/env python3
"""
完整环境测试脚本
验证所有组件是否正常工作
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """运行命令并检查结果"""
    print(f"\n{'='*50}")
    print(f"测试: {description}")
    print(f"命令: {cmd}")
    print("-" * 50)

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print("✅ 成功")
            if result.stdout.strip():
                print("输出:", result.stdout.strip())
            return True
        else:
            print("❌ 失败")
            if result.stderr.strip():
                print("错误:", result.stderr.strip())
            return False
    except subprocess.TimeoutExpired:
        print("❌ 超时")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


def test_python_environment():
    """测试Python环境"""
    tests = [
        ("python --version", "Python版本"),
        ("pip --version", "pip版本"),
        ("poetry --version", "Poetry版本"),
        ("maturin --version", "Maturin版本"),
    ]

    return all(run_command(cmd, desc) for cmd, desc in tests)


def test_docker_environment():
    """测试Docker环境"""
    tests = [
        ("docker --version", "Docker版本"),
        ("docker-compose --version", "Docker Compose版本"),
    ]

    # 如果Docker测试失败，跳过后续测试
    docker_ok = all(run_command(cmd, desc) for cmd, desc in tests)

    if docker_ok:
        # 测试Docker服务状态
        docker_tests = [
            ("docker ps", "Docker服务状态"),
            ("curl -s http://localhost:8123/ping", "ClickHouse连接"),
        ]
        return all(run_command(cmd, desc) for cmd, desc in docker_tests)

    return False


def test_project_structure():
    """测试项目结构"""
    print(f"\n{'='*50}")
    print("测试: 项目结构")
    print("-" * 50)

    required_paths = [
        "src",
        "src/config",
        "src/data",
        "src/utils",
        "tests",
        "config",
        "docs",
        ".vscode",
        "pyproject.toml",
        "requirements.txt",
        ".env.example",
        "docker/docker-compose.yml",
    ]

    missing_paths = []
    for path in required_paths:
        if Path(path).exists():
            print(f"✅ {path}")
        else:
            print(f"❌ {path}")
            missing_paths.append(path)

    return len(missing_paths) == 0


def test_python_modules():
    """测试Python模块导入"""
    print(f"\n{'='*50}")
    print("测试: Python模块导入")
    print("-" * 50)

    # 添加src到Python路径
    sys.path.insert(0, "src")

    modules_to_test = [
        ("config", "配置模块"),
        ("utils.helpers", "工具函数模块"),
        ("utils.logging", "日志模块"),
        ("utils.datetime_utils", "日期工具模块"),
    ]

    success_count = 0
    for module, desc in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {desc}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {desc}: {e}")

    return success_count == len(modules_to_test)


def test_code_quality_tools():
    """测试代码质量工具"""
    tests = [
        ("black --version", "Black代码格式化工具"),
        ("pylint --version", "Pylint代码检查工具"),
        ("mypy --version", "MyPy类型检查工具"),
        ("isort --version", "isort导入排序工具"),
        ("pytest --version", "pytest测试框架"),
    ]

    return all(run_command(cmd, desc) for cmd, desc in tests)


def test_code_quality():
    """测试代码质量"""
    print(f"\n{'='*50}")
    print("测试: 代码质量检查")
    print("-" * 50)

    # 运行代码格式化检查（不修改文件）
    format_check = run_command("black --check src tests --diff", "Black格式检查")

    # 运行导入排序检查
    import_check = run_command("isort --check-only src tests --diff", "isort导入检查")

    # 运行pylint检查（允许一些警告）
    lint_check = run_command(
        "pylint src --disable=R,C,W --fail-under=8.0", "Pylint代码检查"
    )

    return format_check and import_check and lint_check


def test_unit_tests():
    """运行单元测试"""
    return run_command("python3 -m pytest tests/unit -v", "单元测试")


def main():
    """主测试函数"""
    print("🚀 PulseTrader 完整环境测试开始\n")
    print("这个测试将验证您的开发环境是否完全配置正确。\n")

    test_groups = [
        ("Python环境", test_python_environment),
        ("项目结构", test_project_structure),
        ("Python模块", test_python_modules),
        ("代码质量工具", test_code_quality_tools),
        ("代码质量检查", test_code_quality),
        ("单元测试", test_unit_tests),
        ("Docker环境", test_docker_environment),
    ]

    results = {}
    for group_name, test_func in test_groups:
        print(f"\n🧪 {group_name}")
        results[group_name] = test_func()

    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print("=" * 60)

    all_passed = True
    for group_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{group_name:<20} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 恭喜！所有环境测试都通过了！")
        print("您的PulseTrader开发环境已经准备就绪。")
        print("\n🚀 现在您可以：")
        print("  1. 开始第二章：数据获取与存储")
        print("  2. 运行 'make help' 查看可用命令")
        print("  3. 使用VS Code开始开发")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请查看上述错误信息并修复。")
        print("\n📝 常见解决方案：")
        print("  1. 确保激活虚拟环境: source .venv/bin/activate")
        print("  2. 安装缺失依赖: pip install -r requirements.txt")
        print("  3. 检查Docker服务: docker-compose up -d")
        print("  4. 查看详细错误信息并修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())

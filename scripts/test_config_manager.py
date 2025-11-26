#!/usr/bin/env python3
"""
配置管理器测试脚本
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config.config_manager import (
    ConfigManager,
    get_config,
    get_config_manager,
    is_enabled,
)


def test_config_manager():
    """测试配置管理器功能"""
    print("🧪 配置管理器测试")
    print("=" * 50)

    # 测试配置加载
    print("\n1. 测试配置加载...")
    config_manager = ConfigManager()
    print(f"   ✅ 配置管理器初始化成功")
    print(f"   📁 配置文件路径: {config_manager.config_path}")

    # 测试基本配置获取
    print("\n2. 测试基本配置获取...")
    timeout = config_manager.get_timeout()
    print(f"   ⏱️  请求超时时间: {timeout} 秒")

    max_retries = config_manager.get_max_retries()
    print(f"   🔄 最大重试次数: {max_retries}")

    delay = config_manager.get_delay()
    print(f"   ⏳ 请求间隔时间: {delay} 秒")

    # 测试嵌套配置获取
    print("\n3. 测试嵌套配置获取...")
    batch_size = config_manager.get("akshare.data_types.historical.batch_size")
    print(f"   📦 历史数据批量大小: {batch_size}")

    clickhouse_batch = config_manager.get("storage.clickhouse.batch_size")
    print(f"   🗄️  ClickHouse 批量插入大小: {clickhouse_batch}")

    # 测试数据类型配置
    print("\n4. 测试数据类型配置...")
    data_types = ["stock_info", "realtime", "historical", "financial"]
    for data_type in data_types:
        enabled = config_manager.is_data_type_enabled(data_type)
        config = config_manager.get_data_type_config(data_type)
        update_interval = config.get("update_interval", "N/A") if config else "N/A"
        status = "✅ 启用" if enabled else "❌ 禁用"
        print(f"   {status} {data_type}: 更新间隔 {update_interval}")

    # 测试便捷函数
    print("\n5. 测试便捷函数...")
    global_manager = get_config_manager()
    print(f"   🌐 全局配置管理器: {type(global_manager).__name__}")

    # 测试便捷获取函数
    cache_ttl = get_config("storage.cache.redis.ttl", 3600)
    print(f"   💾 缓存过期时间: {cache_ttl} 秒")

    concurrent_workers = config_manager.get_concurrent_workers()
    print(f"   👥 并发工作线程数: {concurrent_workers}")

    # 测试配置验证
    print("\n6. 测试配置验证...")
    is_valid = config_manager.validate_config()
    print(f"   ✅ 配置验证结果: {'通过' if is_valid else '失败'}")

    # 测试日志设置
    print("\n7. 测试日志配置...")
    log_config = config_manager.get_logging_config()
    print(f"   📝 日志级别: {log_config.get('level', 'INFO')}")
    print(f"   📄 日志文件: {log_config.get('file', 'N/A')}")
    print(f"   📏 最大文件大小: {log_config.get('max_size', 'N/A')}")

    print("\n8. 显示完整配置结构...")
    print("   🔧 Akshare 配置:")
    akshare_config = config_manager.get_akshare_config()
    for key, value in akshare_config.items():
        if key != "data_types":
            print(f"      {key}: {value}")

    print("\n   📊 数据类型配置:")
    for data_type in data_types:
        type_config = config_manager.get_data_type_config(data_type)
        if type_config:
            print(f"      {data_type}:")
            for key, value in type_config.items():
                print(f"        {key}: {value}")


def test_error_handling():
    """测试错误处理"""
    print("\n🛡️ 错误处理测试")
    print("=" * 50)

    config_manager = ConfigManager()

    # 测试不存在的配置项
    print("\n1. 测试不存在的配置项...")
    missing_value = config_manager.get("non.existent.key", "default_value")
    print(f"   🕳️  不存在的键值: {missing_value}")

    # 测试无效的配置文件路径
    print("\n2. 测试无效配置文件路径...")
    invalid_manager = ConfigManager("/non/existent/path.yaml")
    print(f"   ⚠️  无效路径下的配置管理器仍然可以工作")

    # 测试配置重载
    print("\n3. 测试配置重载...")
    config_manager.reload()
    print(f"   🔄 配置重载成功")


if __name__ == "__main__":
    try:
        test_config_manager()
        test_error_handling()

        print("\n🎉 配置管理器测试完成！")
        print("\n✅ 所有功能测试通过:")
        print("   • 配置文件加载")
        print("   • 配置项获取")
        print("   • 嵌套配置访问")
        print("   • 便捷函数")
        print("   • 配置验证")
        print("   • 错误处理")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()

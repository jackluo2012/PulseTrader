#!/usr/bin/env python3
"""
ClickHouse数据库功能测试脚本
验证数据库连接、查询和基础操作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.database import db_manager

def test_basic_operations():
    """测试基础数据库操作"""
    print("=== ClickHouse数据库功能测试 ===")

    # 1. 测试连接
    print("\n1. 测试数据库连接...")
    if db_manager.test_connection():
        print("✓ 数据库连接测试通过")
    else:
        print("✗ 数据库连接测试失败")
        return False

    # 2. 测试股票信息查询
    print("\n2. 测试股票信息查询...")
    try:
        stock_info = db_manager.get_stock_info()
        print(f"✓ 查询到 {len(stock_info)} 只股票")
        if len(stock_info) > 0:
            print("  示例股票信息:")
            print(stock_info.head(2).to_string(index=False))
    except Exception as e:
        print(f"✗ 股票信息查询失败: {e}")
        return False

    print("\n=== 数据库功能测试完成 ===")
    return True

def cleanup():
    """清理资源"""
    print("\n清理数据库连接...")
    try:
        db_manager.close()
        print("✓ 数据库连接已关闭")
    except Exception as e:
        print(f"✗ 清理失败: {e}")

if __name__ == "__main__":
    success = True

    # 执行基础功能测试
    if not test_basic_operations():
        success = False

    # 清理资源
    cleanup()

    if success:
        print("\n🎉 所有测试通过！ClickHouse数据库配置完成。")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查配置。")
        sys.exit(1)

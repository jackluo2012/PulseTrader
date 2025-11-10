#!/usr/bin/env python3
"""
检查 ClickHouse 认证配置
"""

import clickhouse_connect

def test_auth():
    """测试不同的认证配置"""
    print("🔍 检查 ClickHouse 认证配置...")

    # 测试不同的认证组合
    configs = [
        # 尝试无认证
        {'host': 'localhost', 'port': 8123, 'database': 'default'},

        # 尝试 default 用户
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'default'},
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'default', 'password': ''},

        # 尝试常见密码
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'default', 'password': 'clickhouse'},
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'default', 'password': '123456'},

        # 尝试 root 用户
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'root'},
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'root', 'password': ''},
    ]

    for i, config in enumerate(configs, 1):
        print(f"\n{i}. 测试配置: {config}")
        try:
            client = clickhouse_connect.get_client(**config)

            # 测试查询
            result = client.query('SELECT version() as version')
            version = result.result_rows[0][0]
            print(f"   ✅ 连接成功! ClickHouse 版本: {version}")

            # 测试数据库列表
            db_result = client.query('SHOW DATABASES')
            databases = [row[0] for row in db_result.result_rows]
            print(f"   数据库列表: {databases}")

            client.close()
            return config

        except Exception as e:
            print(f"   ❌ 失败: {e}")

    print(f"\n❌ 所有认证配置都失败")
    return None

def main():
    config = test_auth()
    if config:
        print(f"\n✅ 找到可用配置: {config}")
        print("请在 DataCache 初始化时使用这个配置")
    else:
        print("\n❌ 请检查 ClickHouse 认证设置")
        print("可能的解决方案:")
        print("1. 检查 ClickHouse 配置文件中的用户设置")
        print("2. 重置 default 用户密码")
        print("3. 创建新的用户")

if __name__ == "__main__":
    main()
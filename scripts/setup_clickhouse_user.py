#!/usr/bin/env python3
"""
设置 ClickHouse 用户和数据库
"""

import requests
import clickhouse_connect

def setup_clickhouse():
    """设置 ClickHouse 用户和数据库"""
    print("🔧 设置 ClickHouse 用户和数据库...")

    # 步骤1: 尝试不同的认证方式来获取管理员权限
    admin_configs = [
        # 可能的管理员配置
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'default', 'password': ''},
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'default', 'password': 'clickhouse'},
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'clickhouse', 'password': ''},
        {'host': 'localhost', 'port': 8123, 'database': 'default', 'username': 'admin', 'password': ''},
    ]

    admin_client = None
    for config in admin_configs:
        try:
            print(f"尝试管理员配置: {config}")
            admin_client = clickhouse_connect.get_client(**config)
            # 测试是否有权限
            result = admin_client.query('SHOW DATABASES')
            print(f"✅ 管理员连接成功，数据库: {[row[0] for row in result.result_rows]}")
            break
        except Exception as e:
            print(f"❌ 失败: {e}")
            continue

    if not admin_client:
        print("❌ 无法获取管理员权限")
        return False

    try:
        # 步骤2: 创建 devuser 用户
        print("\n创建 devuser 用户...")
        try:
            admin_client.command("""
                CREATE USER IF NOT EXISTS devuser
                IDENTIFIED BY 'devpass'
                SETTINGS default_database = 'pulse_trader'
            """)
            print("✅ devuser 用户创建成功")
        except Exception as e:
            print(f"⚠️ 创建用户警告: {e}")

        # 步骤3: 创建 pulse_trader 数据库
        print("\n创建 pulse_trader 数据库...")
        try:
            admin_client.command('CREATE DATABASE IF NOT EXISTS pulse_trader')
            print("✅ pulse_trader 数据库创建成功")
        except Exception as e:
            print(f"⚠️ 创建数据库警告: {e}")

        # 步骤4: 授予权限
        print("\n授予权限...")
        try:
            admin_client.command("""
                GRANT ALL ON pulse_trader.* TO devuser
            """)
            print("✅ 权限授予成功")
        except Exception as e:
            print(f"⚠️ 授权警告: {e}")

        # 步骤5: 验证新用户
        print("\n验证新用户...")
        try:
            test_client = clickhouse_connect.get_client(
                host='localhost',
                port=8123,
                database='pulse_trader',
                username='devuser',
                password='devpass'
            )

            result = test_client.query('SELECT 1 as test')
            print(f"✅ devuser 验证成功: {result.result_rows[0][0]}")

            test_client.close()
            admin_client.close()
            return True

        except Exception as e:
            print(f"❌ devuser 验证失败: {e}")
            return False

    except Exception as e:
        print(f"❌ 设置过程失败: {e}")
        return False

def main():
    print("🐳 ClickHouse 用户和数据库设置")
    print("="*50)

    if setup_clickhouse():
        print("\n🎉 ClickHouse 设置完成！")
        print("现在可以使用以下配置连接:")
        print("  主机: localhost")
        print("  端口: 8123")
        print("  数据库: pulse_trader")
        print("  用户名: devuser")
        print("  密码: devpass")
        print("\n可以运行测试脚本:")
        print("python scripts/test_clickhouse_connect_fixed.py")
    else:
        print("\n❌ ClickHouse 设置失败")
        print("可能需要手动创建用户:")
        print("1. 连接到 ClickHouse 服务器")
        print("2. 执行: CREATE USER devuser IDENTIFIED BY 'devpass';")
        print("3. 执行: CREATE DATABASE pulse_trader;")
        print("4. 执行: GRANT ALL ON pulse_trader.* TO devuser;")

if __name__ == "__main__":
    main()
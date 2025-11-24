#!/usr/bin/env python3
"""
环境测试脚本
验证所有依赖是否正确安装
"""

def test_imports():
    """测试所有核心库的导入"""
    try:
        import pandas as pd
        print(f"✓ pandas: {pd.__version__}")
    except ImportError as e:
        print(f"✗ pandas导入失败: {e}")

    try:
        import numpy as np
        print(f"✓ numpy: {np.__version__}")
    except ImportError as e:
        print(f"✗ numpy导入失败: {e}")

    try:
        import akshare as ak
        print(f"✓ akshare: {ak.__version__}")
    except ImportError as e:
        print(f"✗ akshare导入失败: {e}")

    try:
        import clickhouse_driver
        print(f"✓ clickhouse_driver: 成功导入")
    except ImportError as e:
        print(f"✗ clickhouse_driver导入失败: {e}")

def test_basic_functionality():
    """测试基础功能"""
    try:
        import pandas as pd
        import numpy as np

        # 测试pandas基础操作
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=5),
            'price': [100.0, 101.5, 99.8, 102.3, 103.1]
        })
        print(f"✓ pandas DataFrame创建成功: {df.shape}")

        # 测试numpy基础操作
        arr = np.array([1, 2, 3, 4, 5])
        print(f"✓ numpy数组操作成功: mean={arr.mean()}")

    except Exception as e:
        print(f"✗ 基础功能测试失败: {e}")

if __name__ == "__main__":
    print("=== 环境测试开始 ===")
    test_imports()
    test_basic_functionality()
    print("=== 环境测试完成 ===")
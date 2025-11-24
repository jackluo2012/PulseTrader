#!/bin/bash
# Python环境激活和测试脚本

# 激活虚拟环境并运行Python命令
# 用法: ./run_python.sh <script_name>

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt 2>/dev/null || {
        echo "⚠️  requirements.txt不存在，安装基础依赖..."
        pip install clickhouse-driver clickhouse-pool redis pandas numpy akshare
    }
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 运行指定脚本或Python命令
if [ $# -eq 0 ]; then
    echo "🔧 Python环境已激活"
    echo "用法: $0 <script_name>"
    echo ""
    echo "可用脚本:"
    echo "  test_clickhouse.py  - 测试ClickHouse连接"
    echo "  其他Python脚本..."
else
    SCRIPT_NAME="$1"
    shift
    python "$SCRIPT_NAME" "$@"
fi
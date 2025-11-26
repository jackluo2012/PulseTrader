#!/bin/bash
# PulseTrader 环境设置脚本
# 设置 locale 和其他环境变量

echo "🔧 设置 PulseTrader 开发环境..."

# 设置 locale 环境变量
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

echo "✅ Locale 设置完成"

# 设置 Git 配置（如果没有设置的话）
if ! git config --global user.name &>/dev/null; then
    echo "⚠️  请设置 Git 用户名和邮箱:"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
fi

# 设置 Python 路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "✅ Python 路径设置完成: $PYTHONPATH"

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p data/cache
mkdir -p data/exports
mkdir -p checkpoints

echo "✅ 目录创建完成"

# 检查依赖
echo "🔍 检查 Python 依赖..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3: $(python3 --version)"
else
    echo "❌ Python3 未安装"
    exit 1
fi

if command -v pip &> /dev/null; then
    echo "✅ Pip: $(pip --version)"
else
    echo "❌ Pip 未安装"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ 虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  建议使用虚拟环境"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
fi

echo ""
echo "🎉 环境设置完成！"
echo ""
echo "📋 下一步:"
echo "   1. 激活虚拟环境: source .venv/bin/activate"
echo "   2. 安装依赖: pip install -r requirements.txt"
echo "   3. 运行测试: python scripts/test_config_manager.py"
echo ""
echo "🔧 要使 locale 设置永久生效，请将以下行添加到 ~/.bashrc:"
echo "   export LANGUAGE=en_US.UTF-8"
echo "   export LC_ALL=en_US.UTF-8"
echo "   export LANG=en_US.UTF-8"

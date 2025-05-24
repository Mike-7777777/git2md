#!/bin/bash

# GitHub仓库内容聚合导出工具启动脚本

echo "🚀 启动 Git2MD 应用..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python3 未安装"
    echo "请先安装 Python 3.7+"
    exit 1
fi

# 检查pip是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: pip3 未安装"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装依赖包..."
pip install -r requirements.txt

# 创建必要的目录
echo "📁 创建目录..."
mkdir -p downloads
mkdir -p logs

# 检查环境变量文件
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "📋 复制环境变量示例文件..."
        cp env.example .env
        echo "⚠️  请编辑 .env 文件设置您的配置"
        echo ""
        echo "🔑 强烈建议配置 GitHub Token 以避免API限制："
        echo "   1. 访问 https://github.com/settings/tokens"
        echo "   2. 创建新的 Token (勾选 public_repo 权限)"
        echo "   3. 在 .env 文件中设置: GITHUB_TOKEN=your_token_here"
        echo ""
    fi
fi

# 检查是否配置了GitHub Token
if [ -f ".env" ] && ! grep -q "^GITHUB_TOKEN=" .env || grep -q "^GITHUB_TOKEN=your_github_token_here" .env; then
    echo "⚠️  警告: 未检测到有效的 GitHub Token 配置"
    echo "   这可能导致API限制错误，建议配置后使用"
    echo ""
fi

# 启动应用
echo "🌟 启动应用..."
echo "应用将在 http://localhost:5000 运行"
echo "按 Ctrl+C 停止应用"
echo ""

python app.py 
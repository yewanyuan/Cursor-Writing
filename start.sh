#!/bin/bash

echo "=== Cursor Writing启动脚本 ==="
echo "修复版本 - 使用正确的目录结构"

# 检查当前目录
if [ ! -f "backend/app/main.py" ]; then
    echo "错误: 请在项目根目录下运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 进入后端应用目录
cd backend/app

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "../venv" ]; then
    echo "创建虚拟环境..."
    cd ..
    python3 -m venv venv
    cd app
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source ../venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install -r ../requirements.txt

# 检查环境变量文件
if [ ! -f "../.env" ]; then
    echo "警告: .env 文件不存在，将使用 .env.example"
    echo "请复制 .env.example 到 .env 并配置您的 OpenAI API Key"
    if [ -f "../.env.example" ]; then
        cp ../.env.example ../.env
    fi
fi

# 停止已有进程
echo "停止现有进程..."
pkill -f "uvicorn.*main:app" || true
sleep 2

# 启动FastAPI服务器
echo "启动FastAPI服务器..."
echo "================================================================"
echo "  前端页面: http://127.0.0.1:8000/static/index.html"
echo "  API文档:  http://127.0.0.1:8000/docs"
echo "  健康检查: http://127.0.0.1:8000/health"
echo "================================================================"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
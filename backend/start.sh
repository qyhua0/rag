#!/bin/bash
# 启动后端服务
# Package: top.modelx.rag | Author: hua

set -e
cd "$(dirname "$0")"

echo "🚀 启动 RAG 后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
  echo "📦 创建虚拟环境..."
  python3 -m venv venv
fi

source venv/bin/activate

# 安装依赖
echo "📥 检查依赖..."
pip install -r requirements.txt -q

# 启动服务
echo "✅ 启动 FastAPI 服务 http://localhost:8000"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info

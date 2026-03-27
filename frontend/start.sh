#!/bin/bash
# 启动前端服务
# Package: top.modelx.rag | Author: hua

set -e
cd "$(dirname "$0")"

echo "🎨 启动 RAG 前端..."

if [ ! -d "node_modules" ]; then
  echo "📥 安装 npm 依赖..."
  npm install
fi

echo "✅ 启动 Vue3 开发服务 http://localhost:3000"
npm run dev

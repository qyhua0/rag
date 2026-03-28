# 🧠 ModelX RAG — 企业内部知识库系统

> Package: `top.modelx.rag` | Author: **hua**

基于 LangChain v0.3 + FastAPI + Ollama + Vue3 构建的企业级 RAG 知识库系统，支持多格式文档解析、向量检索和流式问答。

---


![rag_主界面](images/main.png)

![rag_软件库](images/main2.png)

![rag_文档管理](images/main3.png)

![rag_对话](images/main4.png)


## ✨ 核心特性

| 功能 | 说明 |
|------|------|
| 📄 多格式解析 | PDF / Word / Excel / TXT / 图片（PaddleOCR） |
| 🔍 向量检索 | ChromaDB + Qwen3-Embedding-8B 嵌入 |
| 💬 流式问答 | SSE 流式输出，实时打字效果 |
| 📁 灵活导入 | 支持文件上传 & 本地目录路径扫描 |
| 🗂️ 多知识库 | 独立管理，互不干扰 |
| 🖼️ 图片 OCR | PaddleOCR 中文识别，PDF 图片页自动 OCR |
| 📊 引用溯源 | 每次回答标注文档来源和相似度 |

---

## 🏗️ 技术栈

```
后端
├── FastAPI 0.115          Web 框架
├── LangChain v0.3         RAG 核心
├── langchain-ollama       本地 LLM 接入
├── langchain-chroma       向量存储封装
├── ChromaDB               持久化向量库
├── Ollama                 本地模型运行时
│   ├── qwen2.5:7b         对话模型（可替换）
│   └── qwen3-embedding-8b 嵌入模型
├── PaddleOCR              图片文字识别
├── SQLAlchemy 2.0         ORM
└── MySQL 5.7              业务数据库

前端
├── Vue 3.5                UI 框架
├── Vite 6                 构建工具
├── Tailwind CSS 3         样式框架
├── Pinia                  状态管理
└── marked                 Markdown 渲染


---

## 🚀 快速开始

### 1. 前置准备

```bash
# Python 3.10+
python3 --version

# Node.js 18+
node --version

# MySQL 5.7 已启动
mysql -u root -p -e "SELECT VERSION();"

# Ollama 已安装并运行
ollama serve
```

### 2. 拉取 Ollama 模型

```bash
# 嵌入模型（必须）
ollama pull qwen3-embedding-8b

# 对话模型（按配置选择）
ollama pull qwen2.5:7b
# 或更大模型
# ollama pull qwen2.5:14b
```

### 3. 配置后端环境变量

编辑 `backend/.env`：

```env
# 数据库连接（必改）
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/rag_db

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=qwen3-embedding-8b

# 文件上传目录
UPLOAD_DIR=./uploads

# RAG 分块参数
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K=5
```

### 4. 启动后端

```bash
cd backend
chmod +x start.sh
./start.sh
# 或手动：
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 5. 启动前端

```bash
cd frontend
chmod +x start.sh
./start.sh
# 或手动：
npm install && npm run dev
```

### 6. 访问系统

| 地址 | 说明 |
|------|------|
| http://localhost:3000 | 前端界面 |
| http://localhost:8000/docs | API 文档（Swagger） |
| http://localhost:8000/api/system/health | 健康检查 |

---

## 📖 使用流程

```
1. 新建知识库  →  选择图标、填写名称描述
2. 上传文档    →  支持拖拽上传 / 本地目录导入
3. 等待处理    →  文档自动解析 → 分块 → 向量化（状态实时刷新）
4. 开始对话    →  基于知识库内容问答，自动引用来源
```

---

## 🔧 支持的文件格式

| 格式 | 说明 |
|------|------|
| `.pdf` | 文本直接提取，图片页自动 OCR |
| `.docx` | 段落 + 表格内容提取 |
| `.doc` | 需要 `docx2txt`（或 LibreOffice） |
| `.xlsx` | 多 Sheet 提取 |
| `.xls` | 使用 xlrd 解析 |
| `.txt / .md / .csv` | 自动编码检测 |
| `.jpg / .png / ...` | PaddleOCR 文字识别 |

---

## ⚙️ RAG 参数调优

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CHUNK_SIZE` | 1000 | 每块字符数，越小越精准但上下文少 |
| `CHUNK_OVERLAP` | 200 | 块间重叠字符数，保持上下文连贯 |
| `TOP_K` | 5 | 每次检索返回的最相关块数 |

---

## 🐛 常见问题

**Q: PaddleOCR 安装失败？**
```bash
# 先安装 paddlepaddle CPU 版
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install paddleocr
```

**Q: Ollama 连接失败？**
```bash
# 确保 ollama serve 正在运行
curl http://localhost:11434/api/tags
```

**Q: MySQL 连接报错？**
```bash
# 检查用户权限
mysql -u root -p -e "GRANT ALL ON rag_db.* TO 'root'@'localhost';"
```

**Q: 文档一直是"处理中"状态？**
- 检查后端日志 `logs/app.log`
- 嵌入模型需要第一次调用时初始化，可能较慢

---

## 📝 API 示例

```bash
# 创建知识库
curl -X POST http://localhost:8000/api/kb \
  -H "Content-Type: application/json" \
  -d '{"name":"技术文档","icon":"⚙️","description":"内部技术规范"}'

# 上传文件
curl -X POST http://localhost:8000/api/doc/upload \
  -F "kb_id=1" -F "files=@report.pdf"

# 导入本地目录
curl -X POST http://localhost:8000/api/doc/import-path \
  -H "Content-Type: application/json" \
  -d '{"kb_id":1,"path":"/data/docs","recursive":true}'

# 问答（非流式）
curl -X POST http://localhost:8000/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"kb_id":1,"question":"请介绍一下系统架构"}'
```

---

## 📄 License

MIT License — www.modelx.top © hua

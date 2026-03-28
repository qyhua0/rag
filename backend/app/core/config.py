"""
配置管理模块
Package: top.modelx.rag
Author: hua
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Enterprise RAG System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/rag_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_LLM_MODEL: str = "qwen2.5:7b"
    OLLAMA_EMBEDDING_MODEL: str = "qwen3-embedding-8b"

    # Vector Store
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "rag_documents"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 104857600  # 100MB
    ALLOWED_EXTENSIONS: str = "pdf,doc,docx,txt,xls,xlsx,jpg,jpeg,png,gif,bmp"

    # RAG Config
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 8                        # 向量召回数量
    RERANK_TOP_K: int = 5                 # 重排后保留数量
    RETRIEVAL_SCORE_THRESHOLD: float = 0.1 # 相似度最低阈值（过滤噪声）
    MAX_CONTEXT_LENGTH: int = 6000        # 最大 context 字符数

    # Cache
    QUERY_CACHE_TTL: int = 300            # 查询缓存 TTL（秒）
    QUERY_CACHE_MAX_SIZE: int = 500       # 最大缓存条数
    EMBEDDING_CACHE_MAX_SIZE: int = 2000  # Embedding 缓存最大条数

    # Async Worker
    EMBEDDING_CONCURRENCY: int = 3        # 并发 embedding 数量
    EMBED_BATCH_SIZE: int = 20            # 每批 embedding 文本数

    # Logging
    LOG_DIR: str = "./logs"
    LOG_RETRIEVAL: bool = True            # 开启检索日志
    LOG_PROMPT: bool = True               # 开启 prompt 日志
    LOG_LEVEL: str = "INFO"

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    def ensure_dirs(self):
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
settings.ensure_dirs()
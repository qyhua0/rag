-- 企业知识库系统数据库初始化
-- Package: top.modelx.rag | Author: hua
-- MySQL 5.7

CREATE DATABASE IF NOT EXISTS rag_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE rag_db;

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(200) NOT NULL COMMENT '知识库名称',
  description   TEXT COMMENT '知识库描述',
  icon          VARCHAR(10) DEFAULT '📚' COMMENT '图标',
  status        ENUM('active','inactive') DEFAULT 'active',
  embedding_model VARCHAR(100) DEFAULT 'qwen3-embedding-8b',
  doc_count     INT DEFAULT 0 COMMENT '文档数量',
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  kb_id       INT NOT NULL,
  filename    VARCHAR(500) NOT NULL COMMENT '原始文件名',
  file_path   VARCHAR(1000) COMMENT '存储路径',
  file_type   VARCHAR(50) COMMENT '文件类型',
  file_size   BIGINT DEFAULT 0 COMMENT '文件大小(bytes)',
  status      ENUM('pending','processing','completed','failed') DEFAULT 'pending',
  error_msg   TEXT COMMENT '错误信息',
  chunk_count INT DEFAULT 0,
  char_count  INT DEFAULT 0,
  meta_info   JSON COMMENT '元数据',
  source_type VARCHAR(20) DEFAULT 'upload' COMMENT '来源类型',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  INDEX idx_kb_id (kb_id),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 会话表
CREATE TABLE IF NOT EXISTS conversations (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  kb_id      INT NOT NULL,
  title      VARCHAR(500) DEFAULT '新对话',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
  INDEX idx_kb_id (kb_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  conv_id    INT NOT NULL,
  role       VARCHAR(20) NOT NULL COMMENT 'user/assistant',
  content    TEXT NOT NULL,
  sources    JSON COMMENT '引用来源',
  tokens     INT DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (conv_id) REFERENCES conversations(id) ON DELETE CASCADE,
  INDEX idx_conv_id (conv_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT '✅ 数据库初始化完成' AS message;

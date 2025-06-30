# 变更日志

## [2024-01-XX] - 主要更新

### 新增功能
- ✅ 将embedding模型从OpenAI改为本地nomic-embed-text:latest
- ✅ 重构测试框架，使用pytest组织测试
- ✅ 添加Ollama服务支持
- ✅ 更新向量维度从1536改为768

### 技术变更
- **Embedding模型**: OpenAI text-embedding-ada-002 → nomic-embed-text:latest
- **向量维度**: 1536 → 768
- **依赖服务**: 新增Ollama服务 (localhost:11434)
- **测试框架**: 重构为pytest结构

### 文件变更

#### 新增文件
- `test/__init__.py` - 测试包初始化
- `test/conftest.py` - pytest配置和fixture
- `test/test_milvus_connection.py` - Milvus连接测试
- `test/test_milvus_basic_operations.py` - 基础操作测试
- `test/test_milvus_rag_integration.py` - RAG集成测试
- `test/README.md` - 测试文档
- `pytest.ini` - pytest配置
- `OLLAMA_SETUP.md` - Ollama设置指南
- `test_nomic_embedding.py` - nomic-embed-text测试脚本
- `requirements.txt` - 项目依赖
- `CHANGELOG.md` - 本文件

#### 修改文件
- `db/milvus.py` - 支持nomic-embed-text模型
- `docker-compose.yml` - Milvus服务配置
- `MILVUS_SETUP.md` - 更新设置指南

#### 删除文件
- `test_milvus_connection.py` - 迁移到test目录
- `test_milvus_basic.py` - 迁移到test目录

### 环境要求

#### 必需服务
1. **Milvus**: `http://localhost:19530`
2. **Ollama**: `http://localhost:11434`

#### Python依赖
```bash
pip install pymilvus python-dotenv ollama numpy pytest pytest-cov
```

#### 模型下载
```bash
ollama pull nomic-embed-text:latest
```

### 使用示例

```python
from db.milvus import create_milvus_rag

# 创建RAG实例
rag = create_milvus_rag(
    collection_name="my_tables",
    embedding_model="nomic-embed-text:latest",
    embedding_dimension=768
)

# 插入表结构
table_info = {
    "table_name": "users",
    "description": "用户信息表",
    "columns": [
        {"name": "id", "type": "INT", "comment": "用户ID"},
        {"name": "name", "type": "VARCHAR(100)", "comment": "用户名"}
    ]
}

rag.insert_table_schema(table_info)

# 搜索相似表
results = rag.search_similar_tables("查询用户信息", top_k=5)
```

### 测试运行

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest test/test_milvus_connection.py

# 生成覆盖率报告
pytest --cov=db --cov-report=html
```

### 故障排除

1. **Ollama服务未启动**
   ```bash
   ollama serve
   ```

2. **模型未下载**
   ```bash
   ollama pull nomic-embed-text:latest
   ```

3. **Milvus连接失败**
   ```bash
   docker-compose up -d
   ```

### 性能优化

- nomic-embed-text模型比OpenAI API更快（本地运行）
- 768维向量比1536维向量占用更少存储空间
- 支持GPU加速（如果可用）

### 向后兼容性

⚠️ **破坏性变更**: 此更新包含破坏性变更
- 向量维度从1536改为768
- 需要重新创建Milvus集合
- 需要安装Ollama服务

### 迁移指南

1. 备份现有数据
2. 安装Ollama服务
3. 下载nomic-embed-text模型
4. 重新创建Milvus集合
5. 重新插入表结构数据
6. 运行测试验证功能 
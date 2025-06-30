# Milvus 设置指南

## 1. 启动 Milvus 服务

### 使用 Docker Compose（推荐）

```bash
# 启动 Milvus 服务
docker-compose up -d

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f standalone
```

### 手动启动 Docker 容器

如果你不想使用 Docker Compose，也可以手动启动：

```bash
# 启动 etcd
docker run -d --name milvus-etcd \
  -p 2379:2379 \
  -e ETCD_AUTO_COMPACTION_MODE=revision \
  -e ETCD_AUTO_COMPACTION_RETENTION=1000 \
  -e ETCD_QUOTA_BACKEND_BYTES=4294967296 \
  -e ETCD_SNAPSHOT_COUNT=50000 \
  quay.io/coreos/etcd:v3.5.5

# 启动 MinIO
docker run -d --name milvus-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ACCESS_KEY=minioadmin \
  -e MINIO_SECRET_KEY=minioadmin \
  minio/minio:RELEASE.2023-03-20T20-16-18Z server /data --console-address ":9001"

# 启动 Milvus
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  -e ETCD_ENDPOINTS=milvus-etcd:2379 \
  -e MINIO_ADDRESS=milvus-minio:9000 \
  milvusdb/milvus:v2.3.3 milvus run standalone
```

## 2. 验证连接

运行测试脚本：

```bash
python test_milvus_connection.py
```

如果看到 "🎉 Milvus连接测试成功！" 说明连接正常。

## 3. 使用 Milvus RAG

```python
from db.milvus import create_milvus_rag

# 创建 RAG 实例
rag = create_milvus_rag(
    collection_name="my_tables",
    uri="http://localhost:19530"
)

# 插入表结构信息
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
for result in results:
    print(f"表名: {result['table_info']['table_name']}")
    print(f"相似度: {result['similarity_score']:.3f}")
```

## 4. 故障排除

### 连接失败

1. **检查 Docker 服务状态**：
   ```bash
   docker ps
   ```

2. **检查端口是否开放**：
   ```bash
   netstat -an | grep 19530
   ```

3. **检查防火墙设置**：
   ```bash
   # macOS
   sudo pfctl -s all
   
   # Linux
   sudo iptables -L
   ```

### 服务启动失败

1. **查看详细日志**：
   ```bash
   docker-compose logs standalone
   ```

2. **清理并重新启动**：
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

3. **检查磁盘空间**：
   ```bash
   df -h
   ```

## 5. 环境变量

可以在 `.env` 文件中设置以下环境变量：

```env
# Milvus 服务地址
MILVUS_URI=http://localhost:19530

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Docker 数据目录
DOCKER_VOLUME_DIRECTORY=./volumes
```

## 6. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
``` 
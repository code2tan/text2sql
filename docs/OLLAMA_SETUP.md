# Ollama 设置指南

本指南将帮助你设置Ollama服务以运行nomic-embed-text模型。

## 1. 安装 Ollama

### macOS
```bash
# 使用Homebrew安装
brew install ollama

# 或下载安装包
curl -fsSL https://ollama.ai/install.sh | sh
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows
```bash
# 使用WSL2
curl -fsSL https://ollama.ai/install.sh | sh
```

## 2. 启动 Ollama 服务

```bash
# 启动Ollama服务
ollama serve

# 在后台运行
nohup ollama serve > ollama.log 2>&1 &
```

## 3. 下载 nomic-embed-text 模型

```bash
# 拉取nomic-embed-text模型
ollama pull nomic-embed-text:latest

# 验证模型已下载
ollama list
```

## 4. 测试模型

```bash
# 测试embedding功能
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text:latest",
    "prompt": "这是一个测试文本"
  }'
```

## 5. 安装 Python 依赖

```bash
# 安装ollama Python包
pip install ollama

# 或使用项目依赖
pip install -r requirements.txt
```

## 6. 验证设置

运行测试脚本验证设置：

```bash
# 测试连接
python -c "
from ollama import Client
client = Client(host='http://localhost:11434')
response = client.embeddings(model='nomic-embed-text:latest', prompt='测试文本')
print(f'Embedding维度: {len(response[\"embedding\"])}')
print('✓ Ollama设置成功')
"
```

## 7. 环境变量配置

在 `.env` 文件中添加：

```env
# Ollama服务地址
OLLAMA_HOST=localhost:11434

# 嵌入模型名称
EMBEDDING_MODEL=nomic-embed-text:latest

# 嵌入向量维度
EMBEDDING_DIMENSION=768
```

## 8. 使用示例

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

## 9. 故障排除

### 常见问题

1. **Ollama服务未启动**
   ```bash
   # 检查服务状态
   ps aux | grep ollama
   
   # 启动服务
   ollama serve
   ```

2. **模型未下载**
   ```bash
   # 检查已下载的模型
   ollama list
   
   # 下载模型
   ollama pull nomic-embed-text:latest
   ```

3. **端口被占用**
   ```bash
   # 检查端口使用情况
   lsof -i :11434
   
   # 停止占用端口的进程
   sudo kill -9 <PID>
   ```

4. **内存不足**
   ```bash
   # 检查可用内存
   free -h
   
   # 清理内存
   sudo sync && sudo sysctl -w vm.drop_caches=3
   ```

### 性能优化

1. **GPU加速**（如果可用）
   ```bash
   # 检查GPU支持
   nvidia-smi
   
   # 使用GPU运行
   CUDA_VISIBLE_DEVICES=0 ollama serve
   ```

2. **内存优化**
   ```bash
   # 设置内存限制
   export OLLAMA_HOST=0.0.0.0:11434
   export OLLAMA_ORIGINS=*
   ```

3. **网络优化**
   ```bash
   # 使用本地网络
   export OLLAMA_HOST=127.0.0.1:11434
   ```

## 10. 监控和日志

### 查看日志
```bash
# 查看Ollama日志
tail -f ~/.ollama/logs/ollama.log

# 查看系统日志
journalctl -u ollama -f
```

### 性能监控
```bash
# 监控CPU和内存使用
htop

# 监控网络连接
netstat -an | grep 11434
```

## 11. 安全配置

### 防火墙设置
```bash
# 只允许本地访问
sudo ufw allow from 127.0.0.1 to any port 11434

# 或完全禁用外部访问
sudo ufw deny 11434
```

### 认证设置
```bash
# 设置访问令牌
export OLLAMA_API_KEY=your_secret_key
```

## 12. 备份和恢复

### 备份模型
```bash
# 导出模型
ollama export nomic-embed-text:latest > nomic-embed-text.tar

# 备份配置
cp -r ~/.ollama ~/.ollama_backup
```

### 恢复模型
```bash
# 导入模型
ollama import nomic-embed-text.tar

# 恢复配置
cp -r ~/.ollama_backup ~/.ollama
``` 
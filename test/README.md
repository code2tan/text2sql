# 测试目录

本目录包含项目的所有测试文件，使用pytest框架组织。

## 目录结构

```
test/
├── __init__.py              # 测试包初始化文件
├── conftest.py              # pytest配置和共享fixture
├── test_milvus_connection.py        # Milvus连接测试
├── test_milvus_basic_operations.py  # Milvus基础操作测试
├── test_milvus_rag_integration.py   # Milvus RAG集成测试
└── README.md                # 本文件
```

## 测试分类

### 1. 连接测试 (`test_milvus_connection.py`)
- **目的**: 验证Milvus服务连接是否正常
- **范围**: 客户端创建、集合创建、健康检查
- **标记**: 单元测试
- **依赖**: 需要Milvus服务运行

### 2. 基础操作测试 (`test_milvus_basic_operations.py`)
- **目的**: 测试Milvus的基础CRUD操作
- **范围**: 插入、查询、搜索、数据验证
- **标记**: 单元测试
- **依赖**: 需要Milvus服务运行

### 3. RAG集成测试 (`test_milvus_rag_integration.py`)
- **目的**: 测试完整的RAG功能
- **范围**: 向量嵌入、相似性搜索、批量操作
- **标记**: 集成测试
- **依赖**: 需要Milvus服务和OpenAI API Key

## 运行测试

### 安装依赖
```bash
pip install pytest pytest-cov
```

### 运行所有测试
```bash
pytest
```

### 运行特定测试
```bash
# 只运行连接测试
pytest test/test_milvus_connection.py

# 只运行基础操作测试
pytest test/test_milvus_basic_operations.py

# 运行特定测试类
pytest test/test_milvus_connection.py::TestMilvusConnection

# 运行特定测试方法
pytest test/test_milvus_connection.py::TestMilvusConnection::test_milvus_client_creation
```

### 运行带标记的测试
```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 跳过慢速测试
pytest -m "not slow"
```

### 生成覆盖率报告
```bash
pytest --cov=db --cov-report=html
```

## 测试环境要求

### 必需服务
1. **Milvus服务**: 运行在 `http://localhost:19530`
2. **Docker**: 用于启动Milvus服务

### 可选服务
1. **OpenAI API**: 用于RAG功能测试
   - 设置环境变量: `OPENAI_API_KEY=your_api_key`

### 启动Milvus服务
```bash
# 使用Docker Compose
docker-compose up -d

# 或手动启动
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -p 9091:9091 \
  milvusdb/milvus:v2.3.3 milvus run standalone
```

## 测试数据

测试使用以下示例数据：

### 表结构数据
- `users`: 用户信息表
- `orders`: 订单表  
- `products`: 产品表

### 向量数据
- 维度: 1536 (OpenAI text-embedding-ada-002)
- 类型: 浮点数列表

## 故障排除

### 常见问题

1. **Milvus连接失败**
   ```bash
   # 检查服务状态
   docker ps | grep milvus
   
   # 查看日志
   docker logs milvus-standalone
   ```

2. **OpenAI API错误**
   ```bash
   # 检查API Key
   echo $OPENAI_API_KEY
   
   # 设置API Key
   export OPENAI_API_KEY=your_api_key
   ```

3. **测试超时**
   ```bash
   # 增加超时时间
   pytest --timeout=300
   ```

### 调试测试
```bash
# 详细输出
pytest -v -s

# 只运行失败的测试
pytest --lf

# 在第一个失败处停止
pytest -x
```

## 添加新测试

### 1. 创建测试文件
```python
# test/test_new_feature.py
import pytest
from db.milvus import MilvusRAG

class TestNewFeature:
    def test_new_functionality(self, milvus_rag):
        # 测试代码
        pass
```

### 2. 使用现有fixture
- `milvus_rag`: Milvus RAG实例
- `sample_table_data`: 示例表数据
- `random_embedding`: 随机向量

### 3. 添加标记
```python
@pytest.mark.integration
def test_integration_feature(self):
    pass

@pytest.mark.slow
def test_slow_feature(self):
    pass
```

## 持续集成

测试可以集成到CI/CD流程中：

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      milvus:
        image: milvusdb/milvus:v2.3.3
        ports:
          - 19530:19530
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest
``` 
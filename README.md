# Text-to-SQL 工作流系统

基于 PocketFlow 框架的智能 Text-to-SQL 转换系统，使用本地 Ollama LLM + MySQL + Milvus RAG 技术栈。

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](https://github.com/your-repo/text2sql)

## 🚀 功能特性

- 🤖 **智能SQL生成**: 使用本地 Ollama LLM 将自然语言转换为 MySQL SQL
- 🔍 **RAG检索系统**: 基于 Milvus Lite 的表结构信息检索
- 🔄 **循环调试**: 自动检测和修复 SQL 错误
- ✅ **语法验证**: 全面的 SQL 语法和逻辑验证
- 📊 **结果展示**: 格式化的查询结果输出
- 🧪 **完整测试**: 包含单元测试和集成测试
- 🐳 **Docker支持**: 一键启动 Milvus 服务

## 🏗️ 系统架构

```
用户查询 → RAG检索表信息 → 生成SQL → 验证SQL → 执行SQL → 返回结果
                ↓              ↓         ↓
            向量数据库       Ollama      MySQL验证
            (Milvus Lite)     LLM       (SQLAlchemy)
```

## 📋 环境要求

- Python 3.12+
- Docker (用于运行 Milvus)
- Ollama (本地 LLM 服务)

## 🛠️ 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/text2sql.git
cd text2sql
```

### 2. 安装 Python 依赖

```bash
# 使用 uv (推荐)
uv sync
```

### 3. 启动 Milvus 服务

```bash
docker-compose up -d
```

### 4. 安装 Ollama 和模型

```bash
# 安装 Ollama (macOS)
curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve

# 下载所需模型
ollama pull nomic-embed-text:latest
ollama pull deepseek-coder:latest
```

### 5. 环境配置

创建 `.env` 文件并配置以下环境变量：

```bash
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password

# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Ollama配置
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
```

## 🚀 使用方法

### 1. 交互式查询

```bash
python main.py
```

启动后可以输入自然语言查询，例如：
- "查询所有用户的信息"
- "统计每个用户的订单数量"
- "查找订单金额大于100的用户"

### 2. 演示模式

```bash
python main.py demo
```

运行预设的演示查询，展示系统功能。

### 3. 编程接口

```python
from main import run_text_to_sql_query

# 数据库配置
database_config = {
    "host": "localhost",
    "port": 3306,
    "database": "test_db",
    "user": "root",
    "password": "password"
}

# 运行查询
result = run_text_to_sql_query(
    user_query="查询所有用户信息",
    database_config=database_config,
    use_debug=True
)

print(f"查询成功: {result['success']}")
print(f"生成的SQL: {result['sql']}")
print(f"查询结果: {result['result']}")
```

## 📁 项目结构

```
text2sql/
├── main.py                 # 主程序入口
├── flow.py                 # 工作流定义
├── nodes.py                # 节点定义
├── utils/                  # 工具函数
│   ├── call_llm.py        # LLM调用接口
│   └── sql_validator.py   # SQL验证器
├── db/                     # 数据库相关
│   ├── milvus.py          # Milvus向量数据库
│   └── mysql_connector.py # MySQL连接器
├── test/                   # 测试文件
│   ├── test_system.py     # 系统集成测试
│   ├── test_milvus_*.py   # Milvus相关测试
│   └── conftest.py        # pytest配置
├── docs/                   # 文档
│   ├── design.md          # 系统设计文档
│   ├── MILVUS_SETUP.md    # Milvus设置指南
│   └── OLLAMA_SETUP.md    # Ollama设置指南
├── docker-compose.yml      # Docker配置
├── pyproject.toml         # 项目配置
└── README.md              # 项目说明
```

## 🔧 核心组件

### 1. 工具函数 (utils/)

- **`call_llm.py`**: Ollama LLM 调用接口
- **`sql_validator.py`**: SQL 语法和逻辑验证器

### 2. 数据库模块 (db/)

- **`mysql_connector.py`**: MySQL 数据库连接和操作
- **`milvus.py`**: Milvus Lite 向量数据库 RAG 系统

### 3. 节点定义 (nodes.py)

- **`RAGRetrievalNode`**: RAG 检索相关表结构信息
- **`SQLGenerationNode`**: 生成 SQL 语句
- **`SQLValidationNode`**: 验证 SQL 语法和逻辑
- **`SQLDebugNode`**: 调试和修复 SQL 错误
- **`SQLExecutionNode`**: 执行 SQL 并返回结果

### 4. 流程定义 (flow.py)

- **`create_text_to_sql_flow()`**: 完整工作流（包含调试）
- **`create_simple_text_to_sql_flow()`**: 简化工作流（无调试）
- **`create_debug_text_to_sql_flow()`**: 调试工作流

## 🔄 工作流程

1. **RAG检索**: 根据用户查询检索相关的表结构信息
2. **SQL生成**: 使用 LLM 生成初始 SQL 语句
3. **SQL验证**: 验证 SQL 语法、表名、字段名等
4. **循环调试**: 如果验证失败，自动进入调试模式修复错误
5. **SQL执行**: 执行验证通过的 SQL 并返回结果

## 🐛 调试机制

系统支持最多3次自动调试循环：

1. **错误分析**: 分析 SQL 验证错误
2. **修复建议**: 基于表结构信息生成修复建议
3. **重新生成**: 使用修复建议重新生成 SQL
4. **强制执行**: 达到最大调试次数后强制执行最后一次修复

## 📊 示例输出

```
用户查询: 查询所有用户的信息
执行状态: 成功
生成的SQL: SELECT * FROM users LIMIT 100

查询结果:
id | name | email
-----------------
1  | 张三 | zhangsan@example.com
2  | 李四 | lisi@example.com
3  | 王五 | wangwu@example.com
```

## 🧪 测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试

```bash
# 运行系统集成测试
pytest test/test_system.py

# 运行Milvus相关测试
pytest test/test_milvus_*.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 测试覆盖率

```bash
# 查看覆盖率报告
open htmlcov/index.html
```

## ⚡ 性能优化

- **本地LLM**: 使用 Ollama 本地模型，无需网络请求
- **向量缓存**: Milvus Lite 缓存表结构向量
- **连接池**: MySQL 连接复用
- **重试机制**: LLM 调用失败自动重试
- **结果限制**: 查询结果自动限制显示行数

## 🔧 扩展功能

### 1. 自定义提示词

可以修改 `nodes.py` 中的提示词模板来优化 SQL 生成效果。

### 2. 支持更多数据库

通过修改 `db/mysql_connector.py` 可以支持 PostgreSQL、SQLite 等其他数据库。

### 3. 添加更多验证规则

在 `utils/sql_validator.py` 中添加自定义的 SQL 验证规则。

### 4. 集成其他 LLM

修改 `utils/call_llm.py` 可以集成其他 LLM 服务。

## 🚨 故障排除

### 1. 数据库连接失败

- 检查 MySQL 服务是否启动
- 验证数据库配置信息
- 确认用户权限

### 2. Ollama 服务问题

```bash
# 检查 Ollama 服务状态
ollama list

# 重启 Ollama 服务
ollama serve
```

### 3. Milvus 连接失败

```bash
# 检查 Docker 容器状态
docker-compose ps

# 重启 Milvus 服务
docker-compose restart
```

### 4. 模型下载问题

```bash
# 检查模型是否已下载
ollama list

# 重新下载模型
ollama pull nomic-embed-text:latest
ollama pull deepseek-coder:latest
```

## 📈 开发计划

- [ ] 支持更多数据库类型 (PostgreSQL, SQLite)
- [ ] 添加 Web 界面
- [ ] 支持复杂查询优化
- [ ] 添加查询历史记录
- [ ] 支持多语言查询

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发环境设置

```bash
# 安装开发依赖
uv sync --dev

# 运行代码格式化
black .
isort .

# 运行类型检查
mypy .

# 运行测试
pytest
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目主页: [https://github.com/your-repo/text2sql](https://github.com/your-repo/text2sql)
- 问题反馈: [Issues](https://github.com/your-repo/text2sql/issues)
- 讨论区: [Discussions](https://github.com/your-repo/text2sql/discussions)

## 🙏 致谢

- [PocketFlow](https://github.com/the-pocket/PocketFlow) - 轻量级 LLM 框架
- [Milvus](https://milvus.io/) - 向量数据库
- [Ollama](https://ollama.ai/) - 本地 LLM 服务
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL 工具包

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！

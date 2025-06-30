# Text-to-SQL 工作流系统

基于 PocketFlow 框架的智能 Text-to-SQL 转换系统，使用 DeepSeek LLM + MySQL + Milvus Lite RAG 技术栈。

## 功能特性

- 🤖 **智能SQL生成**: 使用 DeepSeek LLM 将自然语言转换为 MySQL SQL
- 🔍 **RAG检索系统**: 基于 Milvus Lite 的表结构信息检索
- 🔄 **循环调试**: 自动检测和修复 SQL 错误
- ✅ **语法验证**: 全面的 SQL 语法和逻辑验证
- 📊 **结果展示**: 格式化的查询结果输出

## 系统架构

```
用户查询 → RAG检索表信息 → 生成SQL → 验证SQL → 执行SQL → 返回结果
                ↓              ↓         ↓
            向量数据库       DeepSeek    MySQL验证
            (Milvus Lite)     LLM       (SQLAlchemy)
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

创建 `.env` 文件并配置以下环境变量：

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# OpenAI API配置（用于向量嵌入）
OPENAI_API_KEY=your_openai_api_key_here

# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=your_database_name
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
```

## 使用方法

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

## 核心组件

### 1. 工具函数 (utils/)

- **`call_llm.py`**: DeepSeek LLM 调用接口
- **`mysql_connector.py`**: MySQL 数据库连接和操作
- **`milvus_lite.py`**: Milvus Lite 向量数据库 RAG 系统
- **`sql_validator.py`**: SQL 语法和逻辑验证器

### 2. 节点定义 (nodes.py)

- **`RAGRetrievalNode`**: RAG 检索相关表结构信息
- **`SQLGenerationNode`**: 生成 SQL 语句
- **`SQLValidationNode`**: 验证 SQL 语法和逻辑
- **`SQLDebugNode`**: 调试和修复 SQL 错误
- **`SQLExecutionNode`**: 执行 SQL 并返回结果

### 3. 流程定义 (flow.py)

- **`create_text_to_sql_flow()`**: 完整工作流（包含调试）
- **`create_simple_text_to_sql_flow()`**: 简化工作流（无调试）
- **`create_debug_text_to_sql_flow()`**: 调试工作流

## 工作流程

1. **RAG检索**: 根据用户查询检索相关的表结构信息
2. **SQL生成**: 使用 LLM 生成初始 SQL 语句
3. **SQL验证**: 验证 SQL 语法、表名、字段名等
4. **循环调试**: 如果验证失败，自动进入调试模式修复错误
5. **SQL执行**: 执行验证通过的 SQL 并返回结果

## 调试机制

系统支持最多3次自动调试循环：

1. **错误分析**: 分析 SQL 验证错误
2. **修复建议**: 基于表结构信息生成修复建议
3. **重新生成**: 使用修复建议重新生成 SQL
4. **强制执行**: 达到最大调试次数后强制执行最后一次修复

## 示例输出

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

## 错误处理

系统提供详细的错误信息和调试历史：

```
执行状态: 失败
错误信息:
- 表 'orders' 不存在
- 可能的表名: user_orders, order_items

调试历史:
第1次调试:
  SQL: SELECT * FROM orders
  错误: 表 'orders' 不存在
  修复: SELECT * FROM user_orders
```

## 性能优化

- **向量缓存**: Milvus Lite 缓存表结构向量
- **连接池**: MySQL 连接复用
- **重试机制**: LLM 调用失败自动重试
- **结果限制**: 查询结果自动限制显示行数

## 扩展功能

### 1. 自定义提示词

可以修改 `nodes.py` 中的提示词模板来优化 SQL 生成效果。

### 2. 支持更多数据库

通过修改 `mysql_connector.py` 可以支持 PostgreSQL、SQLite 等其他数据库。

### 3. 添加更多验证规则

在 `sql_validator.py` 中添加自定义的 SQL 验证规则。

### 4. 集成其他 LLM

修改 `call_llm.py` 可以集成其他 LLM 服务。

## 故障排除

### 1. 数据库连接失败

- 检查 MySQL 服务是否启动
- 验证数据库配置信息
- 确认用户权限

### 2. API 调用失败

- 检查 API 密钥是否正确
- 确认网络连接正常
- 查看 API 配额是否充足

### 3. RAG 系统问题

- 检查 Milvus Lite 安装
- 确认 OpenAI API 密钥配置
- 重新初始化数据库 schema

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue 或联系开发者。

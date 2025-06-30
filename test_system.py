#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text-to-SQL 系统测试脚本
用于验证各个组件的功能
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_llm():
    """测试LLM调用"""
    print("测试 DeepSeek LLM 调用...")
    try:
        from utils.call_llm import call_llm
        response = call_llm("请生成一个简单的SQL查询来获取用户表中的所有记录")
        print(f"✓ LLM调用成功: {response[:100]}...")
        return True
    except Exception as e:
        print(f"✗ LLM调用失败: {e}")
        return False

def test_mysql_connector():
    """测试MySQL连接器"""
    print("测试 MySQL 连接器...")
    try:
        from utils.mysql_connector import create_mysql_connector
        
        config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "database": os.getenv("MYSQL_DATABASE", "test_db"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "password")
        }
        
        connector = create_mysql_connector(config)
        schema = connector.get_table_schema()
        print(f"✓ MySQL连接成功，找到 {len(schema)} 个表")
        connector.close()
        return True
    except Exception as e:
        print(f"✗ MySQL连接失败: {e}")
        return False

def test_milvus_rag():
    """测试Milvus RAG系统"""
    print("测试 Milvus RAG 系统...")
    try:
        from db.milvus import create_milvus_rag
        
        rag = create_milvus_rag()
        
        # 测试数据
        test_schema = {
            "test_users": {
                "table_name": "test_users",
                "description": "测试用户表",
                "columns": [
                    {"name": "id", "type": "INT", "comment": "用户ID"},
                    {"name": "name", "type": "VARCHAR(100)", "comment": "用户名"}
                ]
            }
        }
        
        # 插入测试数据
        success = rag.batch_insert_schemas(test_schema)
        if success:
            print("✓ Milvus RAG 系统测试成功")
            return True
        else:
            print("✗ Milvus RAG 数据插入失败")
            return False
            
    except Exception as e:
        print(f"✗ Milvus RAG 系统测试失败: {e}")
        return False

def test_sql_validator():
    """测试SQL验证器"""
    print("测试 SQL 验证器...")
    try:
        from utils.mysql_connector import create_mysql_connector
        from utils.sql_validator import create_sql_validator
        
        config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "database": os.getenv("MYSQL_DATABASE", "test_db"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "password")
        }
        
        connector = create_mysql_connector(config)
        validator = create_sql_validator(connector)
        
        # 测试SQL验证
        test_sql = "SELECT * FROM users LIMIT 10"
        result = validator.validate_sql(test_sql)
        
        print(f"✓ SQL验证器测试成功，验证结果: {result['is_valid']}")
        connector.close()
        return True
        
    except Exception as e:
        print(f"✗ SQL验证器测试失败: {e}")
        return False

def test_nodes():
    """测试节点定义"""
    print("测试节点定义...")
    try:
        from nodes import (
            RAGRetrievalNode, 
            SQLGenerationNode, 
            SQLValidationNode, 
            SQLDebugNode, 
            SQLExecutionNode
        )
        
        # 创建节点实例
        rag_node = RAGRetrievalNode()
        generate_node = SQLGenerationNode()
        validate_node = SQLValidationNode()
        debug_node = SQLDebugNode()
        execute_node = SQLExecutionNode()
        
        print("✓ 所有节点定义正确")
        return True
        
    except Exception as e:
        print(f"✗ 节点定义测试失败: {e}")
        return False

def test_flow():
    """测试流程定义"""
    print("测试流程定义...")
    try:
        from flow import create_text_to_sql_flow, create_simple_text_to_sql_flow
        
        # 创建流程
        flow1 = create_text_to_sql_flow()
        flow2 = create_simple_text_to_sql_flow()
        
        print("✓ 流程定义测试成功")
        return True
        
    except Exception as e:
        print(f"✗ 流程定义测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("测试集成功能...")
    try:
        from main import run_text_to_sql_query
        
        database_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "database": os.getenv("MYSQL_DATABASE", "test_db"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", "password")
        }
        
        # 测试简单查询
        result = run_text_to_sql_query(
            user_query="查询所有用户信息",
            database_config=database_config,
            use_debug=False  # 使用简化模式
        )
        
        print(f"✓ 集成测试成功，查询状态: {result['success']}")
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Text-to-SQL 系统测试")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("✗ 缺少 DEEPSEEK_API_KEY 环境变量")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("✗ 缺少 OPENAI_API_KEY 环境变量")
        return
    
    # 运行测试
    tests = [
        ("LLM调用", test_llm),
        ("MySQL连接器", test_mysql_connector),
        ("Milvus RAG", test_milvus_rag),
        ("SQL验证器", test_sql_validator),
        ("节点定义", test_nodes),
        ("流程定义", test_flow),
        ("集成功能", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
        print()
    
    # 输出测试结果
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统可以正常使用。")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")

if __name__ == "__main__":
    main() 
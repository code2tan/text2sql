#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text-to-SQL 工作流主程序
使用DeepSeek LLM + MySQL + Milvus Lite RAG系统
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from flow import create_text_to_sql_flow, create_simple_text_to_sql_flow
from utils.mysql_connector import create_mysql_connector
from utils.milvus_lite import create_milvus_rag

# 加载环境变量
load_dotenv()

def initialize_database_schema(database_config: Dict[str, Any]) -> bool:
    """
    初始化数据库schema到RAG系统
    
    Args:
        database_config: 数据库配置
        
    Returns:
        是否初始化成功
    """
    try:
        print("正在初始化数据库schema到RAG系统...")
        
        # 连接数据库获取schema
        mysql_connector = create_mysql_connector(database_config)
        schemas = mysql_connector.get_table_schema()
        mysql_connector.close()
        
        if not schemas:
            print("警告: 数据库中没有找到任何表")
            return False
        
        # 初始化RAG系统
        rag = create_milvus_rag()
        
        # 批量插入schema信息
        success = rag.batch_insert_schemas(schemas)
        
        if success:
            print(f"成功初始化 {len(schemas)} 个表的schema信息")
        else:
            print("部分表schema初始化失败")
        
        return success
        
    except Exception as e:
        print(f"初始化数据库schema失败: {e}")
        return False

def run_text_to_sql_query(user_query: str, database_config: Dict[str, Any], use_debug: bool = True) -> Dict[str, Any]:
    """
    运行Text-to-SQL查询
    
    Args:
        user_query: 用户自然语言查询
        database_config: 数据库配置
        use_debug: 是否使用调试模式
        
    Returns:
        查询结果字典
    """
    try:
        # 创建共享存储
        shared = {
            "user_query": user_query,
            "database_config": database_config,
            "rag_context": {},
            "sql_generation": {},
            "debug_history": []
        }
        
        # 选择流程
        if use_debug:
            from flow import create_debug_text_to_sql_flow
            flow = create_debug_text_to_sql_flow()
        else:
            flow = create_simple_text_to_sql_flow()
        
        print(f"开始处理查询: {user_query}")
        print("=" * 50)
        
        # 运行流程
        flow.run(shared)
        
        # 整理结果
        result = {
            "user_query": user_query,
            "success": False,
            "sql": "",
            "result": None,
            "errors": [],
            "debug_history": shared.get("debug_history", [])
        }
        
        # 检查执行结果
        execution_result = shared.get("sql_generation", {}).get("execution_result")
        if execution_result and execution_result.get("success"):
            result["success"] = True
            result["sql"] = execution_result.get("sql", "")
            result["result"] = execution_result.get("result")
        else:
            result["errors"] = shared.get("sql_generation", {}).get("validation_errors", [])
            if execution_result:
                result["errors"].append(execution_result.get("error", "执行失败"))
        
        return result
        
    except Exception as e:
        print(f"运行Text-to-SQL查询失败: {e}")
        return {
            "user_query": user_query,
            "success": False,
            "sql": "",
            "result": None,
            "errors": [str(e)],
            "debug_history": []
        }

def print_result(result: Dict[str, Any]):
    """打印查询结果"""
    print("\n" + "=" * 50)
    print("查询结果:")
    print(f"用户查询: {result['user_query']}")
    print(f"执行状态: {'成功' if result['success'] else '失败'}")
    
    if result['sql']:
        print(f"生成的SQL: {result['sql']}")
    
    if result['success'] and result['result']:
        print("\n查询结果:")
        if isinstance(result['result'], dict):
            if 'columns' in result['result'] and 'rows' in result['result']:
                # 格式化表格输出
                columns = result['result']['columns']
                rows = result['result']['rows']
                
                # 打印表头
                header = " | ".join(str(col) for col in columns)
                print(header)
                print("-" * len(header))
                
                # 打印数据行
                for row in rows[:10]:  # 只显示前10行
                    print(" | ".join(str(cell) for cell in row))
                
                if len(rows) > 10:
                    print(f"... 还有 {len(rows) - 10} 行数据")
            else:
                print(json.dumps(result['result'], indent=2, ensure_ascii=False))
        else:
            print(result['result'])
    
    if result['errors']:
        print(f"\n错误信息:")
        for error in result['errors']:
            print(f"- {error}")
    
    if result['debug_history']:
        print(f"\n调试历史:")
        for i, history in enumerate(result['debug_history'], 1):
            print(f"第{i}次调试:")
            print(f"  SQL: {history['sql']}")
            print(f"  错误: {history['error']}")
            print(f"  修复: {history['fix_suggestion']}")
            print()

def main():
    """主函数"""
    print("Text-to-SQL 工作流系统")
    print("使用 DeepSeek LLM + MySQL + Milvus Lite RAG")
    print("=" * 50)
    
    # 数据库配置
    database_config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "test_db"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "password")
    }
    
    # 检查环境变量
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("错误: 请设置 DEEPSEEK_API_KEY 环境变量")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("错误: 请设置 OPENAI_API_KEY 环境变量（用于向量嵌入）")
        return
    
    # 初始化数据库schema
    print("正在检查数据库连接...")
    try:
        mysql_connector = create_mysql_connector(database_config)
        mysql_connector.close()
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return
    
    # 初始化RAG系统
    if not initialize_database_schema(database_config):
        print("警告: RAG系统初始化失败，将使用备用方案")
    
    # 交互式查询
    while True:
        print("\n" + "-" * 50)
        user_query = input("请输入您的查询需求（输入 'quit' 退出）: ").strip()
        
        if user_query.lower() in ['quit', 'exit', '退出']:
            print("再见!")
            break
        
        if not user_query:
            print("请输入有效的查询需求")
            continue
        
        # 运行查询
        result = run_text_to_sql_query(user_query, database_config, use_debug=True)
        
        # 打印结果
        print_result(result)

def demo():
    """演示函数"""
    print("Text-to-SQL 工作流演示")
    print("=" * 50)
    
    # 数据库配置
    database_config = {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "test_db"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "password")
    }
    
    # 演示查询
    demo_queries = [
        "查询所有用户的信息",
        "统计每个用户的订单数量",
        "查找订单金额大于100的用户",
        "获取最近10个订单的详细信息"
    ]
    
    for query in demo_queries:
        print(f"\n演示查询: {query}")
        result = run_text_to_sql_query(query, database_config, use_debug=True)
        print_result(result)
        input("按回车键继续下一个演示...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main()

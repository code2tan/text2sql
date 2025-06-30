from pocketflow import Node

from db.milvus import create_milvus_rag
from db.mysql_connector import create_mysql_connector
from utils.call_llm import call_llm
from utils.sql_validator import create_sql_validator


class GetQuestionNode(Node):
    def exec(self, _):
        # Get question directly from user input
        user_question = input("Enter your question: ")
        return user_question
    
    def post(self, shared, prep_res, exec_res):
        # Store the user's question
        shared["question"] = exec_res
        return "default"  # Go to the next node

class AnswerNode(Node):
    def prep(self, shared):
        # Read question from shared
        return shared["question"]
    
    def exec(self, question):
        # Call LLM to get the answer
        return call_llm(question)
    
    def post(self, shared, prep_res, exec_res):
        # Store the answer in shared
        shared["answer"] = exec_res

class RAGRetrievalNode(Node):
    """RAG检索节点 - 检索相关的表结构信息"""
    
    def prep(self, shared):
        """读取用户查询和数据库配置"""
        user_query = shared.get("user_query", "")
        database_config = shared.get("database_config", {})
        return user_query, database_config
    
    def exec(self, inputs):
        """调用Milvus Lite检索相关表信息"""
        user_query, database_config = inputs
        
        try:
            # 创建RAG系统
            rag = create_milvus_rag()
            
            # 搜索相似的表信息
            similar_tables = rag.search_similar_tables(user_query, top_k=5)
            
            # 如果没有找到相关表，尝试从数据库获取所有表信息
            if not similar_tables:
                print("RAG检索未找到相关表，尝试获取所有表信息")
                mysql_connector = create_mysql_connector(database_config)
                all_schemas = mysql_connector.get_table_schema()
                mysql_connector.close()
                
                # 将表信息转换为RAG格式
                similar_tables = []
                for table_name, table_info in all_schemas.items():
                    similar_tables.append({
                        "table_info": table_info,
                        "similarity_score": 0.5,  # 默认相似度
                        "description": f"表 {table_name}"
                    })
            
            return similar_tables
            
        except Exception as e:
            print(f"RAG检索失败: {e}")
            return []
    
    def post(self, shared, prep_res, exec_res):
        """将检索结果写入shared"""
        shared["rag_context"] = {
            "table_info": [item["table_info"] for item in exec_res],
            "similarity_scores": [item["similarity_score"] for item in exec_res],
            "descriptions": [item["description"] for item in exec_res]
        }
        return "default"

class SQLGenerationNode(Node):
    """SQL生成节点 - 根据用户查询和RAG上下文生成SQL"""
    
    def prep(self, shared):
        """读取用户查询和RAG上下文"""
        user_query = shared.get("user_query", "")
        rag_context = shared.get("rag_context", {})
        return user_query, rag_context
    
    def exec(self, inputs):
        """调用LLM生成SQL语句"""
        user_query, rag_context = inputs
        
        # 构建表结构信息文本
        table_info_text = ""
        for i, table_info in enumerate(rag_context.get("table_info", [])):
            table_name = table_info["table_name"]
            columns = table_info["columns"]
            description = table_info.get("description", "")
            
            table_info_text += f"\n表名: {table_name}\n"
            table_info_text += f"描述: {description}\n"
            table_info_text += "字段:\n"
            
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                col_comment = col.get("comment", "")
                table_info_text += f"  - {col_name} ({col_type})"
                if col_comment:
                    table_info_text += f": {col_comment}"
                table_info_text += "\n"
        
        # 构建提示词
        prompt = f"""
你是一个专业的SQL生成助手。请根据用户的需求和数据库表结构信息生成MySQL SQL语句。

数据库表结构信息:
{table_info_text}

用户需求: {user_query}

请生成一个准确、高效的MySQL SQL语句。要求：
1. 只使用上述表结构中的表和字段
2. 确保SQL语法正确
3. 如果是查询语句，建议添加适当的WHERE条件和LIMIT
4. 返回的SQL语句应该是完整的，可以直接执行

请只返回SQL语句，不要包含其他解释：
"""
        
        try:
            sql = call_llm(prompt, temperature=0.1)
            # 清理SQL语句，移除可能的markdown格式
            sql = sql.strip()
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()
            
            return sql
            
        except Exception as e:
            print(f"SQL生成失败: {e}")
            return ""
    
    def post(self, shared, prep_res, exec_res):
        """将生成的SQL写入shared"""
        if "sql_generation" not in shared:
            shared["sql_generation"] = {}
        
        shared["sql_generation"]["initial_sql"] = exec_res
        shared["sql_generation"]["current_sql"] = exec_res
        shared["sql_generation"]["validation_errors"] = []
        shared["sql_generation"]["execution_result"] = None
        
        return "default"

class SQLValidationNode(Node):
    """SQL验证节点 - 验证SQL语法和逻辑"""
    
    def prep(self, shared):
        """读取当前SQL和数据库配置"""
        current_sql = shared.get("sql_generation", {}).get("current_sql", "")
        database_config = shared.get("database_config", {})
        return current_sql, database_config
    
    def exec(self, inputs):
        """验证SQL语法和逻辑"""
        current_sql, database_config = inputs
        
        try:
            # 创建MySQL连接器和验证器
            mysql_connector = create_mysql_connector(database_config)
            validator = create_sql_validator(mysql_connector)
            
            # 验证SQL
            validation_result = validator.validate_sql(current_sql)
            
            mysql_connector.close()
            
            return validation_result
            
        except Exception as e:
            print(f"SQL验证失败: {e}")
            return {
                "is_valid": False,
                "errors": [f"验证过程出错: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }
    
    def post(self, shared, prep_res, exec_res):
        """根据验证结果返回不同action"""
        validation_result = exec_res
        
        # 更新验证错误信息
        if "sql_generation" not in shared:
            shared["sql_generation"] = {}
        
        shared["sql_generation"]["validation_errors"] = validation_result.get("errors", [])
        
        # 根据验证结果决定下一步
        if validation_result.get("is_valid", False):
            return "execute"  # 验证通过，执行SQL
        else:
            return "debug"    # 验证失败，进入调试

class SQLDebugNode(Node):
    """SQL调试节点 - 分析错误并生成修复建议"""
    
    def prep(self, shared):
        """读取验证错误和调试历史"""
        validation_errors = shared.get("sql_generation", {}).get("validation_errors", [])
        current_sql = shared.get("sql_generation", {}).get("current_sql", "")
        rag_context = shared.get("rag_context", {})
        debug_history = shared.get("debug_history", [])
        return validation_errors, current_sql, rag_context, debug_history
    
    def exec(self, inputs):
        """分析错误并生成修复建议"""
        validation_errors, current_sql, rag_context, debug_history = inputs
        
        # 构建表结构信息文本
        table_info_text = ""
        for table_info in rag_context.get("table_info", []):
            table_name = table_info["table_name"]
            columns = table_info["columns"]
            description = table_info.get("description", "")
            
            table_info_text += f"\n表名: {table_name}\n"
            table_info_text += f"描述: {description}\n"
            table_info_text += "字段:\n"
            
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                col_comment = col.get("comment", "")
                table_info_text += f"  - {col_name} ({col_type})"
                if col_comment:
                    table_info_text += f": {col_comment}"
                table_info_text += "\n"
        
        # 构建调试历史文本
        debug_history_text = ""
        if debug_history:
            debug_history_text = "\n调试历史:\n"
            for i, history in enumerate(debug_history[-3:], 1):  # 只显示最近3次
                debug_history_text += f"{i}. SQL: {history.get('sql', '')}\n"
                debug_history_text += f"   错误: {history.get('error', '')}\n"
                debug_history_text += f"   修复: {history.get('fix_suggestion', '')}\n"
        
        # 构建提示词
        prompt = f"""
你是一个专业的SQL调试助手。请分析SQL错误并提供修复建议。

数据库表结构信息:
{table_info_text}

当前SQL: {current_sql}

验证错误:
{chr(10).join(validation_errors)}
{debug_history_text}

请分析错误原因并提供修复后的SQL语句。要求：
1. 仔细分析每个错误
2. 参考表结构信息确保表名和字段名正确
3. 修复语法错误
4. 返回完整的修复后SQL语句

请只返回修复后的SQL语句：
"""
        
        try:
            fixed_sql = call_llm(prompt, temperature=0.1)
            # 清理SQL语句
            fixed_sql = fixed_sql.strip()
            if fixed_sql.startswith("```sql"):
                fixed_sql = fixed_sql[6:]
            if fixed_sql.endswith("```"):
                fixed_sql = fixed_sql[:-3]
            fixed_sql = fixed_sql.strip()
            
            return {
                "fixed_sql": fixed_sql,
                "error_analysis": validation_errors
            }
            
        except Exception as e:
            print(f"SQL调试失败: {e}")
            return {
                "fixed_sql": current_sql,
                "error_analysis": [f"调试过程出错: {str(e)}"]
            }
    
    def post(self, shared, prep_res, exec_res):
        """更新调试历史，返回修复后的SQL"""
        fixed_sql = exec_res["fixed_sql"]
        error_analysis = exec_res["error_analysis"]
        
        # 更新调试历史
        if "debug_history" not in shared:
            shared["debug_history"] = []
        
        current_sql = shared.get("sql_generation", {}).get("current_sql", "")
        
        debug_entry = {
            "iteration": len(shared["debug_history"]) + 1,
            "sql": current_sql,
            "error": "; ".join(error_analysis),
            "fix_suggestion": fixed_sql
        }
        
        shared["debug_history"].append(debug_entry)
        
        # 更新当前SQL
        if "sql_generation" not in shared:
            shared["sql_generation"] = {}
        
        shared["sql_generation"]["current_sql"] = fixed_sql
        
        # 检查是否超过最大调试次数
        max_debug_iterations = 3
        if len(shared["debug_history"]) >= max_debug_iterations:
            print(f"达到最大调试次数 ({max_debug_iterations})，停止调试")
            return "execute"  # 强制执行最后一次修复的SQL
        
        return "generate"  # 重新生成SQL

class SQLExecutionNode(Node):
    """SQL执行节点 - 执行验证通过的SQL"""
    
    def prep(self, shared):
        """读取验证通过的SQL和数据库配置"""
        current_sql = shared.get("sql_generation", {}).get("current_sql", "")
        database_config = shared.get("database_config", {})
        return current_sql, database_config
    
    def exec(self, inputs):
        """执行SQL并获取结果"""
        current_sql, database_config = inputs
        
        try:
            # 创建MySQL连接器
            mysql_connector = create_mysql_connector(database_config)
            
            # 执行SQL
            success, result = mysql_connector.execute_sql(current_sql)
            
            mysql_connector.close()
            
            if success:
                return {
                    "success": True,
                    "result": result,
                    "sql": current_sql
                }
            else:
                return {
                    "success": False,
                    "error": result,
                    "sql": current_sql
                }
                
        except Exception as e:
            print(f"SQL执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql": current_sql
            }
    
    def post(self, shared, prep_res, exec_res):
        """将执行结果写入shared"""
        if "sql_generation" not in shared:
            shared["sql_generation"] = {}
        
        shared["sql_generation"]["execution_result"] = exec_res
        
        if exec_res["success"]:
            print("SQL执行成功!")
            return "default"  # 流程结束
        else:
            print(f"SQL执行失败: {exec_res['error']}")
            # 如果执行失败，可以进入调试模式
            if len(shared.get("debug_history", [])) < 3:
                return "debug"
            else:
                return "default"  # 达到最大调试次数，结束流程
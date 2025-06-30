from pocketflow import Flow

from nodes import (
    RAGRetrievalNode,
    SQLGenerationNode,
    SQLValidationNode,
    SQLDebugNode,
    SQLExecutionNode
)


def create_text_to_sql_flow():
    """创建Text-to-SQL工作流"""
    
    # 创建节点实例
    rag_node = RAGRetrievalNode()
    generate_node = SQLGenerationNode()
    validate_node = SQLValidationNode()
    debug_node = SQLDebugNode()
    execute_node = SQLExecutionNode()
    
    # 定义流程连接
    # 主要流程：RAG检索 -> SQL生成 -> SQL验证
    rag_node >> generate_node >> validate_node
    
    # 验证结果分支
    validate_node - "execute" >> execute_node  # 验证通过，执行SQL
    validate_node - "debug" >> debug_node      # 验证失败，进入调试
    
    # 调试流程
    debug_node - "generate" >> generate_node   # 重新生成SQL
    debug_node - "execute" >> execute_node     # 强制执行修复后的SQL
    
    # 创建流程
    flow = Flow(start=rag_node)
    
    return flow

def create_simple_text_to_sql_flow():
    """创建简化版Text-to-SQL工作流（无循环调试）"""
    
    # 创建节点实例
    rag_node = RAGRetrievalNode()
    generate_node = SQLGenerationNode()
    execute_node = SQLExecutionNode()
    
    # 定义流程连接
    rag_node >> generate_node >> execute_node
    
    # 创建流程
    flow = Flow(start=rag_node)
    
    return flow

def create_debug_text_to_sql_flow():
    """创建带调试的Text-to-SQL工作流"""
    
    # 创建节点实例
    rag_node = RAGRetrievalNode()
    generate_node = SQLGenerationNode()
    validate_node = SQLValidationNode()
    debug_node = SQLDebugNode()
    execute_node = SQLExecutionNode()
    
    # 定义流程连接
    rag_node >> generate_node >> validate_node
    
    # 验证结果分支
    validate_node - "execute" >> execute_node
    validate_node - "debug" >> debug_node
    
    # 调试循环（最多3次）
    debug_node - "generate" >> generate_node
    
    # 调试失败后强制执行
    debug_node - "execute" >> execute_node
    
    # 创建流程
    flow = Flow(start=rag_node)
    
    return flow

# 默认导出主流程
text_to_sql_flow = create_text_to_sql_flow()
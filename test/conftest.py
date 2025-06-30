"""
Pytest配置文件
包含共享的fixture和测试设置
"""

import os
import sys

import pytest

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.milvus import MilvusRAG


@pytest.fixture(scope="session")
def milvus_uri():
    """Milvus服务地址"""
    return "http://localhost:19530"


@pytest.fixture(scope="session")
def collection_name():
    """测试集合名称"""
    return "test_table_schema"


@pytest.fixture(scope="function")
def milvus_rag(milvus_uri, collection_name):
    """创建Milvus RAG实例"""
    rag = MilvusRAG(
        collection_name=collection_name,
        uri=milvus_uri
    )
    
    # 确保集合存在
    rag.create_collection()
    
    yield rag
    
    # 清理：删除测试集合
    try:
        rag.delete_collection()
    except Exception:
        pass  # 忽略清理错误


@pytest.fixture(scope="function")
def sample_table_data():
    """示例表结构数据"""
    return {
        "users": {
            "table_name": "users",
            "description": "用户信息表",
            "columns": [
                {"name": "id", "type": "INT", "comment": "用户ID"},
                {"name": "name", "type": "VARCHAR(100)", "comment": "用户名"},
                {"name": "email", "type": "VARCHAR(255)", "comment": "邮箱"}
            ]
        },
        "orders": {
            "table_name": "orders", 
            "description": "订单表",
            "columns": [
                {"name": "id", "type": "INT", "comment": "订单ID"},
                {"name": "user_id", "type": "INT", "comment": "用户ID"},
                {"name": "amount", "type": "DECIMAL(10,2)", "comment": "订单金额"}
            ]
        },
        "products": {
            "table_name": "products",
            "description": "产品表",
            "columns": [
                {"name": "id", "type": "INT", "comment": "产品ID"},
                {"name": "name", "type": "VARCHAR(200)", "comment": "产品名称"},
                {"name": "price", "type": "DECIMAL(10,2)", "comment": "产品价格"},
                {"name": "category", "type": "VARCHAR(100)", "comment": "产品分类"}
            ]
        }
    }


@pytest.fixture(scope="function")
def random_embedding():
    """生成随机向量嵌入"""
    import numpy as np
    return list(np.random.rand(1536)) 
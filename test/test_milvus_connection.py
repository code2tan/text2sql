"""
Milvus连接测试
测试Milvus服务的基本连接功能
"""

import pytest

from db.milvus import MilvusRAG


class TestMilvusConnection:
    """Milvus连接测试类"""
    
    def test_milvus_client_creation(self, milvus_uri):
        """测试Milvus客户端创建"""
        rag = MilvusRAG(uri=milvus_uri)
        assert rag.milvus is not None
        assert rag.uri == milvus_uri
    
    def test_collection_creation(self, milvus_rag):
        """测试集合创建"""
        # 集合创建在fixture中已经完成
        assert milvus_rag.collection_name == "test_table_schema"
    
    def test_get_all_tables_empty(self, milvus_rag):
        """测试获取空集合中的表"""
        tables = milvus_rag.get_all_tables()
        assert isinstance(tables, list)
        assert len(tables) == 0
    
    def test_milvus_health_check(self, milvus_rag):
        """测试Milvus健康状态"""
        # 尝试执行一个简单的操作来检查连接
        try:
            tables = milvus_rag.get_all_tables()
            assert isinstance(tables, list)
        except Exception as e:
            pytest.fail(f"Milvus连接失败: {e}")


class TestMilvusConfiguration:
    """Milvus配置测试类"""
    
    def test_milvus_with_custom_uri(self):
        """测试自定义URI配置"""
        custom_uri = "http://localhost:19530"
        rag = MilvusRAG(uri=custom_uri)
        assert rag.uri == custom_uri
    
    def test_milvus_with_token(self):
        """测试带token的配置"""
        # 注意：这里只是测试配置，不实际连接
        rag = MilvusRAG(uri="http://localhost:19530", token="test_token")
        assert rag.token == "test_token"
    
    def test_milvus_dimension(self, milvus_rag):
        """测试向量维度配置"""
        assert milvus_rag.dimension == 1536  # OpenAI text-embedding-ada-002 维度 
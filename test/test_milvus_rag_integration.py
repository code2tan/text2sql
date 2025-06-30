"""
Milvus RAG集成测试
测试完整的RAG功能（需要OpenAI API Key）
"""

import os
from unittest.mock import Mock, patch

import pytest

from db.milvus import MilvusRAG


class TestMilvusRAGIntegration:
    """Milvus RAG集成测试类"""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here",
        reason="需要有效的OpenAI API Key"
    )
    def test_full_rag_pipeline(self, milvus_rag, sample_table_data):
        """测试完整的RAG流程"""
        # 插入测试数据
        success = milvus_rag.batch_insert_schemas(sample_table_data)
        assert success
        
        # 搜索相似表
        query = "查询用户订单信息"
        results = milvus_rag.search_similar_tables(query, top_k=3)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 验证搜索结果格式
        for result in results:
            assert "table_info" in result
            assert "similarity_score" in result
            assert "description" in result
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here",
        reason="需要有效的OpenAI API Key"
    )
    def test_embedding_generation(self, milvus_rag):
        """测试向量嵌入生成"""
        text = "这是一个测试文本"
        embedding = milvus_rag.get_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here",
        reason="需要有效的OpenAI API Key"
    )
    def test_table_schema_insertion(self, milvus_rag, sample_table_data):
        """测试表结构插入"""
        table_info = sample_table_data["users"]
        success = milvus_rag.insert_table_schema(table_info)
        
        assert success
        
        # 验证表已插入
        tables = milvus_rag.get_all_tables()
        assert table_info["table_name"] in tables
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here",
        reason="需要有效的OpenAI API Key"
    )
    def test_batch_insertion(self, milvus_rag, sample_table_data):
        """测试批量插入"""
        success = milvus_rag.batch_insert_schemas(sample_table_data)
        assert success
        
        # 验证所有表都插入成功
        tables = milvus_rag.get_all_tables()
        for table_name in sample_table_data.keys():
            assert table_name in tables


class TestMilvusRAGMocked:
    """使用Mock的RAG测试类（不依赖OpenAI）"""
    
    @patch('db.milvus.OpenAI')
    def test_rag_with_mock_openai(self, mock_openai, milvus_rag, sample_table_data):
        """使用Mock OpenAI测试RAG功能"""
        # 设置Mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536  # 模拟嵌入向量
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 测试插入
        table_info = sample_table_data["users"]
        success = milvus_rag.insert_table_schema(table_info)
        assert success
        
        # 测试搜索
        results = milvus_rag.search_similar_tables("查询用户信息", top_k=1)
        assert isinstance(results, list)
    
    def test_rag_error_handling(self, milvus_rag):
        """测试RAG错误处理"""
        # 测试无效的表结构
        invalid_table_info = {
            "table_name": "invalid_table",
            # 缺少必要的字段
        }
        
        success = milvus_rag.insert_table_schema(invalid_table_info)
        assert not success  # 应该失败
    
    def test_search_with_empty_collection(self, milvus_rag):
        """测试空集合的搜索"""
        results = milvus_rag.search_similar_tables("测试查询", top_k=5)
        assert isinstance(results, list)
        assert len(results) == 0  # 空集合应该返回空结果


class TestMilvusRAGUtilities:
    """RAG工具函数测试类"""
    
    def test_create_milvus_rag_function(self, milvus_uri):
        """测试create_milvus_rag函数"""
        from db.milvus import create_milvus_rag
        
        rag = create_milvus_rag(
            collection_name="test_collection",
            uri=milvus_uri
        )
        
        assert isinstance(rag, MilvusRAG)
        assert rag.collection_name == "test_collection"
        assert rag.uri == milvus_uri
    
    def test_collection_cleanup(self, milvus_rag):
        """测试集合清理"""
        collection_name = milvus_rag.collection_name
        
        # 删除集合
        milvus_rag.delete_collection()
        
        # 验证集合已删除（通过尝试获取表名）
        tables = milvus_rag.get_all_tables()
        # 删除后应该返回空列表或抛出异常
        assert isinstance(tables, list) 
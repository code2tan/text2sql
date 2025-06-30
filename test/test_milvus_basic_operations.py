"""
Milvus基础操作测试
测试插入、查询、搜索等基础功能
"""

import hashlib

import pytest

from db.milvus import MilvusRAG


class TestMilvusBasicOperations:
    """Milvus基础操作测试类"""
    
    def test_insert_single_table(self, milvus_rag, sample_table_data, random_embedding):
        """测试插入单个表结构"""
        table_info = sample_table_data["users"]
        table_name = table_info["table_name"]
        
        # 生成数字ID
        table_id = int(hashlib.md5(table_name.encode()).hexdigest()[:8], 16)
        
        # 构建描述文本
        description = f"表名: {table_name}\n"
        description += f"描述: {table_info.get('description', '')}\n"
        description += "列信息:\n"
        
        for col in table_info["columns"]:
            col_name = col["name"]
            col_type = col["type"]
            col_comment = col.get("comment", "")
            description += f"- {col_name} ({col_type})"
            if col_comment:
                description += f": {col_comment}"
            description += "\n"
        
        # 直接插入到Milvus
        milvus_rag.milvus.insert(
            collection_name=milvus_rag.collection_name,
            data=[{
                "id": table_id,
                "vector": random_embedding
            }]
        )
        
        # 验证插入成功
        tables = milvus_rag.get_all_tables()
        assert table_id in tables
    
    def test_insert_multiple_tables(self, milvus_rag, sample_table_data, random_embedding):
        """测试插入多个表结构"""
        inserted_tables = []
        
        for table_name, table_info in sample_table_data.items():
            # 生成数字ID - 确保唯一性
            table_id = int(hashlib.md5(table_name.encode()).hexdigest()[:8], 16)
            
            # 插入到Milvus
            milvus_rag.milvus.insert(
                collection_name=milvus_rag.collection_name,
                data=[{
                    "id": table_id,
                    "vector": random_embedding
                }]
            )
            inserted_tables.append(table_name)
        
        # 验证所有表都插入成功
        tables = milvus_rag.get_all_tables()
        for table_name in inserted_tables:
            table_id = int(hashlib.md5(table_name.encode()).hexdigest()[:8], 16)
            assert table_id in tables
    
    def test_search_functionality(self, milvus_rag, random_embedding):
        """测试搜索功能"""
        # 使用随机向量进行搜索
        results = milvus_rag.milvus.search(
            collection_name=milvus_rag.collection_name,
            data=[random_embedding],
            top_k=5,
            metric_type="COSINE"
        )
        
        # 验证搜索结果格式
        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], list)
    
    def test_query_functionality(self, milvus_rag):
        """测试查询功能"""
        # 查询所有表ID
        results = milvus_rag.milvus.query(
            collection_name=milvus_rag.collection_name,
            output_fields=["id"],
            limit=1000
        )
        
        assert isinstance(results, list)
    
    def test_collection_operations(self, milvus_rag):
        """测试集合操作"""
        # 测试获取集合信息
        collection_name = milvus_rag.collection_name
        
        # 验证集合存在
        try:
            tables = milvus_rag.get_all_tables()
            assert isinstance(tables, list)
        except Exception as e:
            pytest.fail(f"集合操作失败: {e}")


class TestMilvusDataValidation:
    """Milvus数据验证测试类"""
    
    def test_table_id_generation(self):
        """测试表ID生成"""
        table_name = "test_table"
        table_id = int(hashlib.md5(table_name.encode()).hexdigest()[:8], 16)
        
        assert isinstance(table_id, int)
        assert table_id > 0
    
    def test_embedding_dimension(self, random_embedding, embedding_dimension):
        """测试向量维度"""
        assert len(random_embedding) == embedding_dimension
        assert all(isinstance(x, (int, float)) for x in random_embedding)
    
    def test_table_info_structure(self, sample_table_data):
        """测试表结构信息格式"""
        for table_name, table_info in sample_table_data.items():
            assert "table_name" in table_info
            assert "description" in table_info
            assert "columns" in table_info
            assert isinstance(table_info["columns"], list)
            
            for col in table_info["columns"]:
                assert "name" in col
                assert "type" in col 
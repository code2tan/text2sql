import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from pymilvus import MilvusClient
from pymilvus import CollectionSchema, FieldSchema, DataType

load_dotenv()

class MilvusRAG:
    """基于Milvus Lite的RAG系统"""
    
    def __init__(self, collection_name: str = "table_schema", 
                 uri: str = "http://localhost:19530", 
                 token: str | None = None,
                 embedding_model: str = "nomic-embed-text:latest",
                 embedding_dimension: int = 768):
        """
        初始化Milvus Lite RAG系统
        
        Args:
            collection_name: 集合名称
            uri: Milvus服务地址，默认为本地Docker
            token: 认证token（如果有的话）
            embedding_model: 嵌入模型名称，默认为nomic-embed-text:latest
            embedding_dimension: 嵌入向量维度，nomic-embed-text默认为768
        """
        self.collection_name = collection_name
        self.uri = uri
        self.token = token
        self.embedding_model = embedding_model
        self.dimension = embedding_dimension
        
        # 初始化Milvus客户端
        if token:
            self.milvus = MilvusClient(uri=uri, token=token)
        else:
            self.milvus = MilvusClient(uri=uri)
            
        # 初始化Ollama客户端（用于本地embedding）
        try:
            from ollama import Client
            self.ollama_client = Client(host='http://localhost:11434')
        except ImportError:
            print("警告: 未安装ollama包，请运行: pip install ollama")
            self.ollama_client = None
        
    def create_collection(self):
        """创建向量集合"""
        try:
            # 使用Milvus 2.6.0的简单API创建集合
            self.milvus.create_collection(
                collection_name=self.collection_name,
                dimension=self.dimension,
                metric_type="COSINE"
            )
            print(f"集合 {self.collection_name} 创建成功")
            
            # 创建后立即加载集合
            self.load_collection()
        except Exception as e:
            print(f"集合已存在或创建失败: {e}")
    
    def load_collection(self):
        """加载集合到内存"""
        try:
            self.milvus.load_collection(self.collection_name)
            print(f"集合 {self.collection_name} 已加载")
        except Exception as e:
            print(f"加载集合失败: {e}")
    
    def ensure_collection_loaded(self):
        """确保集合已加载"""
        try:
            # 直接尝试加载集合，如果已加载会忽略
            self.load_collection()
        except Exception as e:
            # 如果加载失败，可能是集合不存在或其他问题
            print(f"确保集合加载时出错: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            向量嵌入
        """
        try:
            if self.ollama_client is None:
                raise Exception("Ollama客户端未初始化")
            
            # 使用Ollama获取embedding
            response = self.ollama_client.embeddings(
                model=self.embedding_model,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"获取嵌入失败: {e}")
            raise
    
    def insert_table_schema(self, table_info: Dict[str, Any]) -> bool:
        """
        插入表结构信息到向量数据库
        
        Args:
            table_info: 表结构信息
            
        Returns:
            是否插入成功
        """
        try:
            # 构建表结构描述文本
            table_name = table_info["table_name"]
            columns = table_info["columns"]
            
            # 构建描述文本
            description = f"表名: {table_name}\n"
            description += f"描述: {table_info.get('description', '')}\n"
            description += "列信息:\n"
            
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]
                col_comment = col.get("comment", "")
                description += f"- {col_name} ({col_type})"
                if col_comment:
                    description += f": {col_comment}"
                description += "\n"
            
            # 获取向量嵌入
            embedding = self.get_embedding(description)
            
            # 生成数字ID（使用表名的hash值）
            import hashlib
            table_id = int(hashlib.md5(table_name.encode()).hexdigest()[:8], 16)
            
            # 插入到Milvus - 只使用默认字段
            self.milvus.insert(
                collection_name=self.collection_name,
                data=[{
                    "id": table_id,
                    "vector": embedding
                }]
            )
            
            print(f"表 {table_name} 信息已插入向量数据库")
            return True
            
        except Exception as e:
            print(f"插入表结构失败: {e}")
            return False
    
    def search_similar_tables(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相似的表结构信息
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            相似的表结构信息列表
        """
        try:
            # 确保集合已加载
            self.ensure_collection_loaded()
            
            # 获取查询的向量嵌入
            query_embedding = self.get_embedding(query)
            
            # 在Milvus中搜索
            results = self.milvus.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                top_k=top_k,
                metric_type="COSINE"
            )
            
            # 处理搜索结果 - 只返回ID和相似度分数
            similar_tables = []
            for result in results[0]:
                table_id = result.get("id")
                similarity_score = result.get("score", 0.0)
                
                similar_tables.append({
                    "table_id": table_id,
                    "similarity_score": similarity_score
                })
            
            return similar_tables
            
        except Exception as e:
            print(f"搜索相似表失败: {e}")
            return []
    
    def batch_insert_schemas(self, schemas: Dict[str, Any]) -> bool:
        """
        批量插入多个表的结构信息
        
        Args:
            schemas: 表结构信息字典
            
        Returns:
            是否全部插入成功
        """
        try:
            # 确保集合存在
            self.create_collection()
            
            success_count = 0
            total_count = len(schemas)
            
            for table_name, table_info in schemas.items():
                if self.insert_table_schema(table_info):
                    success_count += 1
            
            print(f"批量插入完成: {success_count}/{total_count} 个表成功")
            return success_count == total_count
            
        except Exception as e:
            print(f"批量插入失败: {e}")
            return False
    
    def get_all_tables(self) -> List[int]:
        """
        获取所有已存储的表ID
        
        Returns:
            表ID列表
        """
        try:
            # 确保集合已加载
            self.ensure_collection_loaded()
            
            # 获取集合中的所有数据
            results = self.milvus.query(
                collection_name=self.collection_name,
                output_fields=["id"],
                limit=1000  # 添加limit参数
            )
            
            return [result["id"] for result in results]
            
        except Exception as e:
            print(f"获取表ID列表失败: {e}")
            return []
    
    def delete_collection(self):
        """删除集合"""
        try:
            self.milvus.drop_collection(self.collection_name)
            print(f"集合 {self.collection_name} 已删除")
        except Exception as e:
            print(f"删除集合失败: {e}")

def create_milvus_rag(collection_name: str = "table_schema", 
                     uri: str = "http://localhost:19530",
                     token: str | None = None,
                     embedding_model: str = "nomic-embed-text:latest",
                     embedding_dimension: int = 768) -> MilvusRAG:
    """
    创建Milvus Lite RAG实例
    
    Args:
        collection_name: 集合名称
        uri: Milvus服务地址
        token: 认证token
        embedding_model: 嵌入模型名称
        embedding_dimension: 嵌入向量维度
        
    Returns:
        MilvusLiteRAG实例
    """
    return MilvusRAG(collection_name, uri, token, embedding_model, embedding_dimension)

if __name__ == "__main__":
    # 测试Milvus Lite RAG
    # 使用Docker中的Milvus服务和本地nomic-embed-text模型
    rag = create_milvus_rag(
        uri="http://localhost:19530",
        embedding_model="nomic-embed-text:latest",
        embedding_dimension=768
    )
    
    # 创建测试数据
    test_schema = {
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
        }
    }
    
    # 批量插入
    rag.batch_insert_schemas(test_schema)
    
    # 搜索测试
    query = "查询用户订单信息"
    results = rag.search_similar_tables(query, top_k=2)
    
    print("搜索结果:")
    for result in results:
        print(f"表名: {result['table_id']}")
        print(f"相似度: {result['similarity_score']:.3f}")
        print("---") 
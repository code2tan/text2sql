import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from pymilvus import MilvusClient
from openai import OpenAI

load_dotenv()

class MilvusRAG:
    """基于Milvus Lite的RAG系统"""
    
    def __init__(self, collection_name: str = "table_schema", 
                 uri: str = "http://localhost:19530", 
                 token: str | None = None):
        """
        初始化Milvus Lite RAG系统
        
        Args:
            collection_name: 集合名称
            uri: Milvus服务地址，默认为本地Docker
            token: 认证token（如果有的话）
        """
        self.collection_name = collection_name
        self.uri = uri
        self.token = token
        
        # 初始化Milvus客户端
        if token:
            self.milvus = MilvusClient(uri=uri, token=token)
        else:
            self.milvus = MilvusClient(uri=uri)
            
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.dimension = 1536  # OpenAI text-embedding-ada-002 维度
        
    def create_collection(self):
        """创建向量集合"""
        try:
            # 创建集合
            self.milvus.create_collection(
                collection_name=self.collection_name,
                dimension=self.dimension,
                metric_type="COSINE"
            )
            print(f"集合 {self.collection_name} 创建成功")
        except Exception as e:
            print(f"集合已存在或创建失败: {e}")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        
        Args:
            text: 输入文本
            
        Returns:
            向量嵌入
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
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
            
            # 插入到Milvus
            self.milvus.insert(
                collection_name=self.collection_name,
                data=[{
                    "id": table_id,
                    "embedding": embedding,
                    "table_info": table_info,
                    "description": description,
                    "table_name": table_name  # 添加表名字段用于查询
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
            # 获取查询的向量嵌入
            query_embedding = self.get_embedding(query)
            
            # 在Milvus中搜索
            results = self.milvus.search(
                collection_name=self.collection_name,
                data=[query_embedding],
                top_k=top_k,
                metric_type="COSINE",
                output_fields=["table_info", "description"]
            )
            
            # 处理搜索结果 - 修复结果处理方式
            similar_tables = []
            for result in results[0]:
                # Milvus Lite返回的结果格式不同
                table_info = result.get("table_info")
                similarity_score = result.get("score", 0.0)
                description = result.get("description", "")
                
                similar_tables.append({
                    "table_info": table_info,
                    "similarity_score": similarity_score,
                    "description": description
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
    
    def get_all_tables(self) -> List[str]:
        """
        获取所有已存储的表名
        
        Returns:
            表名列表
        """
        try:
            # 获取集合中的所有数据
            results = self.milvus.query(
                collection_name=self.collection_name,
                output_fields=["table_name"],
                limit=1000  # 添加limit参数
            )
            
            return [result["table_name"] for result in results]
            
        except Exception as e:
            print(f"获取表名列表失败: {e}")
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
                     token: str | None = None) -> MilvusRAG:
    """
    创建Milvus Lite RAG实例
    
    Args:
        collection_name: 集合名称
        uri: Milvus服务地址
        token: 认证token
        
    Returns:
        MilvusLiteRAG实例
    """
    return MilvusRAG(collection_name, uri, token)

if __name__ == "__main__":
    # 测试Milvus Lite RAG
    # 使用Docker中的Milvus服务
    rag = create_milvus_rag(uri="http://localhost:19530")
    
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
        print(f"表名: {result['table_info']['table_name']}")
        print(f"相似度: {result['similarity_score']:.3f}")
        print("---") 
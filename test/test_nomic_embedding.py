#!/usr/bin/env python3
"""
测试nomic-embed-text模型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ollama_connection():
    """测试Ollama连接"""
    try:
        from ollama import Client
        client = Client(host='http://localhost:11434')
        print("✓ Ollama客户端创建成功")
        return client
    except ImportError:
        print("❌ 未安装ollama包，请运行: uv add ollama")
        return None
    except Exception as e:
        print(f"❌ Ollama连接失败: {e}")
        return None

def test_nomic_embedding(client):
    """测试nomic-embed-text模型"""
    if client is None:
        return False
    
    try:
        # 测试embedding生成
        text = "这是一个测试文本"
        response = client.embeddings(
            model="nomic-embed-text:latest",
            prompt=text
        )
        
        embedding = response['embedding']
        print(f"✓ Embedding生成成功，维度: {len(embedding)}")
        
        # 验证维度
        if len(embedding) == 768:
            print("✓ Embedding维度正确 (768)")
        else:
            print(f"⚠️  Embedding维度异常: {len(embedding)} (期望: 768)")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding生成失败: {e}")
        return False

def test_milvus_integration():
    """测试Milvus集成"""
    try:
        from db.milvus import create_milvus_rag
        
        # 创建RAG实例
        rag = create_milvus_rag(
            collection_name="test_nomic",
            embedding_model="nomic-embed-text:latest",
            embedding_dimension=768
        )
        
        print("✓ Milvus RAG实例创建成功")
        
        # 测试embedding生成
        text = "测试表结构"
        embedding = rag.get_embedding(text)
        
        print(f"✓ RAG Embedding生成成功，维度: {len(embedding)}")
        
        # 清理测试集合
        try:
            rag.delete_collection()
            print("✓ 测试集合清理成功")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Milvus集成测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试nomic-embed-text模型...")
    print("=" * 50)
    
    # 测试Ollama连接
    client = test_ollama_connection()
    
    # 测试nomic-embed-text模型
    if client:
        test_nomic_embedding(client)
    
    # 测试Milvus集成
    test_milvus_integration()
    
    print("=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
简单的测试运行脚本
用于验证测试结构，不依赖pytest
"""

import importlib
import os
import sys
import traceback
import inspect
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_fixtures():
    """创建测试所需的fixtures"""
    import numpy as np
    from db.milvus import MilvusRAG
    
    fixtures = {}
    
    # 基本配置fixtures
    fixtures['milvus_uri'] = "http://localhost:19530"
    fixtures['collection_name'] = "test_table_schema"
    fixtures['embedding_model'] = "nomic-embed-text:latest"
    fixtures['embedding_dimension'] = 768
    
    # 创建Milvus RAG实例
    try:
        rag = MilvusRAG(
            collection_name=fixtures['collection_name'],
            uri=fixtures['milvus_uri'],
            embedding_model=fixtures['embedding_model'],
            embedding_dimension=fixtures['embedding_dimension']
        )
        # 确保集合存在
        rag.create_collection()
        fixtures['milvus_rag'] = rag
    except Exception as e:
        print(f"警告: 无法创建Milvus RAG实例: {e}")
        fixtures['milvus_rag'] = None
    
    # 示例表结构数据
    fixtures['sample_table_data'] = {
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
    
    # 随机向量嵌入
    fixtures['random_embedding'] = list(np.random.rand(fixtures['embedding_dimension']))
    
    # 添加Mock相关的fixtures
    try:
        from unittest.mock import Mock
        fixtures['mock_client'] = Mock()
        fixtures['mock_ollama'] = Mock()
        fixtures['mock_response'] = {'embedding': [0.1] * fixtures['embedding_dimension']}
        fixtures['mock_ollama'].embeddings.return_value = fixtures['mock_response']
        fixtures['mock_client'].return_value = fixtures['mock_ollama']
    except ImportError:
        fixtures['mock_client'] = None
        fixtures['mock_ollama'] = None
        fixtures['mock_response'] = None
    
    return fixtures

def cleanup_fixtures(fixtures):
    """清理fixtures资源"""
    if fixtures.get('milvus_rag'):
        try:
            fixtures['milvus_rag'].delete_collection()
        except Exception:
            pass  # 忽略清理错误

def get_test_method_args(method, fixtures):
    """获取测试方法所需的参数"""
    sig = inspect.signature(method)
    args = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        if param_name in fixtures:
            args.append(fixtures[param_name])
        else:
            # 如果fixture不存在，尝试提供默认值
            if param.default != inspect.Parameter.empty:
                args.append(param.default)
            else:
                # 对于没有默认值的必需参数，跳过这个测试
                return None
    
    return args

def run_test_module(module_name: str, fixtures: Dict[str, Any]) -> Dict[str, Any]:
    """运行测试模块"""
    print(f"\n{'='*50}")
    print(f"运行测试模块: {module_name}")
    print(f"{'='*50}")
    
    try:
        # 导入测试模块
        module = importlib.import_module(module_name)
        
        # 查找测试类
        test_classes = []
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and name.startswith('Test'):
                test_classes.append(obj)
        
        results = {
            'module': module_name,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # 运行每个测试类
        for test_class in test_classes:
            print(f"\n测试类: {test_class.__name__}")
            print("-" * 30)
            
            # 创建测试实例
            test_instance = test_class()
            
            # 查找测试方法
            test_methods = []
            for name in dir(test_instance):
                if name.startswith('test_'):
                    test_methods.append(name)
            
            # 运行测试方法
            for method_name in test_methods:
                method = getattr(test_instance, method_name)
                if callable(method):
                    results['total_tests'] += 1
                    
                    try:
                        # 获取方法参数
                        args = get_test_method_args(method, fixtures)
                        
                        if args is None:
                            print(f"⚠ {method_name}: 缺少必需的fixtures，跳过")
                            results['failed'] += 1
                            results['errors'].append({
                                'method': method_name,
                                'error': '缺少必需的fixtures',
                                'traceback': '跳过测试'
                            })
                            continue
                        
                        # 尝试运行测试方法
                        method(*args)
                        print(f"✓ {method_name}")
                        results['passed'] += 1
                    except Exception as e:
                        print(f"✗ {method_name}: {e}")
                        results['failed'] += 1
                        results['errors'].append({
                            'method': method_name,
                            'error': str(e),
                            'traceback': traceback.format_exc()
                        })
        
        return results
        
    except Exception as e:
        print(f"导入模块 {module_name} 失败: {e}")
        return {
            'module': module_name,
            'total_tests': 0,
            'passed': 0,
            'failed': 1,
            'errors': [{'method': 'import', 'error': str(e), 'traceback': traceback.format_exc()}]
        }


def main():
    """主函数"""
    print("开始运行测试...")
    
    # 创建fixtures
    print("创建测试fixtures...")
    fixtures = create_fixtures()
    
    try:
        # 测试模块列表
        test_modules = [
            'test.test_milvus_connection',
            'test.test_milvus_basic_operations',
            'test.test_milvus_rag_integration'
        ]
        
        all_results = []
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        # 运行每个测试模块
        for module_name in test_modules:
            try:
                results = run_test_module(module_name, fixtures)
                all_results.append(results)
                
                total_tests += results['total_tests']
                total_passed += results['passed']
                total_failed += results['failed']
                
            except Exception as e:
                print(f"运行模块 {module_name} 时出错: {e}")
        
        # 打印总结
        print(f"\n{'='*50}")
        print("测试总结")
        print(f"{'='*50}")
        print(f"总测试数: {total_tests}")
        print(f"通过: {total_passed}")
        print(f"失败: {total_failed}")
        print(f"成功率: {total_passed/total_tests*100:.1f}%" if total_tests > 0 else "成功率: 0%")
        
        # 打印错误详情
        if total_failed > 0:
            print(f"\n错误详情:")
            for result in all_results:
                if result['errors']:
                    print(f"\n模块: {result['module']}")
                    for error in result['errors']:
                        print(f"  - {error['method']}: {error['error']}")
    
    finally:
        # 清理fixtures
        print("\n清理测试资源...")
        cleanup_fixtures(fixtures)


if __name__ == "__main__":
    main() 
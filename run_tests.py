#!/usr/bin/env python3
"""
简单的测试运行脚本
用于验证测试结构，不依赖pytest
"""

import importlib
import os
import sys
import traceback
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_test_module(module_name: str) -> Dict[str, Any]:
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
                        # 尝试运行测试方法
                        method()
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
            results = run_test_module(module_name)
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


if __name__ == "__main__":
    main() 
import re
from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

class SQLValidator:
    """SQL验证器"""
    
    def __init__(self, mysql_connector):
        """
        初始化SQL验证器
        
        Args:
            mysql_connector: MySQL连接器实例
        """
        self.mysql_connector = mysql_connector
        self.schema_info = None
        self._load_schema()
    
    def _load_schema(self):
        """加载数据库schema信息"""
        try:
            self.schema_info = self.mysql_connector.get_table_schema()
        except Exception as e:
            print(f"加载schema失败: {e}")
            self.schema_info = {}
    
    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        全面验证SQL语句
        
        Args:
            sql: SQL语句
            
        Returns:
            验证结果字典
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # 1. 基本语法检查
        syntax_result = self._validate_syntax(sql)
        if not syntax_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(syntax_result["errors"])
        
        # 2. 表名检查
        table_result = self._validate_tables(sql)
        if not table_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(table_result["errors"])
        
        # 3. 字段名检查
        column_result = self._validate_columns(sql)
        if not column_result["is_valid"]:
            result["is_valid"] = False
            result["errors"].extend(column_result["errors"])
        
        # 4. 逻辑检查
        logic_result = self._validate_logic(sql)
        result["warnings"].extend(logic_result["warnings"])
        result["suggestions"].extend(logic_result["suggestions"])
        
        return result
    
    def _validate_syntax(self, sql: str) -> Dict[str, Any]:
        """验证SQL语法"""
        result = {"is_valid": True, "errors": []}
        
        try:
            # 使用SQLAlchemy验证语法
            self.mysql_connector.validate_sql_syntax(sql)
        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"语法错误: {str(e)}")
        
        return result
    
    def _validate_tables(self, sql: str) -> Dict[str, Any]:
        """验证表名是否存在"""
        result = {"is_valid": True, "errors": []}
        
        if not self.schema_info:
            return result
        
        # 提取SQL中的表名
        table_names = self._extract_table_names(sql)
        available_tables = set(self.schema_info.keys())
        
        for table_name in table_names:
            if table_name not in available_tables:
                result["is_valid"] = False
                result["errors"].append(f"表 '{table_name}' 不存在")
                
                # 提供相似表名建议
                suggestions = self._find_similar_tables(table_name, available_tables)
                if suggestions:
                    result["errors"].append(f"可能的表名: {', '.join(suggestions)}")
        
        return result
    
    def _validate_columns(self, sql: str) -> Dict[str, Any]:
        """验证字段名是否存在"""
        result = {"is_valid": True, "errors": []}
        
        if not self.schema_info:
            return result
        
        # 提取SQL中的字段名
        column_names = self._extract_column_names(sql)
        
        for table_name, columns in column_names.items():
            if table_name in self.schema_info:
                available_columns = {col["name"] for col in self.schema_info[table_name]["columns"]}
                
                for column_name in columns:
                    if column_name not in available_columns:
                        result["is_valid"] = False
                        result["errors"].append(f"表 '{table_name}' 中不存在字段 '{column_name}'")
                        
                        # 提供相似字段名建议
                        suggestions = self._find_similar_columns(column_name, available_columns)
                        if suggestions:
                            result["errors"].append(f"可能的字段名: {', '.join(suggestions)}")
        
        return result
    
    def _validate_logic(self, sql: str) -> Dict[str, Any]:
        """验证SQL逻辑"""
        result = {"warnings": [], "suggestions": []}
        
        sql_upper = sql.upper()
        
        # 检查是否有WHERE子句
        if "SELECT" in sql_upper and "WHERE" not in sql_upper:
            result["warnings"].append("查询没有WHERE条件，可能返回大量数据")
        
        # 检查是否有LIMIT子句
        if "SELECT" in sql_upper and "LIMIT" not in sql_upper:
            result["suggestions"].append("建议添加LIMIT子句以限制返回结果数量")
        
        # 检查是否有ORDER BY子句
        if "SELECT" in sql_upper and "ORDER BY" not in sql_upper:
            result["suggestions"].append("建议添加ORDER BY子句以确保结果顺序")
        
        # 检查JOIN语法
        if "JOIN" in sql_upper and "ON" not in sql_upper:
            result["warnings"].append("JOIN语句缺少ON条件")
        
        return result
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """提取SQL中的表名"""
        table_names = []
        
        # 匹配FROM和JOIN后的表名
        patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            table_names.extend(matches)
        
        return list(set(table_names))
    
    def _extract_column_names(self, sql: str) -> Dict[str, List[str]]:
        """提取SQL中的字段名和对应的表名"""
        column_mapping = {}
        
        # 匹配SELECT后的字段名
        select_pattern = r'SELECT\s+(.*?)\s+FROM\s+(\w+)'
        select_matches = re.findall(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for columns_str, table_name in select_matches:
            # 分割字段名
            columns = []
            for col in columns_str.split(','):
                col = col.strip()
                # 移除别名
                if ' AS ' in col.upper():
                    col = col.split(' AS ')[0].strip()
                # 移除表名前缀
                if '.' in col:
                    col = col.split('.')[-1].strip()
                columns.append(col)
            
            column_mapping[table_name] = columns
        
        return column_mapping
    
    def _find_similar_tables(self, table_name: str, available_tables: set) -> List[str]:
        """查找相似的表名"""
        suggestions = []
        
        for available_table in available_tables:
            # 简单的相似度计算
            if table_name.lower() in available_table.lower() or available_table.lower() in table_name.lower():
                suggestions.append(available_table)
        
        return suggestions[:3]  # 最多返回3个建议
    
    def _find_similar_columns(self, column_name: str, available_columns: set) -> List[str]:
        """查找相似的字段名"""
        suggestions = []
        
        for available_column in available_columns:
            # 简单的相似度计算
            if column_name.lower() in available_column.lower() or available_column.lower() in column_name.lower():
                suggestions.append(available_column)
        
        return suggestions[:3]  # 最多返回3个建议
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """获取表信息"""
        return self.schema_info.get(table_name)
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        return list(self.schema_info.keys()) if self.schema_info else []

def create_sql_validator(mysql_connector) -> SQLValidator:
    """
    创建SQL验证器实例
    
    Args:
        mysql_connector: MySQL连接器
        
    Returns:
        SQLValidator实例
    """
    return SQLValidator(mysql_connector)

if __name__ == "__main__":
    # 测试SQL验证器
    from utils.mysql_connector import create_mysql_connector
    
    config = {
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "user": "root",
        "password": "password"
    }
    
    try:
        connector = create_mysql_connector(config)
        validator = create_sql_validator(connector)
        
        # 测试SQL
        test_sql = "SELECT name, email FROM users WHERE id = 1"
        result = validator.validate_sql(test_sql)
        
        print("验证结果:")
        print(f"是否有效: {result['is_valid']}")
        print(f"错误: {result['errors']}")
        print(f"警告: {result['warnings']}")
        print(f"建议: {result['suggestions']}")
        
        connector.close()
    except Exception as e:
        print(f"测试失败: {e}") 
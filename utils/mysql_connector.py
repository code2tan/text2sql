import pymysql
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
import json

class MySQLConnector:
    """MySQL数据库连接器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MySQL连接器
        
        Args:
            config: 数据库配置字典，包含host, port, database, user, password
        """
        self.config = config
        self.connection = None
        self.engine = None
        
    def connect(self) -> bool:
        """建立数据库连接"""
        try:
            # 创建SQLAlchemy引擎
            connection_string = (
                f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
            )
            self.engine = create_engine(connection_string)
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("MySQL连接成功")
            return True
            
        except Exception as e:
            print(f"MySQL连接失败: {e}")
            return False
    
    def get_table_schema(self) -> Dict[str, Any]:
        """
        获取数据库表结构信息
        
        Returns:
            包含所有表结构信息的字典
        """
        if not self.engine:
            raise Exception("数据库未连接")
        
        try:
            inspector = inspect(self.engine)
            schema_info = {}
            
            for table_name in inspector.get_table_names():
                table_info = {
                    "table_name": table_name,
                    "columns": [],
                    "primary_keys": [],
                    "foreign_keys": [],
                    "description": f"表 {table_name}"
                }
                
                # 获取列信息
                columns = inspector.get_columns(table_name)
                for column in columns:
                    col_info = {
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column["nullable"],
                        "default": column.get("default"),
                        "comment": column.get("comment", "")
                    }
                    table_info["columns"].append(col_info)
                
                # 获取主键信息
                primary_keys = inspector.get_pk_constraint(table_name)
                if primary_keys["constrained_columns"]:
                    table_info["primary_keys"] = primary_keys["constrained_columns"]
                
                # 获取外键信息
                foreign_keys = inspector.get_foreign_keys(table_name)
                table_info["foreign_keys"] = foreign_keys
                
                schema_info[table_name] = table_info
            
            return schema_info
            
        except Exception as e:
            print(f"获取表结构失败: {e}")
            raise
    
    def execute_sql(self, sql: str) -> Tuple[bool, Any]:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            
        Returns:
            (是否成功, 结果或错误信息)
        """
        if not self.engine:
            raise Exception("数据库未连接")
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                
                # 如果是查询语句，获取结果
                if sql.strip().upper().startswith("SELECT"):
                    rows = result.fetchall()
                    columns = result.keys()
                    return True, {
                        "columns": list(columns),
                        "rows": [list(row) for row in rows],
                        "row_count": len(rows)
                    }
                else:
                    # 非查询语句，返回影响的行数
                    return True, {"affected_rows": result.rowcount}
                    
        except Exception as e:
            return False, str(e)
    
    def validate_sql_syntax(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        验证SQL语法（不执行）
        
        Args:
            sql: SQL语句
            
        Returns:
            (语法是否正确, 错误信息)
        """
        if not self.engine:
            raise Exception("数据库未连接")
        
        try:
            with self.engine.connect() as conn:
                # 尝试编译SQL，不执行
                compiled = text(sql).compile(compile_kwargs={"literal_binds": True})
                return True, None
        except Exception as e:
            return False, str(e)
    
    def get_table_names(self) -> List[str]:
        """获取所有表名"""
        if not self.engine:
            raise Exception("数据库未连接")
        
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_column_names(self, table_name: str) -> List[str]:
        """获取指定表的所有列名"""
        if not self.engine:
            raise Exception("数据库未连接")
        
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        return [col["name"] for col in columns]
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            print("MySQL连接已关闭")

def create_mysql_connector(config: Dict[str, Any]) -> MySQLConnector:
    """
    创建MySQL连接器实例
    
    Args:
        config: 数据库配置
        
    Returns:
        MySQLConnector实例
    """
    connector = MySQLConnector(config)
    if connector.connect():
        return connector
    else:
        raise Exception("无法连接到MySQL数据库")

if __name__ == "__main__":
    # 测试MySQL连接器
    config = {
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "user": "root",
        "password": "password"
    }
    
    try:
        connector = create_mysql_connector(config)
        schema = connector.get_table_schema()
        print("表结构信息:", json.dumps(schema, indent=2, ensure_ascii=False))
        connector.close()
    except Exception as e:
        print(f"测试失败: {e}") 
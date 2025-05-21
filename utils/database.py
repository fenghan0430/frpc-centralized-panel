import sqlite3
import threading

class DataBase:
    """
    数据库类，使用sqlite3实现基本的数据库操作
    提供表管理、增删改查功能
    """

    def __init__(self, db_path):
        """
        初始化数据库配置
        
        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.local = threading.local()  # 用于存储线程本地资源

    def __enter__(self):
        """
        上下文管理器入口，自动建立数据库连接
        
        Returns:
            DataBase: 返回自身实例便于进一步操作
        """
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.cursor = self.local.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口，自动清理数据库连接
        
        Args:
            exc_type (type): 异常类型（如果发生）
            exc_val (Exception): 异常实例（如果发生）
            exc_tb (traceback): 异常回溯信息
        """
        if hasattr(self.local, 'cursor'):
            self.local.cursor.close()
            del self.local.cursor
        if hasattr(self.local, 'conn'):
            self.local.conn.close()
            del self.local.conn

    def init_db(self):
        """
        初始化数据库表结构，清除现有表后重新创建
        
        Raises:
            RuntimeError: 当数据库连接未建立时抛出
        """
        if not hasattr(self.local, 'cursor') or not hasattr(self.local, 'conn'):
            raise RuntimeError("Database connection not established")
        
        # 清理旧表
        self.local.cursor.execute('DROP TABLE IF EXISTS program')
        
        # 创建新表
        create_sql = '''
        CREATE TABLE IF NOT EXISTS program (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
        '''
        self.local.cursor.execute(create_sql)
        self.local.conn.commit()

    def query_program(self, program_id=None, name=None):
        """
        查询程序信息，支持按ID/名称查询或全表查询
        
        Args:
            program_id (int, optional): 程序唯一标识. Defaults to None.
            name (str, optional): 程序名称. Defaults to None.
        
        Raises:
            RuntimeError: 当数据库连接未建立时抛出
        
        Returns:
            list: 查询结果列表（元组形式），每个元组包含(id, name, description)
        """
        if not hasattr(self.local, 'cursor'):
            raise RuntimeError("Database connection not established")
            
        if program_id is not None:
            self.local.cursor.execute(
                'SELECT * FROM program WHERE id = ?', 
                (program_id,)
            )
        elif name is not None:
            self.local.cursor.execute(
                'SELECT * FROM program WHERE name = ?', 
                (name,)
            )
        else:
            self.local.cursor.execute('SELECT * FROM program')
            
        return self.local.cursor.fetchall()

    def update_program(self, program_id, name=None, description=None):
        """
        更新程序信息，支持部分字段更新
        
        Args:
            program_id (int): 要更新的程序ID
            name (str, optional): 新名称. Defaults to None.
            description (str, optional): 新描述. Defaults to None.
        
        Raises:
            RuntimeError: 当数据库连接未建立时抛出
        
        Returns:
            bool: 是否成功更新（返回True表示至少更新一行）
        """
        if not hasattr(self.local, 'cursor') or not hasattr(self.local, 'conn'):
            raise RuntimeError("数据库连接尚未建立")
        update_fields = []
        params = []
        
        if name is not None:
            # 检查新 name 是否已被其它记录使用
            self.local.cursor.execute(
                "SELECT id FROM program WHERE name = ? AND id != ?", (name, program_id)
            )
            if self.local.cursor.fetchone():
                raise ValueError("程序名称已存在")
            update_fields.append("name = ?")
            params.append(name)
        if description is not None:
            update_fields.append("description = ?")
            params.append(description)
            
        if not update_fields:
            return False
            
        update_sql = f"UPDATE program SET {', '.join(update_fields)} WHERE id = ?"
        params.append(program_id)
        
        self.local.cursor.execute(update_sql, tuple(params))
        self.local.conn.commit()
        return self.local.cursor.rowcount > 0

    def delete_program(self, program_id):
        """
        删除程序记录
        
        Args:
            program_id (int): 要删除的程序ID
        
        Raises:
            RuntimeError: 当数据库连接未建立时抛出
        
        Returns:
            bool: 是否成功删除（返回True表示至少删除一行）
        """
        if not hasattr(self.local, 'cursor') or not hasattr(self.local, 'conn'):
            raise RuntimeError("Database connection not established")
            
        self.local.cursor.execute(
            'DELETE FROM program WHERE id = ?', 
            (program_id,)
        )
        self.local.conn.commit()
        return self.local.cursor.rowcount > 0

    def insert_program(self, name, description=None):
        """
        插入新的程序记录
        
        Args:
            name (str): 程序名称
            description (str, optional): 程序描述. Defaults to None.
        
        Raises:
            RuntimeError: 当数据库连接未建立时抛出

        Returns:
            int: 新插入记录的自增ID
        """
        if not hasattr(self.local, 'cursor') or not hasattr(self.local, 'conn'):
            raise RuntimeError("数据库连接尚未建立")
        # 检查 name 是否唯一
        self.local.cursor.execute("SELECT id FROM program WHERE name = ?", (name,))
        if self.local.cursor.fetchone():
            raise ValueError("程序名称已存在")
        insert_sql = "INSERT INTO program (name, description) VALUES (?, ?)"
        self.local.cursor.execute(insert_sql, (name, description))
        self.local.conn.commit()
        return self.local.cursor.lastrowid

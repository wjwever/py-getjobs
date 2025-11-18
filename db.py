import mysql.connector
from mysql.connector import Error

class MySqlClient:
    def __init__(self):
        self.connection = None
        self.connect()
        
    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',      # 数据库地址
                user='root',           # 用户名
                password='root',   # 密码
                database='name_ai'     # 数据库名
            )
            print("MySQL数据库连接成功！")
        except Error as e:
            print(f"连接失败: {e}")
    
    def create_table(self):
        """创建数据表"""
        try:
            cursor = self.connection.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                age INT
            )
            """
            cursor.execute(create_table_query)
            print("数据表创建成功！")
        except Error as e:
            print(f"创建表失败: {e}")
    
    # CREATE - 插入数据
    def create_user(self, name, email, age):
        """插入新用户"""
        try:
            cursor = self.connection.cursor()
            insert_query = "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (name, email, age))
            self.connection.commit()
            print(f"用户 {name} 插入成功！")
        except Error as e:
            print(f"插入失败: {e}")
    
    # READ - 查询数据
    def read_users(self):
        """查询所有用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            print("\n所有用户:")
            for user in users:
                print(f"ID: {user[0]}, 姓名: {user[1]}, 邮箱: {user[2]}, 年龄: {user[3]}")
            return users
        except Error as e:
            print(f"查询失败: {e}")
    
    def read_user_by_id(self, user_id):
        """根据ID查询用户"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if user:
                print(f"\n找到用户: ID: {user[0]}, 姓名: {user[1]}, 邮箱: {user[2]}, 年龄: {user[3]}")
            else:
                print(f"未找到ID为 {user_id} 的用户")
            return user
        except Error as e:
            print(f"查询失败: {e}")
    
    # UPDATE - 更新数据
    def update_user(self, user_id, name=None, email=None, age=None):
        """更新用户信息"""
        try:
            cursor = self.connection.cursor()
            
            # 构建动态更新语句
            update_fields = []
            values = []
            
            if name:
                update_fields.append("name = %s")
                values.append(name)
            if email:
                update_fields.append("email = %s")
                values.append(email)
            if age is not None:
                update_fields.append("age = %s")
                values.append(age)
            
            if update_fields:
                values.append(user_id)
                update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_query, values)
                self.connection.commit()
                print(f"用户ID {user_id} 更新成功！")
            else:
                print("没有提供更新字段")
        except Error as e:
            print(f"更新失败: {e}")
    
    # DELETE - 删除数据
    def delete_user(self, user_id):
        """删除用户"""
        try:
            cursor = self.connection.cursor()
            delete_query = "DELETE FROM users WHERE id = %s"
            cursor.execute(delete_query, (user_id,))
            self.connection.commit()
            print(f"用户ID {user_id} 删除成功！")
        except Error as e:
            print(f"删除失败: {e}")
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")

# 使用示例
def main():
    # 创建CRUD实例
    db = MySqlClient()
    
    # 创建表
    db.create_table()
    
    # CREATE - 插入数据
    print("\n=== 插入数据 ===")
    db.create_user("张三", "zhangsan@email.com", 25)
    db.create_user("李四", "lisi@email.com", 30)
    db.create_user("王五", "wangwu@email.com", 28)
    
    # READ - 查询数据
    print("\n=== 查询所有数据 ===")
    db.read_users()
    
    print("\n=== 根据ID查询 ===")
    db.read_user_by_id(1)
    
    # UPDATE - 更新数据
    print("\n=== 更新数据 ===")
    db.update_user(1, name="张三丰", age=35)
    db.read_users()
    
    # DELETE - 删除数据
    print("\n=== 删除数据 ===")
    db.delete_user(2)
    db.read_users()
    
    # 关闭连接
    db.close_connection()

if __name__ == "__main__":
    main()

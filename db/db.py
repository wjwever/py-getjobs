from typing import Collection, List, Dict, Any, Optional
import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    """数据库管理器 - 简洁易用的数据库操作类"""
    
    # 单例模式实现
    _instance = None
    
    def __new__(cls):
        """重写__new__方法实现单例模式"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.connection = None
            cls._instance.connect()
        return cls._instance
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='py_getjobs',
                charset='utf8mb4'
            )
            print("✅ 数据库连接成功！")
        except Error as e:
            print(f"❌ 连接失败: {e}")
    
    def create_tables(self):
        """创建数据表"""
        self.create_jobs_table()
        self.create_posts_table()
    
    def create_jobs_table(self):
        """创建职位信息表"""
        try:
            cursor = self.connection.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_name VARCHAR(255),
                job_desc TEXT,
                skills TEXT,
                key_word VARCHAR(255),
                job_salary VARCHAR(100),
                tag_list TEXT,
                boss_name VARCHAR(255),
                boss_company VARCHAR(255),
                company_location VARCHAR(255),
                boss_title VARCHAR(255),
                boss_active VARCHAR(100),
                job_detail_url VARCHAR(500) UNIQUE,
                referer VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            print("✅ 职位信息表创建成功！")
        except Error as e:
            print(f"❌ 创建职位表失败: {e}")
    
    def create_posts_table(self):
        """创建投递记录表"""
        try:
            cursor = self.connection.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_id INT,
                status VARCHAR(50),
                ai_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
            )
            """
            cursor.execute(create_table_query)
            print("✅ 投递记录表创建成功！")
        except Error as e:
            print(f"❌ 创建投递记录表失败: {e}")

    # ========== 职位表操作 ==========
    
    def add_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """添加职位信息"""
        try:
            cursor = self.connection.cursor()
            insert_query = """
            INSERT INTO jobs (
                job_name, job_desc, skills, key_word, job_salary, tag_list,
                boss_name, boss_company, company_location, boss_title, 
                boss_active, job_detail_url, referer
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                job_data.get('job_name', ''),           #card
                job_data.get('job_desc', ''),
                job_data.get('skills', ''),
                job_data.get('key_word', ''),           #card
                job_data.get('job_salary', ''),         #card
                job_data.get('tag_list', ''),           #card
                job_data.get('boss_name', ''),
                job_data.get('boss_company', ''),       #card
                job_data.get('company_location', ''),   #card
                job_data.get('boss_title', ''),
                job_data.get('boss_active', ''),
                job_data.get('job_detail_url', ''),     #card
                job_data.get('referer', '')             #card
            )
            
            cursor.execute(insert_query, values)
            self.connection.commit()
            job_id = cursor.lastrowid
            print(f"✅ 职位 '{job_data.get('job_name', '')}' 添加成功！ID: {job_id}")
            return job_id
        except Error as e:
            if "Duplicate entry" in str(e):
                print(f"⚠️ 职位已存在: {job_data.get('job_detail_url', '')}")
            else:
                print(f"❌ 添加职位失败: {e}")
            return None
    
    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"❌ 获取职位失败: {e}")
            return None
    
    def get_job_by_url(self, job_detail_url: str) -> Optional[Dict[str, Any]]:
        """根据URL获取职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE job_detail_url = %s", (job_detail_url,))
            return cursor.fetchone()
        except Error as e:
            print(f"❌ 获取职位失败: {e}")
            return None
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """获取所有职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            return cursor.fetchall()
        except Error as e:
            print(f"❌ 获取职位列表失败: {e}")
            return []
    
    def search_jobs(self, keyword: str, field: str = "job_name") -> List[Dict[str, Any]]:
        """搜索职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = f"SELECT * FROM jobs WHERE {field} LIKE %s ORDER BY created_at DESC"
            cursor.execute(query, (f"%{keyword}%",))
            return cursor.fetchall()
        except Error as e:
            print(f"❌ 搜索职位失败: {e}")
            return []
    
    def search_jobs_by_field_value(self, field: str, value: str) -> List[Dict[str, Any]]:
        """精准搜索职位信息 - 根据指定字段和值进行精确匹配
        
        Args:
            field: 要搜索的字段名
            value: 要搜索的值
            
        Returns:
            匹配的职位列表
        """
        try:
            # 验证字段名是否有效，防止SQL注入
            valid_fields = [
                'job_name', 'job_desc', 'skills', 'key_word', 'job_salary', 
                'tag_list', 'boss_name', 'boss_company', 'company_location', 
                'boss_title', 'boss_active', 'job_detail_url', 'referer'
            ]
            
            if field not in valid_fields:
                print(f"❌ 无效的字段名: {field}")
                return []
            
            cursor = self.connection.cursor(dictionary=True)
            
            if value == "":
                # 搜索空值
                query = f"SELECT * FROM jobs WHERE {field} IS NULL OR {field} = '' ORDER BY created_at DESC"
                cursor.execute(query)
            else:
                # 精确匹配非空值
                query = f"SELECT * FROM jobs WHERE {field} = %s ORDER BY created_at DESC"
                cursor.execute(query, (value,))
            
            results = cursor.fetchall()
            print(f"✅ 在字段 '{field}' 中搜索值 '{value}'，找到 {len(results)} 个匹配职位")
            return results
            
        except Error as e:
            print(f"❌ 精准搜索职位失败: {e}")
            return []

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> bool:
        """更新职位信息"""
        try:
            cursor = self.connection.cursor()
            
            update_fields = []
            values = []
            
            valid_fields = [
                'job_name', 'job_desc', 'skills', 'key_word', 'job_salary', 
                'tag_list', 'boss_name', 'boss_company', 'company_location', 
                'boss_title', 'boss_active', 'referer'
            ]
            
            for field in valid_fields:
                if field in update_data:
                    update_fields.append(f"{field} = %s")
                    values.append(update_data[field])
            
            if update_fields:
                values.append(job_id)
                update_query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_query, values)
                self.connection.commit()
                print(f"✅ 职位ID {job_id} 更新成功！")
                return True
            return False
        except Error as e:
            print(f"❌ 更新职位失败: {e}")
            return False
    
    def delete_job(self, job_id: int) -> bool:
        """删除职位信息"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
            self.connection.commit()
            print(f"✅ 职位ID {job_id} 删除成功！")
            return True
        except Error as e:
            print(f"❌ 删除职位失败: {e}")
            return False

    # ========== 投递记录表操作 ==========
    
    def add_post_record(self, job_id: int, status: str, ai_result: str = "") -> Optional[int]:
        """添加投递记录，如果job_id已存在则更新记录"""
        try:
            cursor = self.connection.cursor()
            
            # 先检查是否已存在该job_id的记录
            cursor.execute("SELECT id FROM posts WHERE job_id = %s", (job_id,))
            existing_record = cursor.fetchall()
            
            if existing_record:
                # 如果记录已存在，则更新
                update_query = """
                UPDATE posts 
                SET status = %s, ai_result = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE job_id = %s
                """
                cursor.execute(update_query, (status, ai_result, job_id))
                self.connection.commit()
                post_id = existing_record[0]  # 使用已存在的记录ID
                print(f"✅ 投递记录已更新！职位ID: {job_id}, 状态: {status}")
            else:
                # 如果记录不存在，则插入新记录
                insert_query = """
                INSERT INTO posts (job_id, status, ai_result) VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (job_id, status, ai_result))
                self.connection.commit()
                post_id = cursor.lastrowid
                print(f"✅ 投递记录添加成功！职位ID: {job_id}, 状态: {status}")
            
            return post_id
        except Error as e:
            print(f"❌ 处理投递记录失败: {e}")
            return None
    
    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取投递记录"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
            return cursor.fetchone()
        except Error as e:
            print(f"❌ 获取投递记录失败: {e}")
            return None
    
    def get_posts_by_job_id(self, job_id: int) -> List[Dict[str, Any]]:
        """根据职位ID获取投递记录"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM posts WHERE job_id = %s ORDER BY created_at DESC", (job_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"❌ 获取投递记录失败: {e}")
            return []
    
    def get_all_posts(self) -> List[Dict[str, Any]]:
        """获取所有投递记录"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.*, j.job_name, j.boss_company 
                FROM posts p 
                LEFT JOIN jobs j ON p.job_id = j.id 
                ORDER BY p.created_at DESC
            """)
            return cursor.fetchall()
        except Error as e:
            print(f"❌ 获取投递记录失败: {e}")
            return []
    
    def update_post_status(self, post_id: int, status: str) -> bool:
        """更新投递状态"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE posts SET status = %s WHERE id = %s", (status, post_id))
            self.connection.commit()
            print(f"✅ 投递记录ID {post_id} 状态更新为: {status}")
            return True
        except Error as e:
            print(f"❌ 更新投递状态失败: {e}")
            return False
    
    def get_jobs_by_post_status(self, status: str) -> List[Dict[str, Any]]:
        """根据投递状态查找所有职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT j.*, p.status, p.created_at as post_created_at, p.updated_at as post_updated_at
                FROM jobs j
                INNER JOIN posts p ON j.id = p.job_id
                WHERE p.status = %s
                ORDER BY p.updated_at DESC
            """, (status,))
            return cursor.fetchall()
        except Error as e:
            print(f"❌ 根据投递状态查找职位失败: {e}")
            return []

    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """获取活跃职位 - 在posts表中没有记录的职位"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT j.* 
                FROM jobs j 
                LEFT JOIN posts p ON j.id = p.job_id 
                WHERE p.job_id IS NULL 
                ORDER BY j.created_at DESC
            """)
            active_jobs = cursor.fetchall()
            print(f"✅ 找到 {len(active_jobs)} 个活跃职位")
            return active_jobs
        except Error as e:
            print(f"❌ 获取活跃职位失败: {e}")
            return []

    def get_error_status_jobs(self) -> List[Dict[str, Any]]:
        """获取活跃职位 - 在posts表中没有记录的职位"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT j.* 
                FROM jobs j 
                LEFT JOIN posts p ON j.id = p.job_id 
                WHERE p.status = "closed"
                ORDER BY j.created_at DESC
            """)
            jobs = cursor.fetchall()
            print(f"✅ 找到 {len(jobs)} 个活跃职位")
            return jobs
        except Error as e:
            print(f"❌ 获取活跃职位失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            cursor = self.connection.cursor()
            
            # 职位统计
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = cursor.fetchone()[0]
            
            # 投递统计
            cursor.execute("SELECT COUNT(*) FROM posts")
            total_posts = cursor.fetchone()[0]
            
            # 状态统计
            cursor.execute("SELECT status, COUNT(*) FROM posts GROUP BY status")
            status_stats = {status: count for status, count in cursor.fetchall()}
            
            return {
                'total_jobs': total_jobs,
                'total_posts': total_posts,
                'status_stats': status_stats
            }
        except Error as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {'total_jobs': 0, 'total_posts': 0, 'status_stats': {}}
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("✅ 数据库连接已关闭")

# 使用示例
if __name__ == "__main__":
    # 创建数据库管理器（单例模式）
    db = DatabaseManager()
    
    # 测试单例模式
    db2 = DatabaseManager()
    print(f"db和db2是同一个实例吗？ {db is db2}")
    
    # 创建数据表
    db.create_tables()
    db.add_post_record(203, "post_error")
    
    # # 示例1: 添加职位信息
    # print("\n=== 添加职位信息 ===")
    # job_data = {
    #     "job_name": "Python开发工程师",
    #     "job_desc": "负责Python后端开发，使用Django/Flask框架",
    #     "skills": "Python, Django, Flask, MySQL",
    #     "key_word": "Python",
    #     "job_salary": "15-25K",
    #     "tag_list": "Python,后端开发",
    #     "boss_name": "张经理",
    #     "boss_company": "阿里巴巴",
    #     "company_location": "杭州",
    #     "boss_title": "招聘经理",
    #     "boss_active": "3天内活跃",
    #     "job_detail_url": "https://www.zhipin.com/job1",
    #     "referer": "https://www.zhipin.com"
    # }
    #
    # job_id = db.add_job(job_data)
    #
    # # 示例2: 添加投递记录
    # if job_id:
    #     print("\n=== 添加投递记录 ===")
    #     post_id = db.add_post_record(job_id, "已投递", "AI分析通过")
    #
    # # 示例3: 查询职位信息
    # print("\n=== 查询职位信息 ===")
    # job = db.get_job_by_id(job_id)
    # if job:
    #     print(f"职位名称: {job['job_name']}")
    #     print(f"公司: {job['boss_company']}")
    #     print(f"薪资: {job['job_salary']}")
    #
    # # 示例4: 查询投递记录
    # print("\n=== 查询投递记录 ===")
    # posts = db.get_posts_by_job_id(job_id)
    # for post in posts:
    #     print(f"投递状态: {post['status']}, AI结果: {post['ai_result']}")
    #     print(f"创建时间: {post['created_at']}, 更新时间: {post['updated_at']}")
    #
    # # 示例5: 根据投递状态查找职位
    # print("\n=== 根据投递状态查找职位 ===")
    # jobs_with_status = db.get_jobs_by_post_status("已投递")
    # for job in jobs_with_status:
    #     print(f"职位: {job['job_name']}, 公司: {job['boss_company']}, 投递状态: {job['status']}")
    #
    # # 示例6: 获取统计信息
    # print("\n=== 统计信息 ===")
    # stats = db.get_statistics()
    # print(f"总职位数: {stats['total_jobs']}")
    # print(f"总投递数: {stats['total_posts']}")
    # print(f"状态统计: {stats['status_stats']}")
    
    # 关闭连接
    db.close()

from typing import Collection, List, Dict, Any, Optional
import mysql.connector
from mysql.connector import Error

class MySqlClient:
    # 类变量，用于存储唯一的实例
    _instance = None
    
    def __new__(cls):
        """重写__new__方法实现单例模式"""
        if cls._instance is None:
            # 如果是第一次创建实例，调用父类的__new__方法
            cls._instance = super(MySqlClient, cls).__new__(cls)
            # 初始化连接
            cls._instance.connection = None
            cls._instance.connect()
        # 返回已经存在的实例
        return cls._instance
        
    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',       # 数据库地址
                user='root',            # 用户名
                password='root',        # 密码
                database='get_jobs',     # 数据库名
                charset='utf8mb4'
            )
            print("MySQL数据库连接成功！")
        except Error as e:
            print(f"连接失败: {e}")
    
    def create_jobs_table(self):
        """创建职位信息数据表"""
        try:
            cursor = self.connection.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_name VARCHAR(100) NOT NULL,
                job_salary VARCHAR(50),
                job_desc TEXT,
                job_status VARCHAR(20) DEFAULT 'active',
                key_word VARCHAR(100),
                tag_list TEXT,
                boss_company VARCHAR(100),
                company_location VARCHAR(100),
                job_detail_url VARCHAR(500) UNIQUE,
                referer VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            print("职位信息数据表创建成功！")
        except Error as e:
            print(f"创建职位表失败: {e}")
    
    # CREATE - 插入职位数据
    def create_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """插入新职位信息"""
        try:
            cursor = self.connection.cursor()
            insert_query = """
            INSERT INTO jobs (job_name, job_salary, job_desc, job_status, key_word, tag_list, boss_company, company_location, job_detail_url, referer) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # 准备数据
            values = (
                job_data.get('job_name', ''),
                job_data.get('job_salary', ''),
                job_data.get('job_desc', ''),
                job_data.get('job_status', 'active'),  # 默认状态为active
                job_data.get('key_word', ''),
                job_data.get('tag_list', ''),
                job_data.get('boss_company', ''),
                job_data.get('company_location', ''),
                job_data.get('job_detail_url', ''),
                job_data.get('referer', '')
            )
            
            cursor.execute(insert_query, values)
            self.connection.commit()
            job_id = cursor.lastrowid
            print(f"职位 {job_data.get('job_name', '')} 插入成功！ID: {job_id}")
            return job_id
        except Error as e:
            if "Duplicate entry" in str(e):
                print(f"职位已存在: {job_data.get('job_detail_url', '')}")
            else:
                print(f"插入职位失败: {e}")
            return None
    
    def create_jobs_batch(self, jobs_data: List[Dict[str, Any]]) -> List[int]:
        """批量插入职位信息"""
        inserted_ids = []
        for job_data in jobs_data:
            job_id = self.create_job(job_data)
            if job_id:
                inserted_ids.append(job_id)
        return inserted_ids
    
    # READ - 查询职位数据
    def read_all_jobs(self) -> List[Dict[str, Any]]:
        """查询所有职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            jobs = cursor.fetchall()
            
            print(f"\n所有职位信息 (共{len(jobs)}条):")
            for job in jobs:
                print(f"ID: {job['id']}, 职位: {job['job_name']}, 关键词: {job['key_word']}, 薪资: {job['job_salary']}, 状态: {job['job_status']}, 公司: {job['boss_company']}")
            return jobs
        except Error as e:
            print(f"查询职位失败: {e}")
            return []
    
    def read_jobs_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态查询职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE job_status = %s ORDER BY created_at DESC", (status,))
            jobs = cursor.fetchall()
            
            print(f"\n状态为 '{status}' 的职位信息 (共{len(jobs)}条):")
            for job in jobs:
                print(f"ID: {job['id']}, 职位: {job['job_name']}, 关键词: {job['key_word']}, 薪资: {job['job_salary']}, 公司: {job['boss_company']}")
            return jobs
        except Error as e:
            print(f"查询职位失败: {e}")
            return []
    
    def read_jobs_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """根据关键词查询职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE key_word = %s ORDER BY created_at DESC", (keyword,))
            jobs = cursor.fetchall()
            
            print(f"\n关键词为 '{keyword}' 的职位信息 (共{len(jobs)}条):")
            for job in jobs:
                print(f"ID: {job['id']}, 职位: {job['job_name']}, 薪资: {job['job_salary']}, 状态: {job['job_status']}, 公司: {job['boss_company']}")
            return jobs
        except Error as e:
            print(f"查询职位失败: {e}")
            return []
    
    def read_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """根据ID查询职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            
            if job:
                print(f"\n找到职位: ID: {job['id']}, 职位: {job['job_name']}, 关键词: {job['key_word']}, 薪资: {job['job_salary']}, 状态: {job['job_status']}")
            else:
                print(f"未找到ID为 {job_id} 的职位")
            return job
        except Error as e:
            print(f"查询职位失败: {e}")
            return None
    
    def read_job_by_url(self, job_detail_url: str) -> Optional[Dict[str, Any]]:
        """根据职位详情URL查询职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE job_detail_url = %s", (job_detail_url,))
            job = cursor.fetchone()
            
            if job:
                print(f"职位已存在: {job['job_name']} (关键词: {job['key_word']}, 状态: {job['job_status']})")
            return job
        except Error as e:
            print(f"查询职位失败: {e}")
            return None
    
    def search_jobs(self, keyword: str, field: str = "job_name") -> List[Dict[str, Any]]:
        """根据关键词搜索职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            search_query = f"SELECT * FROM jobs WHERE {field} LIKE %s ORDER BY created_at DESC"
            cursor.execute(search_query, (f"%{keyword}%",))
            jobs = cursor.fetchall()
            
            print(f"\n搜索到 {len(jobs)} 条包含 '{keyword}' 的职位:")
            for job in jobs:
                print(f"ID: {job['id']}, 职位: {job['job_name']}, 关键词: {job['key_word']}, 薪资: {job['job_salary']}, 状态: {job['job_status']}, 公司: {job['boss_company']}")
            return jobs
        except Error as e:
            print(f"搜索职位失败: {e}")
            return []
    
    def get_keywords_statistics(self) -> Dict[str, int]:
        """获取关键词统计信息"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT key_word, COUNT(*) FROM jobs WHERE key_word IS NOT NULL AND key_word != '' GROUP BY key_word ORDER BY COUNT(*) DESC")
            keyword_stats = {}
            for keyword, count in cursor.fetchall():
                keyword_stats[keyword] = count
            
            print(f"\n关键词统计信息:")
            for keyword, count in keyword_stats.items():
                print(f"关键词 '{keyword}': {count} 个职位")
            
            return keyword_stats
        except Error as e:
            print(f"获取关键词统计信息失败: {e}")
            return {}
    
    # UPDATE - 更新职位数据
    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> bool:
        """更新职位信息"""
        try:
            cursor = self.connection.cursor()
            
            # 构建动态更新语句
            update_fields = []
            values = []
            
            valid_fields = ['job_name', 'job_salary', 'job_desc', 'job_status', 'key_word', 'tag_list', 'boss_company', 'company_location', 'referer']
            
            for field in valid_fields:
                if field in update_data:
                    update_fields.append(f"{field} = %s")
                    values.append(update_data[field])
            
            if update_fields:
                values.append(job_id)
                update_query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_query, values)
                self.connection.commit()
                print(f"职位ID {job_id} 更新成功！")
                return True
            else:
                print("没有提供有效的更新字段")
                return False
        except Error as e:
            print(f"更新职位失败: {e}")
            return False
    
    def update_job_status(self, job_id: int, status: str) -> bool:
        """更新职位状态"""
        try:
            cursor = self.connection.cursor()
            update_query = "UPDATE jobs SET job_status = %s WHERE id = %s"
            cursor.execute(update_query, (status, job_id))
            self.connection.commit()
            print(f"职位ID {job_id} 状态更新为: {status}")
            return True
        except Error as e:
            print(f"更新职位状态失败: {e}")
            return False
    
    def update_job_description(self, job_id: int, description: str) -> bool:
        """更新职位描述"""
        try:
            cursor = self.connection.cursor()
            update_query = "UPDATE jobs SET job_desc = %s WHERE id = %s"
            cursor.execute(update_query, (description, job_id))
            self.connection.commit()
            print(f"职位ID {job_id} 描述已更新")
            return True
        except Error as e:
            print(f"更新职位描述失败: {e}")
            return False
    
    def update_job_keyword(self, job_id: int, keyword: str) -> bool:
        """更新职位关键词"""
        try:
            cursor = self.connection.cursor()
            update_query = "UPDATE jobs SET key_word = %s WHERE id = %s"
            cursor.execute(update_query, (keyword, job_id))
            self.connection.commit()
            print(f"职位ID {job_id} 关键词更新为: {keyword}")
            return True
        except Error as e:
            print(f"更新职位关键词失败: {e}")
            return False
    
    # DELETE - 删除职位数据
    def delete_job(self, job_id: int) -> bool:
        """删除职位信息"""
        try:
            cursor = self.connection.cursor()
            delete_query = "DELETE FROM jobs WHERE id = %s"
            cursor.execute(delete_query, (job_id,))
            self.connection.commit()
            print(f"职位ID {job_id} 删除成功！")
            return True
        except Error as e:
            print(f"删除职位失败: {e}")
            return False
    
    def delete_job_by_url(self, job_detail_url: str) -> bool:
        """根据职位详情URL删除职位信息"""
        try:
            cursor = self.connection.cursor()
            delete_query = "DELETE FROM jobs WHERE job_detail_url = %s"
            cursor.execute(delete_query, (job_detail_url,))
            self.connection.commit()
            print(f"职位URL {job_detail_url} 删除成功！")
            return True
        except Error as e:
            print(f"删除职位失败: {e}")
            return False
    
    def delete_jobs_by_keyword(self, keyword: str) -> int:
        """根据关键词删除职位信息"""
        try:
            cursor = self.connection.cursor()
            delete_query = "DELETE FROM jobs WHERE key_word = %s"
            cursor.execute(delete_query, (keyword,))
            deleted_count = cursor.rowcount
            self.connection.commit()
            print(f"删除了 {deleted_count} 个关键词为 '{keyword}' 的职位")
            return deleted_count
        except Error as e:
            print(f"删除职位失败: {e}")
            return 0
    
    def get_jobs_count(self) -> int:
        """获取职位总数"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs")
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"获取职位总数失败: {e}")
            return 0
    
    def get_jobs_count_by_status(self, status: str) -> int:
        """根据状态获取职位数量"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_status = %s", (status,))
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"获取状态为 '{status}' 的职位数量失败: {e}")
            return 0
    
    def get_jobs_count_by_keyword(self, keyword: str) -> int:
        """根据关键词获取职位数量"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM jobs WHERE key_word = %s", (keyword,))
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"获取关键词为 '{keyword}' 的职位数量失败: {e}")
            return 0
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近添加的职位信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s", (limit,))
            jobs = cursor.fetchall()
            return jobs
        except Error as e:
            print(f"获取最近职位失败: {e}")
            return []
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """获取职位统计信息"""
        try:
            cursor = self.connection.cursor()
            
            # 获取各种状态的职位数量
            status_counts = {}
            cursor.execute("SELECT job_status, COUNT(*) FROM jobs GROUP BY job_status")
            for status, count in cursor.fetchall():
                status_counts[status] = count
            
            # 获取关键词统计
            keyword_stats = self.get_keywords_statistics()
            
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM jobs")
            total_count = cursor.fetchone()[0]
            
            statistics = {
                'total': total_count,
                'by_status': status_counts,
                'by_keyword': keyword_stats
            }
            
            print(f"\n职位统计信息:")
            print(f"总职位数: {total_count}")
            for status, count in status_counts.items():
                print(f"状态 '{status}': {count} 个职位")
            
            return statistics
        except Error as e:
            print(f"获取职位统计信息失败: {e}")
            return {'total': 0, 'by_status': {}, 'by_keyword': {}}
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")
    
    # 删除职位表
    def drop_jobs_table(self):
        """删除职位信息数据表"""
        try:
            cursor = self.connection.cursor()
            drop_query = "DROP TABLE IF EXISTS jobs"
            cursor.execute(drop_query)
            self.connection.commit()
            print("职位信息数据表已删除！")
        except Error as e:
            print(f"删除职位表失败: {e}")
    
    # 清空职位数据
    def truncate_jobs(self):
        """清空职位信息数据"""
        try:
            cursor = self.connection.cursor()
            truncate_query = "TRUNCATE TABLE jobs"
            cursor.execute(truncate_query)
            self.connection.commit()
            print("职位信息数据表已清空")
        except Error as e:
            print(f"清空职位表失败: {e}")

# 使用示例
if __name__ == "__main__":
    # 创建数据库客户端实例
    db = MySqlClient()
    
    # 创建职位信息表
    db.create_jobs_table()
    
    # 测试单例模式
    db2 = MySqlClient()
    print(f"db和db2是同一个实例吗？ {db is db2}")
    
    # CREATE - 插入职位数据
    print("\n=== 插入职位数据 ===")
    job_data_1 = {
        "job_name": "Python开发工程师",
        "job_salary": "15-25K",
        "job_desc": "负责Python后端开发，使用Django/Flask框架",
        "job_status": "active",
        "tag_list": "Python, Django, Flask",
        "boss_company": "阿里巴巴",
        "company_location": "杭州",
        "job_detail_url": "https://www.zhipin.com/job1",
        "referer": "https://www.zhipin.com"
    }
    
    job_data_2 = {
        "job_name": "Java开发工程师",
        "job_salary": "20-30K",
        "job_desc": "负责Java后端开发，使用Spring框架",
        "job_status": "active",
        "tag_list": "Java, Spring, MySQL",
        "boss_company": "腾讯",
        "company_location": "深圳",
        "job_detail_url": "https://www.zhipin.com/job2",
        "referer": "https://www.zhipin.com"
    }
    
    job_data_3 = {
        "job_name": "前端开发工程师",
        "job_salary": "18-28K",
        "job_desc": "负责前端开发，使用Vue/React框架",
        "job_status": "inactive",
        "tag_list": "Vue, React, JavaScript",
        "boss_company": "字节跳动",
        "company_location": "北京",
        "job_detail_url": "https://www.zhipin.com/job3",
        "referer": "https://www.zhipin.com"
    }
    
    job_id_1 = db.create_job(job_data_1)
    job_id_2 = db.create_job(job_data_2)
    job_id_3 = db.create_job(job_data_3)
    
    # 测试重复插入（应该不会插入重复的URL）
    db.create_job(job_data_1)
    
    # READ - 查询职位数据
    print("\n=== 查询所有职位数据 ===")
    jobs = db.read_all_jobs()
    
    print("\n=== 根据状态查询职位 ===")
    active_jobs = db.read_jobs_by_status("active")
    inactive_jobs = db.read_jobs_by_status("inactive")
    
    print("\n=== 根据关键词查询职位 ===")
    python_jobs = db.read_jobs_by_keyword("Python")
    java_jobs = db.read_jobs_by_keyword("Java")
    
    print("\n=== 根据ID查询 ===")
    if job_id_1:
        db.read_job_by_id(job_id_1)
    
    print("\n=== 根据URL查询 ===")
    db.read_job_by_url("https://www.zhipin.com/job1")
    
    print("\n=== 搜索职位 ===")
    db.search_jobs("Python")
    
    # UPDATE - 更新职位数据
    print("\n=== 更新职位数据 ===")
    if job_id_1:
        update_data = {
            "job_salary": "18-28K",
            "job_desc": "负责Python后端开发，使用Django/Flask框架，有AI项目经验优先",
            "tag_list": "Python, Django, Flask, FastAPI"
        }
        db.update_job(job_id_1, update_data)
        db.read_job_by_id(job_id_1)
    
    print("\n=== 更新职位状态 ===")
    if job_id_2:
        db.update_job_status(job_id_2, "applied")
        db.read_job_by_id(job_id_2)
    
    print("\n=== 更新职位描述 ===")
    if job_id_3:
        db.update_job_description(job_id_3, "负责前端开发，使用Vue/React框架，有移动端开发经验优先")
        db.read_job_by_id(job_id_3)
    
    print("\n=== 更新职位关键词 ===")
    if job_id_3:
        db.update_job_keyword(job_id_3, "前端开发")
        db.read_job_by_id(job_id_3)
    
    # 获取统计信息
    print(f"\n=== 统计信息 ===")
    count = db.get_jobs_count()
    print(f"职位总数: {count}")
    
    active_count = db.get_jobs_count_by_status("active")
    print(f"活跃职位数: {active_count}")
    
    python_count = db.get_jobs_count_by_keyword("Python")
    print(f"Python相关职位数: {python_count}")
    
    statistics = db.get_job_statistics()
    
    keyword_stats = db.get_keywords_statistics()
    
    recent_jobs = db.get_recent_jobs(5)
    print(f"最近5个职位: {len(recent_jobs)}")
    
    # DELETE - 删除职位数据
    print("\n=== 删除职位数据 ===")
    if job_id_2:
        db.delete_job(job_id_2)
    
    print("\n=== 根据关键词删除职位 ===")
    deleted_count = db.delete_jobs_by_keyword("前端")
    print(f"删除了 {deleted_count} 个前端相关职位")
    
    # 重新查询确认删除
    jobs_after_delete = db.read_all_jobs()
    print(f"删除后剩余职位数: {len(jobs_after_delete)}")
    
    # 关闭连接
    db.close_connection()

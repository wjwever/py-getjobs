import os
import sqlite3
from typing import List, Dict, Any, Optional

import pymysql
from pymysql import Error as MySQLError

from util.logger import logger
from boss.boss_config import load_mysql_config, load_sqlite_config


# ========== SQLite 适配层 ==========

class _SQLiteCursor:
    """将 sqlite3 cursor 包装成和 pymysql DictCursor 相同的接口"""

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def execute(self, query: str, args=None):
        # pymysql 使用 %s 占位符，sqlite3 使用 ?
        sqlite_query = query.replace('%s', '?')
        if args is not None:
            self._cursor.execute(sqlite_query, args)
        else:
            self._cursor.execute(sqlite_query)

    def fetchone(self) -> Optional[Dict[str, Any]]:
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self) -> List[Dict[str, Any]]:
        return [dict(row) for row in self._cursor.fetchall()]

    @property
    def lastrowid(self) -> Optional[int]:
        return self._cursor.lastrowid


class _SQLiteConnection:
    """将 sqlite3 connection 包装成和 pymysql connection 相同的接口"""

    def __init__(self, conn: sqlite3.Connection):
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        self._conn = conn

    def cursor(self) -> _SQLiteCursor:
        return _SQLiteCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


# ========== DatabaseManager ==========

class DatabaseManager:
    """数据库管理器 - 支持 MySQL / SQLite 双后端，对外接口统一"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.connection = None
            cls._instance._is_sqlite = False
            cls._instance.connect()
        return cls._instance

    def connect(self):
        """根据配置连接 MySQL 或 SQLite"""
        mysql_config = load_mysql_config()

        if not mysql_config.enable:
            self._connect_sqlite()
        else:
            self._connect_mysql(mysql_config)

    def _connect_sqlite(self):
        """连接 SQLite 数据库"""
        sqlite_config = load_sqlite_config()
        db_path = sqlite_config.path
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        try:
            raw_conn = sqlite3.connect(db_path, check_same_thread=False)
            self.connection = _SQLiteConnection(raw_conn)
            self._is_sqlite = True
            logger.info(f"SQLite 数据库连接成功: {db_path}")
        except sqlite3.Error as e:
            logger.error(f"SQLite 连接失败: {e}")
            raise

    def _connect_mysql(self, config):
        """连接 MySQL 数据库"""
        try:
            # 先连接服务器，检查并创建数据库
            temp_conn = pymysql.connect(
                host=config.host,
                user=config.user,
                password=config.password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            cursor = temp_conn.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{config.database}'")
            if not cursor.fetchone():
                logger.info(f"数据库 '{config.database}' 不存在，正在创建...")
                cursor.execute(
                    f"CREATE DATABASE `{config.database}` "
                    f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                logger.info(f"数据库 '{config.database}' 创建成功！")
            cursor.close()
            temp_conn.close()

            # 连接到具体数据库
            self.connection = pymysql.connect(
                host=config.host,
                user=config.user,
                password=config.password,
                database=config.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            self._is_sqlite = False
            logger.info("MySQL 数据库连接成功！")
        except MySQLError as e:
            logger.error(f"MySQL 连接失败: {e}")
            raise

    # ========== 建表 ==========

    def _add_column_if_not_exists(self, cursor, table: str, column: str, col_def: str):
        """如果指定列不存在，则为表添加该列"""
        try:
            if self._is_sqlite:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row['name'] for row in cursor.fetchall()]
            else:
                cursor.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_NAME = %s AND COLUMN_NAME = %s",
                    (table, column)
                )
                columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                logger.info(f"已为表 {table} 添加列 {column}")
        except (MySQLError, sqlite3.Error) as e:
            logger.warning(f"检查/添加列 {column} 失败: {e}")

    def _migrate_jobs_column_order(self, cursor):
        """迁移 jobs 表列顺序，使 job_type, boss_company, boss_active 排在 id 之后"""
        expected_order = [
            'id', 'job_type', 'boss_company', 'boss_active',
            'job_name', 'job_desc', 'skills', 'key_word', 'job_salary',
            'tag_list', 'boss_name', 'company_location', 'boss_title',
            'job_detail_url', 'referer', 'created_at', 'updated_at'
        ]
        try:
            if self._is_sqlite:
                cursor.execute("PRAGMA table_info(jobs)")
                current_order = [row['name'] for row in cursor.fetchall()]
                if current_order == expected_order:
                    return
                # 只有当表存在且列顺序不一致时才迁移
                if not current_order:
                    return
                logger.info("检测到 jobs 表列顺序需要调整，开始迁移...")
                cols = ', '.join(expected_order)
                cursor.execute(f"CREATE TABLE jobs_new AS SELECT {cols} FROM jobs")
                cursor.execute("DROP TABLE jobs")
                cursor.execute(f"""
                    CREATE TABLE jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_type VARCHAR(50) DEFAULT '不限',
                        boss_company VARCHAR(255),
                        boss_active VARCHAR(100),
                        job_name VARCHAR(255),
                        job_desc TEXT,
                        skills TEXT,
                        key_word VARCHAR(255),
                        job_salary VARCHAR(100),
                        tag_list TEXT,
                        boss_name VARCHAR(255),
                        company_location VARCHAR(255),
                        boss_title VARCHAR(255),
                        job_detail_url VARCHAR(500) UNIQUE,
                        referer VARCHAR(500),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute(f"INSERT INTO jobs ({cols}) SELECT {cols} FROM jobs_new")
                cursor.execute("DROP TABLE jobs_new")
                logger.info("jobs 表列顺序迁移完成")
            else:
                cursor.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_NAME = 'jobs' ORDER BY ORDINAL_POSITION"
                )
                current_order = [row['COLUMN_NAME'] for row in cursor.fetchall()]
                if current_order == expected_order:
                    return
                if not current_order:
                    return
                logger.info("检测到 jobs 表列顺序需要调整，开始迁移...")
                cursor.execute("ALTER TABLE jobs MODIFY COLUMN job_type VARCHAR(50) DEFAULT '不限' AFTER id")
                cursor.execute("ALTER TABLE jobs MODIFY COLUMN boss_company VARCHAR(255) AFTER job_type")
                cursor.execute("ALTER TABLE jobs MODIFY COLUMN boss_active VARCHAR(100) AFTER boss_company")
                logger.info("jobs 表列顺序迁移完成")
        except (MySQLError, sqlite3.Error) as e:
            logger.warning(f"迁移 jobs 表列顺序失败: {e}")

    def create_tables(self):
        """创建数据表"""
        self.create_jobs_table()
        self.create_posts_table()

    def create_jobs_table(self):
        """创建职位信息表"""
        try:
            with self.connection.cursor() as cursor:
                if self._is_sqlite:
                    ddl = """
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_type VARCHAR(50) DEFAULT '不限',
                        boss_company VARCHAR(255),
                        boss_active VARCHAR(100),
                        job_name VARCHAR(255),
                        job_desc TEXT,
                        skills TEXT,
                        key_word VARCHAR(255),
                        job_salary VARCHAR(100),
                        tag_list TEXT,
                        boss_name VARCHAR(255),
                        company_location VARCHAR(255),
                        boss_title VARCHAR(255),
                        job_detail_url VARCHAR(500) UNIQUE,
                        referer VARCHAR(500),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                else:
                    ddl = """
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        job_type VARCHAR(50) DEFAULT '不限',
                        boss_company VARCHAR(255),
                        boss_active VARCHAR(100),
                        job_name VARCHAR(255),
                        job_desc TEXT,
                        skills TEXT,
                        key_word VARCHAR(255),
                        job_salary VARCHAR(100),
                        tag_list TEXT,
                        boss_name VARCHAR(255),
                        company_location VARCHAR(255),
                        boss_title VARCHAR(255),
                        job_detail_url VARCHAR(500) UNIQUE,
                        referer VARCHAR(500),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                    """
                cursor.execute(ddl)
                # 兼容旧表：如果 job_type 列不存在则自动添加，然后迁移列顺序
                self._add_column_if_not_exists(cursor, 'jobs', 'job_type', "VARCHAR(50) DEFAULT '不限'")
                self._migrate_jobs_column_order(cursor)
                if not self._is_sqlite:
                    self.connection.commit()
                logger.info("职位信息表创建成功！")
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"创建职位表失败: {e}")

    def create_posts_table(self):
        """创建投递记录表"""
        try:
            with self.connection.cursor() as cursor:
                if self._is_sqlite:
                    ddl = """
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INT,
                        status VARCHAR(50),
                        ai_result TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
                    )
                    """
                else:
                    ddl = """
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
                cursor.execute(ddl)
                if not self._is_sqlite:
                    self.connection.commit()
                logger.info("投递记录表创建成功！")
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"创建投递记录表失败: {e}")

    # ========== 职位表操作 ==========

    def add_job(self, job_data: Dict[str, Any]) -> Optional[int]:
        """添加职位信息"""
        try:
            with self.connection.cursor() as cursor:
                insert_query = """
                INSERT INTO jobs (
                    job_type, boss_company, boss_active,
                    job_name, job_desc, skills, key_word, job_salary, tag_list,
                    boss_name, company_location, boss_title,
                    job_detail_url, referer
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    job_data.get('job_type', '不限'),
                    job_data.get('boss_company', ''),
                    job_data.get('boss_active', ''),
                    job_data.get('job_name', ''),
                    job_data.get('job_desc', ''),
                    job_data.get('skills', ''),
                    job_data.get('key_word', ''),
                    job_data.get('job_salary', ''),
                    job_data.get('tag_list', ''),
                    job_data.get('boss_name', ''),
                    job_data.get('company_location', ''),
                    job_data.get('boss_title', ''),
                    job_data.get('job_detail_url', ''),
                    job_data.get('referer', '')
                )
                cursor.execute(insert_query, values)
                self.connection.commit()
                job_id = cursor.lastrowid
                logger.info(f"职位 '{job_data.get('job_name', '')}' 添加成功！ID: {job_id}")
                return job_id
        except (MySQLError, sqlite3.Error) as e:
            if "Duplicate entry" in str(e) or "UNIQUE constraint failed" in str(e):
                logger.warning(f"职位已存在: {job_data.get('job_detail_url', '')}")
            else:
                logger.error(f"添加职位失败: {e}")
            return None

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取职位信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
                return cursor.fetchone()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取职位失败: {e}")
            return None

    def get_job_by_url(self, job_detail_url: str) -> Optional[Dict[str, Any]]:
        """根据URL获取职位信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM jobs WHERE job_detail_url = %s", (job_detail_url,))
                return cursor.fetchone()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取职位失败: {e}")
            return None

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """获取所有职位信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
                return cursor.fetchall()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取职位列表失败: {e}")
            return []

    def search_jobs(self, keyword: str, field: str = "job_name") -> List[Dict[str, Any]]:
        """搜索职位信息"""
        try:
            with self.connection.cursor() as cursor:
                query = f"SELECT * FROM jobs WHERE {field} LIKE %s ORDER BY created_at DESC"
                cursor.execute(query, (f"%{keyword}%",))
                return cursor.fetchall()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"搜索职位失败: {e}")
            return []

    def search_jobs_by_field_value(self, field: str, value: str) -> List[Dict[str, Any]]:
        """精准搜索职位信息 - 根据指定字段和值进行精确匹配"""
        try:
            valid_fields = [
                'job_name', 'job_desc', 'skills', 'key_word', 'job_type', 'job_salary',
                'tag_list', 'boss_name', 'boss_company', 'company_location',
                'boss_title', 'boss_active', 'job_detail_url', 'referer'
            ]
            if field not in valid_fields:
                logger.error(f"无效的字段名: {field}")
                return []

            with self.connection.cursor() as cursor:
                if value == "":
                    query = f"SELECT * FROM jobs WHERE {field} IS NULL OR {field} = '' ORDER BY created_at DESC"
                    cursor.execute(query)
                else:
                    query = f"SELECT * FROM jobs WHERE {field} = %s ORDER BY created_at DESC"
                    cursor.execute(query, (value,))
                results = cursor.fetchall()
                logger.info(f"在字段 '{field}' 中搜索值 '{value}'，找到 {len(results)} 个匹配职位")
                return results
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"精准搜索职位失败: {e}")
            return []

    def update_job(self, job_id: int, update_data: Dict[str, Any]) -> bool:
        """更新职位信息"""
        try:
            valid_fields = [
                'job_name', 'job_desc', 'skills', 'key_word', 'job_type', 'job_salary',
                'tag_list', 'boss_name', 'boss_company', 'company_location',
                'boss_title', 'boss_active', 'referer'
            ]
            update_fields = []
            values = []
            for field in valid_fields:
                if field in update_data:
                    update_fields.append(f"{field} = %s")
                    values.append(update_data[field])

            if not update_fields:
                return False

            values.append(job_id)
            with self.connection.cursor() as cursor:
                update_query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_query, values)
                self.connection.commit()
            logger.info(f"职位ID {job_id} 更新成功！")
            return True
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"更新职位失败: {e}")
            return False

    def delete_job(self, job_id: int) -> bool:
        """删除职位信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
                self.connection.commit()
            logger.info(f"职位ID {job_id} 删除成功！")
            return True
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"删除职位失败: {e}")
            return False

    # ========== 投递记录表操作 ==========

    def add_post_record(self, job_id: int, status: str, ai_result: str = "") -> Optional[int]:
        """添加投递记录，如果 job_id 已存在则更新记录"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id FROM posts WHERE job_id = %s", (job_id,))
                existing_record = cursor.fetchone()

                if existing_record:
                    update_query = """
                    UPDATE posts
                    SET status = %s, ai_result = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE job_id = %s
                    """
                    cursor.execute(update_query, (status, ai_result, job_id))
                    self.connection.commit()
                    post_id = existing_record['id']
                    logger.info(f"投递记录已更新！职位ID: {job_id}, 状态: {status}")
                else:
                    insert_query = """
                    INSERT INTO posts (job_id, status, ai_result) VALUES (%s, %s, %s)
                    """
                    cursor.execute(insert_query, (job_id, status, ai_result))
                    self.connection.commit()
                    post_id = cursor.lastrowid
                    logger.info(f"投递记录添加成功！职位ID: {job_id}, 状态: {status}")

                return post_id
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"处理投递记录失败: {e}")
            return None

    def get_post_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取投递记录"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT * FROM posts WHERE id = %s", (post_id,))
                return cursor.fetchone()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取投递记录失败: {e}")
            return None

    def get_posts_by_job_id(self, job_id: int) -> List[Dict[str, Any]]:
        """根据职位ID获取投递记录"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM posts WHERE job_id = %s ORDER BY created_at DESC",
                    (job_id,)
                )
                return cursor.fetchall()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取投递记录失败: {e}")
            return []

    def get_all_posts(self) -> List[Dict[str, Any]]:
        """获取所有投递记录"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.*, j.job_name, j.boss_company
                    FROM posts p
                    LEFT JOIN jobs j ON p.job_id = j.id
                    ORDER BY p.created_at DESC
                """)
                return cursor.fetchall()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取投递记录失败: {e}")
            return []

    def update_post_status(self, post_id: int, status: str) -> bool:
        """更新投递状态"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE posts SET status = %s WHERE id = %s",
                    (status, post_id)
                )
                self.connection.commit()
            logger.info(f"投递记录ID {post_id} 状态更新为: {status}")
            return True
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"更新投递状态失败: {e}")
            return False

    def get_jobs_by_post_status(self, status: str) -> List[Dict[str, Any]]:
        """根据投递状态查找所有职位信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT j.*, p.status, p.created_at as post_created_at, p.updated_at as post_updated_at
                    FROM jobs j
                    INNER JOIN posts p ON j.id = p.job_id
                    WHERE p.status = %s
                    ORDER BY p.updated_at DESC
                """, (status,))
                return cursor.fetchall()
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"根据投递状态查找职位失败: {e}")
            return []

    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """获取活跃职位 - 在 posts 表中没有记录的职位"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT j.*
                    FROM jobs j
                    LEFT JOIN posts p ON j.id = p.job_id
                    WHERE p.job_id IS NULL or p.status = ''
                    ORDER BY j.created_at DESC
                """)
                active_jobs = cursor.fetchall()
                logger.info(f"找到 {len(active_jobs)} 个活跃职位")
                return active_jobs
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取活跃职位失败: {e}")
            return []

    def get_error_status_jobs(self) -> List[Dict[str, Any]]:
        """获取 closed 状态的职位"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT j.*
                    FROM jobs j
                    LEFT JOIN posts p ON j.id = p.job_id
                    WHERE p.status = 'closed'
                    ORDER BY j.created_at DESC
                """)
                jobs = cursor.fetchall()
                logger.info(f"找到 {len(jobs)} 个 closed 状态职位")
                return jobs
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取 closed 状态职位失败: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM jobs")
                total_jobs = cursor.fetchone()['count']

                cursor.execute("SELECT COUNT(*) as count FROM posts")
                total_posts = cursor.fetchone()['count']

                cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
                status_stats = {row['status']: row['count'] for row in cursor.fetchall()}

                return {
                    'total_jobs': total_jobs,
                    'total_posts': total_posts,
                    'status_stats': status_stats
                }
        except (MySQLError, sqlite3.Error) as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'total_jobs': 0, 'total_posts': 0, 'status_stats': {}}

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")


# 使用示例
if __name__ == "__main__":
    db = DatabaseManager()
    db2 = DatabaseManager()
    logger.info(f"db和db2是同一个实例吗？ {db is db2}")

    db.create_tables()
    db.add_post_record(203, "post_error")

    db.close()

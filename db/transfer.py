from db_old import MySqlClient
from db import DatabaseManager
from typing import Optional

class DataTransfer:
    """数据迁移工具 - 负责从旧数据库迁移数据到新数据库"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.old_db = MySqlClient()  # 旧数据库连接
        self.new_db = DatabaseManager()  # 新数据库连接
    
    def migrate_all_jobs(self):
        """迁移所有职位数据"""
        print("🚀 开始数据迁移...")
        
        # 获取旧数据库中的所有职位
        old_jobs = self.old_db.read_all_jobs()
        print(f"📊 从旧数据库读取到 {len(old_jobs)} 条职位记录")
        
        migrated_count = 0
        post_created_count = 0
        
        for old_job in old_jobs:
            # 迁移职位数据到新数据库
            job_id = self._migrate_job(old_job)
            
            if job_id:
                migrated_count += 1
                
                # 如果旧职位有状态信息，迁移到posts表
                if old_job.get('job_status') and old_job['job_status'] != 'active':
                    self._migrate_job_status(job_id, old_job['job_status'])
                    post_created_count += 1
        
        print(f"✅ 数据迁移完成！")
        print(f"📝 成功迁移职位: {migrated_count} 条")
        print(f"📨 创建投递记录: {post_created_count} 条")
        
        return migrated_count, post_created_count
    
    def _migrate_job(self, old_job: dict) -> Optional[int]:
        """迁移单个职位数据"""
        try:
            # 构建新职位数据结构
            new_job_data = {
                'job_name': old_job.get('job_name', ''),
                'job_desc': old_job.get('job_desc', ''),
                'skills': '',  # 旧数据库没有这个字段
                'key_word': old_job.get('key_word', ''),
                'job_salary': old_job.get('job_salary', ''),
                'tag_list': old_job.get('tag_list', ''),
                'boss_name': '',  # 旧数据库没有这个字段
                'boss_company': old_job.get('boss_company', ''),
                'company_location': old_job.get('company_location', ''),
                'boss_title': '',  # 旧数据库没有这个字段
                'boss_active': '',  # 旧数据库没有这个字段
                'job_detail_url': old_job.get('job_detail_url', ''),
                'referer': old_job.get('referer', '')
            }
            
            # 检查是否已存在（通过URL判断）
            existing_job = self.new_db.get_job_by_url(new_job_data['job_detail_url'])
            if existing_job:
                print(f"⚠️ 职位已存在，跳过: {new_job_data['job_name']}")
                return existing_job['id']
            
            # 添加新职位
            job_id = self.new_db.add_job(new_job_data)
            if job_id:
                print(f"✅ 迁移职位成功: {new_job_data['job_name']}")
                return job_id
            else:
                print(f"❌ 迁移职位失败: {new_job_data['job_name']}")
                return None
                
        except Exception as e:
            print(f"❌ 迁移职位时出错: {e}")
            return None
    
    def _migrate_job_status(self, job_id: int, status: str):
        """迁移职位状态到投递记录表"""
        try:
            # 添加投递记录
            post_id = self.new_db.add_post_record(job_id, status, "从旧数据库迁移")
            if post_id:
                print(f"📨 创建投递记录成功: 职位ID={job_id}, 状态={status}")
            else:
                print(f"⚠️ 创建投递记录失败: 职位ID={job_id}, 状态={status}")
        except Exception as e:
            print(f"❌ 迁移状态时出错: {e}")
    
    def get_migration_statistics(self):
        """获取迁移统计信息"""
        print("\n📊 迁移统计信息:")
        
        # 旧数据库统计
        old_jobs = self.old_db.read_all_jobs()
        old_status_count = sum(1 for job in old_jobs if job.get('job_status') and job['job_status'] != 'active')
        
        print(f"📋 旧数据库:")
        print(f"   - 总职位数: {len(old_jobs)}")
        print(f"   - 有状态记录的职位: {old_status_count}")
        
        # 新数据库统计
        new_jobs = self.new_db.get_all_jobs()
        new_posts = self.new_db.get_all_posts()
        
        print(f"📋 新数据库:")
        print(f"   - 总职位数: {len(new_jobs)}")
        print(f"   - 总投递记录数: {len(new_posts)}")
        
        # 状态分布
        status_stats = self.new_db.get_statistics()
        print(f"   - 投递状态分布: {status_stats.get('status_stats', {})}")

def main():
    """主函数 - 执行数据迁移"""
    print("=" * 50)
    print("🔄 数据迁移工具启动")
    print("=" * 50)
    
    # 创建迁移工具实例
    transfer = DataTransfer()
    
    # 确保新数据库表已创建
    print("🔧 创建新数据库表...")
    transfer.new_db.create_tables()
    
    # 显示迁移前统计
    print("\n📈 迁移前统计:")
    transfer.get_migration_statistics()
    
    # 执行迁移
    print("\n🔄 开始执行数据迁移...")
    migrated_count, post_created_count = transfer.migrate_all_jobs()
    
    # 显示迁移后统计
    print("\n📈 迁移后统计:")
    transfer.get_migration_statistics()
    
    print("\n" + "=" * 50)
    print("🎉 数据迁移完成！")
    print("=" * 50)

if __name__ == "__main__":
    main()

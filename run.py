from boss.boss import Boss
from util.logger import log
from db.db import DatabaseManager


def find_new_jobs():
    # 100只是为了重试
    for _ in range(100):
        try:
            Boss.new_jobs()
            break
        except Exception as e:
            log.info(f"{e} retry")

def fill_job_infos():
    for _ in range(100):
        try:
            jobs = db.search_jobs_by_field_value("job_desc", "")
            if not jobs:
                break
            Boss.update_job_detail_info(jobs)
        except Exception as e:
            log.info(f"{e} retry")


if __name__ == "__main__":
    db = DatabaseManager()
    db.create_tables()

    find_new_jobs()

    fill_job_infos()

    # 投递那就打开下面这行
    #Boss.post_active_jobs()

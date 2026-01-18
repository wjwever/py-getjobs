from boss.boss import Boss
from util.logger import log
from db.db import DatabaseManager

if __name__ == "__main__":
    db = DatabaseManager()
    db.create_tables()
    for _ in range(100):
        try:
            Boss.new_jobs()
            break
        except Exception as e:
            log.info(f"{e} retry")

    for _ in range(100):
        try:
            jobs = db.search_jobs_by_field_value("job_desc", "")
            if not jobs:
                break
            Boss.update_job_detail_info(jobs)
        except Exception as e:
            log.info(f"{e} retry")

    Boss.post_active_jobs()
    # Boss.post_error_status_jobs()
    # Boss.save_black_list()



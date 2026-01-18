from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import mysql.connector
from mysql.connector import Error

app = FastAPI(title="PyGetJobs API", description="Boss直聘职位管理API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobResponse(BaseModel):
    id: int
    job_name: str
    job_desc: str
    job_salary: str
    boss_company: str
    company_location: str
    tag_list: str
    created_at: str
    post_status: Optional[str] = None
    post_date: Optional[str] = None
    boss_name: Optional[str] = None
    skills: Optional[str] = None
    key_word: Optional[str] = None
    boss_title: Optional[str] = None
    boss_active: Optional[str] = None
    job_detail_url: Optional[str] = None


class JobDetailResponse(BaseModel):
    id: int
    job_name: str
    job_desc: str
    skills: str
    key_word: str
    job_salary: str
    tag_list: str
    boss_name: str
    boss_company: str
    company_location: str
    boss_title: str
    boss_active: str
    job_detail_url: str
    referer: str
    created_at: str
    updated_at: str
    post_status: Optional[str] = None
    post_date: Optional[str] = None


class ApplyRequest(BaseModel):
    status: str = "applied"
    ai_result: str = ""


class StatsResponse(BaseModel):
    total_jobs: int
    total_posts: int
    active_jobs: int
    status_stats: Dict[str, int]


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.connection = None
            cls._instance.connect()
        return cls._instance

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="py_getjobs",
                charset="utf8mb4",
            )
        except Error as e:
            raise HTTPException(status_code=500, detail=f"数据库连接失败: {e}")

    def get_db(self):
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection


db_manager = DatabaseManager()


def get_db():
    return db_manager.get_db()


@app.get("/api/jobs", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    db=Depends(get_db),
):
    try:
        print("get/jobs")
        cursor = db.cursor(dictionary=True)

        query = """
        SELECT 
            j.*,
            p.status as post_status,
            p.created_at as post_date
        FROM jobs j
        LEFT JOIN posts p ON j.id = p.job_id
        WHERE 1=1
        """
        params = []

        if keyword:
            query += " AND (j.job_name LIKE %s OR j.job_desc LIKE %s OR j.boss_company LIKE %s)"
            keyword_param = f"%{keyword}%"
            params.extend([keyword_param, keyword_param, keyword_param])

        if company:
            query += " AND j.boss_company LIKE %s"
            params.append(f"%{company}%")

        if location:
            query += " AND j.company_location LIKE %s"
            params.append(f"%{location}%")

        query += " ORDER BY j.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cursor.execute(query, params)
        jobs = cursor.fetchall()

        for job in jobs:
            if job["post_date"]:
                job["post_date"] = (
                    job["post_date"].isoformat()
                    if hasattr(job["post_date"], "isoformat")
                    else str(job["post_date"])
                )
            if job["created_at"]:
                job["created_at"] = (
                    job["created_at"].isoformat()
                    if hasattr(job["created_at"], "isoformat")
                    else str(job["created_at"])
                )

        return jobs
    except Error as e:
        raise HTTPException(status_code=500, detail=f"获取职位失败: {e}")


@app.get("/api/jobs/active", response_model=List[JobResponse])
async def get_active_jobs(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db=Depends(get_db)
):
    try:
        cursor = db.cursor(dictionary=True)

        query = """
        SELECT j.*, NULL as post_status, NULL as post_date
        FROM jobs j 
        LEFT JOIN posts p ON j.id = p.job_id 
        WHERE p.job_id IS NULL OR p.status = '' 
        ORDER BY j.created_at DESC
        LIMIT %s OFFSET %s
        """

        cursor.execute(query, (limit, skip))
        jobs = cursor.fetchall()

        for job in jobs:
            if job["created_at"]:
                job["created_at"] = (
                    job["created_at"].isoformat()
                    if hasattr(job["created_at"], "isoformat")
                    else str(job["created_at"])
                )

        return jobs
    except Error as e:
        raise HTTPException(status_code=500, detail=f"获取活跃职位失败: {e}")


@app.get("/api/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job_detail(job_id: int, db=Depends(get_db)):
    try:
        cursor = db.cursor(dictionary=True)

        query = """
        SELECT 
            j.*,
            p.status as post_status,
            p.created_at as post_date
        FROM jobs j
        LEFT JOIN posts p ON j.id = p.job_id
        WHERE j.id = %s
        """

        cursor.execute(query, (job_id,))
        job = cursor.fetchone()

        if not job:
            raise HTTPException(status_code=404, detail="职位不存在")

        if job["post_date"]:
            job["post_date"] = (
                job["post_date"].isoformat()
                if hasattr(job["post_date"], "isoformat")
                else str(job["post_date"])
            )
        if job["created_at"]:
            job["created_at"] = (
                job["created_at"].isoformat()
                if hasattr(job["created_at"], "isoformat")
                else str(job["created_at"])
            )
        if job["updated_at"]:
            job["updated_at"] = (
                job["updated_at"].isoformat()
                if hasattr(job["updated_at"], "isoformat")
                else str(job["updated_at"])
            )

        return job
    except Error as e:
        raise HTTPException(status_code=500, detail=f"获取职位详情失败: {e}")


@app.post("/api/jobs/{job_id}/apply")
async def apply_job(job_id: int, apply_request: ApplyRequest, db=Depends(get_db)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="职位不存在")

        cursor.execute("SELECT id FROM posts WHERE job_id = %s", (job_id,))
        existing_record = cursor.fetchone()

        if existing_record:
            update_query = """
            UPDATE posts 
            SET status = %s, ai_result = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE job_id = %s
            """
            cursor.execute(
                update_query, (apply_request.status, apply_request.ai_result, job_id)
            )
        else:
            insert_query = """
            INSERT INTO posts (job_id, status, ai_result) VALUES (%s, %s, %s)
            """
            cursor.execute(
                insert_query, (job_id, apply_request.status, apply_request.ai_result)
            )

        db.commit()

        return {"message": "投递成功", "job_id": job_id, "status": apply_request.status}
    except Error as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"投递失败: {e}")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db=Depends(get_db)):
    try:
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) 
            FROM jobs j 
            LEFT JOIN posts p ON j.id = p.job_id 
            WHERE p.job_id IS NULL OR p.status = ''
        """)
        active_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT status, COUNT(*) FROM posts GROUP BY status")
        status_stats = {status: count for status, count in cursor.fetchall()}

        return StatsResponse(
            total_jobs=total_jobs,
            total_posts=total_posts,
            active_jobs=active_jobs,
            status_stats=status_stats,
        )
    except Error as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {e}")


@app.get("/api/search")
async def search_jobs(
    q: str = Query(..., min_length=1),
    field: str = Query(
        "job_name", regex="^(job_name|job_desc|boss_company|company_location|skills)$"
    ),
    db=Depends(get_db),
):
    try:
        cursor = db.cursor(dictionary=True)

        query = f"""
        SELECT 
            j.*,
            p.status as post_status,
            p.created_at as post_date
        FROM jobs j
        LEFT JOIN posts p ON j.id = p.job_id
        WHERE j.{field} LIKE %s
        ORDER BY j.created_at DESC
        """

        cursor.execute(query, (f"%{q}%",))
        jobs = cursor.fetchall()

        for job in jobs:
            if job["post_date"]:
                job["post_date"] = (
                    job["post_date"].isoformat()
                    if hasattr(job["post_date"], "isoformat")
                    else str(job["post_date"])
                )
            if job["created_at"]:
                job["created_at"] = (
                    job["created_at"].isoformat()
                    if hasattr(job["created_at"], "isoformat")
                    else str(job["created_at"])
                )

        return jobs
    except Error as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


@app.get("/")
async def root():
    return {
        "message": "PyGetJobs API",
        "version": "1.0.0",
        "endpoints": {
            "jobs": "/api/jobs",
            "active_jobs": "/api/jobs/active",
            "job_detail": "/api/jobs/{id}",
            "apply_job": "/api/jobs/{id}/apply",
            "stats": "/api/stats",
            "search": "/api/search",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

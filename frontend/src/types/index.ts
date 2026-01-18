export interface Job {
  id: number;
  job_name: string;
  job_desc: string;
  job_salary: string;
  boss_company: string;
  company_location: string;
  tag_list: string;
  created_at: string;
  post_status?: string;
  post_date?: string;
  boss_name?: string;
  skills?: string;
  key_word?: string;
  boss_title?: string;
  boss_active?: string;
  job_detail_url?: string;
}

export interface JobDetail extends Job {
  referer: string;
  updated_at: string;
}

export interface Stats {
  total_jobs: number;
  total_posts: number;
  active_jobs: number;
  status_stats: Record<string, number>;
}

export interface ApplyRequest {
  status: string;
  ai_result: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}
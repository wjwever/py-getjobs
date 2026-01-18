import axios from 'axios';
import type { Job, JobDetail, Stats, ApplyRequest } from '../types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const jobApi = {
  getJobs: async (params?: {
    skip?: number;
    limit?: number;
    keyword?: string;
    company?: string;
    location?: string;
  }) => {
    const response = await api.get<Job[]>('/api/jobs', { params });
    return response.data;
  },

  getActiveJobs: async (params?: {
    skip?: number;
    limit?: number;
  }) => {
    const response = await api.get<Job[]>('/api/jobs/active', { params });
    return response.data;
  },

  getJobDetail: async (jobId: number) => {
    const response = await api.get<JobDetail>(`/api/jobs/${jobId}`);
    return response.data;
  },

  applyJob: async (jobId: number, data: ApplyRequest) => {
    const response = await api.post(`/api/jobs/${jobId}/apply`, data);
    return response.data;
  },

  getStats: async () => {
    const response = await api.get<Stats>('/api/stats');
    return response.data;
  },

  searchJobs: async (query: string, field: string = 'job_name') => {
    const response = await api.get<Job[]>('/api/search', {
      params: { q: query, field }
    });
    return response.data;
  },
};

export default api;
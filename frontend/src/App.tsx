import { useState, useEffect, useCallback } from 'react';
import type { Job, JobDetail, Stats } from './types';
import { jobApi } from './services/api';
import Header from './components/Header';
import StatsPanel from './components/StatsPanel';
import SearchBar from './components/SearchBar';
import JobGrid from './components/JobGrid';
import JobDetailModal from './components/JobDetailModal';
import { Toaster, toast } from 'react-hot-toast';

const PAGE_SIZE = 20;

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<Stats>({
    total_jobs: 0,
    total_posts: 0,
    active_jobs: 0,
    status_stats: {},
  });
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [applyingJobId, setApplyingJobId] = useState<number | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [searchParams, setSearchParams] = useState<{
    keyword?: string;
    company?: string;
    location?: string;
  }>({});
  const [selectedJob, setSelectedJob] = useState<JobDetail | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchStats = useCallback(async () => {
    try {
      const data = await jobApi.getStats();
      setStats(data);
    } catch (error) {
      console.error('获取统计信息失败:', error);
      toast.error('获取统计信息失败');
    }
  }, []);

  const fetchJobs = useCallback(async (reset = false) => {
    try {
      const currentPage = reset ? 0 : page;
      const skip = currentPage * PAGE_SIZE;
      
      const data = await jobApi.getJobs({
        skip,
        limit: PAGE_SIZE,
        ...searchParams,
      });

      if (reset) {
        setJobs(data);
      } else {
        setJobs(prev => [...prev, ...data]);
      }

      setHasMore(data.length === PAGE_SIZE);
      if (reset) {
        setPage(1);
      } else {
        setPage(prev => prev + 1);
      }
    } catch (error) {
      console.error('获取职位失败:', error);
      toast.error('获取职位失败');
    } finally {
      setLoading(false);
      setSearchLoading(false);
    }
  }, [page, searchParams]);

  const handleSearch = useCallback((params: {
    keyword?: string;
    company?: string;
    location?: string;
  }) => {
    setSearchParams(params);
    setSearchLoading(true);
    setPage(0);
    setHasMore(true);
  }, []);

  const handleApply = useCallback(async (jobId: number) => {
    try {
      setApplyingJobId(jobId);
      await jobApi.applyJob(jobId, { status: 'applied', ai_result: '' });
      
      setJobs(prev => prev.map(job => 
        job.id === jobId 
          ? { ...job, post_status: 'applied', post_date: new Date().toISOString() }
          : job
      ));
      
      await fetchStats();
      toast.success('投递成功！');
    } catch (error) {
      console.error('投递失败:', error);
      toast.error('投递失败');
    } finally {
      setApplyingJobId(null);
    }
  }, [fetchStats]);

  const handleCardClick = useCallback(async (jobId: number) => {
    try {
      const jobDetail = await jobApi.getJobDetail(jobId);
      setSelectedJob(jobDetail);
      setIsModalOpen(true);
    } catch (error) {
      console.error('获取职位详情失败:', error);
      toast.error('获取职位详情失败');
    }
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedJob(null);
  }, []);

  const handleLoadMore = useCallback(() => {
    if (!loading && hasMore) {
      fetchJobs();
    }
  }, [loading, hasMore, fetchJobs]);



  useEffect(() => {
    fetchStats();
    fetchJobs(true);
  }, []);

  useEffect(() => {
    if (searchLoading) {
      fetchJobs(true);
    }
  }, [searchLoading, fetchJobs]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StatsPanel stats={stats} isLoading={loading} />
        
        <SearchBar onSearch={handleSearch} isLoading={searchLoading} />
        
        <JobGrid
          jobs={jobs}
          onApply={handleApply}
          onCardClick={handleCardClick}
          loading={loading}
          hasMore={hasMore}
          onLoadMore={handleLoadMore}
          applyingJobId={applyingJobId}
        />
      </main>
      
      <footer className="mt-12 py-6 border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-600 text-sm">
            <p>PyGetJobs - Boss直聘职位管理平台</p>
            <p className="mt-2">© {new Date().getFullYear()} 版权所有</p>
          </div>
        </div>
      </footer>

      <JobDetailModal
        job={selectedJob}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}

export default App;
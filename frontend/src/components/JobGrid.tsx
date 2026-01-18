import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { Job } from '../types';
import JobCard from './JobCard';

interface JobGridProps {
  jobs: Job[];
  onApply: (jobId: number) => Promise<void>;
  onCardClick?: (jobId: number) => void;
  loading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  applyingJobId?: number | null;
}

const JobGrid: React.FC<JobGridProps> = ({
  jobs,
  onApply,
  onCardClick,
  loading = false,
  hasMore = false,
  onLoadMore,
  applyingJobId = null,
}) => {
  const observerRef = useRef<IntersectionObserver | null>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const [columns, setColumns] = useState(3);

  useEffect(() => {
    const updateColumns = () => {
      const width = window.innerWidth;
      if (width < 640) setColumns(1);
      else if (width < 1024) setColumns(2);
      else setColumns(3);
    };

    updateColumns();
    window.addEventListener('resize', updateColumns);
    return () => window.removeEventListener('resize', updateColumns);
  }, []);

  useEffect(() => {
    if (!hasMore || !onLoadMore || loading) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [hasMore, onLoadMore, loading]);

  const distributeJobs = useCallback(() => {
    const columnsArray: Job[][] = Array.from({ length: columns }, () => []);
    
    jobs.forEach((job, index) => {
      const columnIndex = index % columns;
      columnsArray[columnIndex].push(job);
    });
    
    return columnsArray;
  }, [jobs, columns]);

  const columnsArray = distributeJobs();

  if (loading && jobs.length === 0) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-6"></div>
            <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-4/6"></div>
          </div>
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-gray-700 mb-2">暂无职位</h3>
        <p className="text-gray-500">尝试调整搜索条件或刷新页面</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {columnsArray.map((columnJobs, columnIndex) => (
          <div key={columnIndex} className="space-y-6">
            {columnJobs.map((job) => (
               <JobCard
                key={job.id}
                job={job}
                onApply={onApply}
                onClick={onCardClick}
                isLoading={applyingJobId === job.id}
              />
            ))}
          </div>
        ))}
      </div>

      {hasMore && onLoadMore && (
        <div ref={loadMoreRef} className="py-8 text-center">
          {loading ? (
            <div className="inline-flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-gray-600">加载更多...</span>
            </div>
          ) : (
            <div className="h-20"></div>
          )}
        </div>
      )}

      {loading && jobs.length > 0 && (
        <div className="py-8 text-center">
          <div className="inline-flex items-center space-x-2">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-gray-600">加载中...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobGrid;
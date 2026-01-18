import React from 'react';
import type { Job } from '../types';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface JobCardProps {
  job: Job;
  onApply?: (jobId: number) => void;
  onClick?: (jobId: number) => void;
  isLoading?: boolean;
}

const JobCard: React.FC<JobCardProps> = ({ job, onApply, onClick, isLoading = false }) => {
  const tags = job.tag_list ? job.tag_list.split(',').filter(tag => tag.trim()) : [];
  const skills = job.skills ? job.skills.split(',').filter(skill => skill.trim()) : [];

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return formatDistanceToNow(date, { addSuffix: true, locale: zhCN });
    } catch {
      return dateString;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'applied':
        return 'bg-green-100 text-green-800';
      case 'post_ok':
        return 'bg-blue-100 text-blue-800';
      case 'ai_filtered':
        return 'bg-yellow-100 text-yellow-800';
      case 'post_error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status?: string) => {
    switch (status) {
      case 'applied':
        return '已投递';
      case 'post_ok':
        return '投递成功';
      case 'ai_filtered':
        return 'AI过滤';
      case 'post_error':
        return '投递失败';
      default:
        return '未投递';
    }
  };

  const handleCardClick = (e: React.MouseEvent) => {
    // 防止点击投递按钮时触发卡片点击
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    onClick?.(job.id);
  };

  const getDescriptionPreview = () => {
    if (!job.job_desc) return '';
    // 移除多余的空格和换行，截取前150个字符
    const cleanDesc = job.job_desc.replace(/\s+/g, ' ').trim();
    if (cleanDesc.length <= 150) return cleanDesc;
    return cleanDesc.substring(0, 150) + '...';
  };

  const descriptionPreview = getDescriptionPreview();

  return (
    <div 
      className="bg-white rounded-xl shadow-md hover:shadow-lg transition-shadow duration-300 overflow-hidden border border-gray-200 cursor-pointer"
      onClick={handleCardClick}
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2 hover:text-blue-600 transition-colors">
              {job.job_name}
            </h3>
            <div className="flex items-center gap-4 mb-3">
              <span className="text-lg font-semibold text-blue-600">
                {job.job_salary || '面议'}
              </span>
              <span className="text-sm text-gray-600">
                {job.company_location}
              </span>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.post_status)}`}>
            {getStatusText(job.post_status)}
          </div>
        </div>

        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-medium text-gray-700">{job.boss_company}</span>
            {job.boss_name && (
              <span className="text-sm text-gray-500">· {job.boss_name}</span>
            )}
          </div>
          {job.boss_title && (
            <p className="text-sm text-gray-600">{job.boss_title}</p>
          )}
        </div>

        {/* 职位描述预览 */}
        {descriptionPreview && (
          <div className="mb-4">
            <div className="text-sm text-gray-600 line-clamp-3 bg-gray-50 p-3 rounded-lg">
              {descriptionPreview}
              <span className="text-blue-500 ml-1 cursor-pointer hover:text-blue-700" onClick={(e) => {
                e.stopPropagation();
                onClick?.(job.id);
              }}>
                查看更多
              </span>
            </div>
          </div>
        )}

        {skills.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">技能要求</h4>
            <div className="flex flex-wrap gap-2">
              {skills.slice(0, 5).map((skill, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                >
                  {skill.trim()}
                </span>
              ))}
              {skills.length > 5 && (
                <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
                  +{skills.length - 5}更多
                </span>
              )}
            </div>
          </div>
        )}

        {tags.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-600 rounded-md text-xs"
                >
                  {tag.trim()}
                </span>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100">
          <div className="text-sm text-gray-500">
            {formatDate(job.created_at)}
          </div>
          
          {job.post_status ? (
            <div className="text-sm text-gray-600">
              投递于 {formatDate(job.post_date)}
            </div>
          ) : (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onApply?.(job.id);
              }}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
            >
              {isLoading ? '投递中...' : '立即投递'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobCard;
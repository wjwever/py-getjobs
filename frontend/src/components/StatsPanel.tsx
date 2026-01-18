import React from 'react';
import { Briefcase, Send, Clock, TrendingUp } from 'lucide-react';
import type { Stats } from '../types';

interface StatsPanelProps {
  stats: Stats;
  isLoading?: boolean;
}

const StatsPanel: React.FC<StatsPanelProps> = ({ stats, isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: '总职位数',
      value: stats.total_jobs,
      icon: Briefcase,
      color: 'bg-blue-500',
      textColor: 'text-blue-600',
    },
    {
      title: '已投递数',
      value: stats.total_posts,
      icon: Send,
      color: 'bg-green-500',
      textColor: 'text-green-600',
    },
    {
      title: '活跃职位',
      value: stats.active_jobs,
      icon: Clock,
      color: 'bg-yellow-500',
      textColor: 'text-yellow-600',
    },
    {
      title: '投递成功率',
      value: stats.total_posts > 0 
        ? `${Math.round((stats.status_stats['post_ok'] || 0) / stats.total_posts * 100)}%`
        : '0%',
      icon: TrendingUp,
      color: 'bg-purple-500',
      textColor: 'text-purple-600',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      {statCards.map((card, index) => (
        <div key={index} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-lg ${card.color} bg-opacity-10`}>
              <card.icon className={`w-6 h-6 ${card.textColor}`} />
            </div>
            <span className="text-sm text-gray-500">{card.title}</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{card.value}</div>
        </div>
      ))}
    </div>
  );
};

export default StatsPanel;
import React from 'react';
import { Briefcase } from 'lucide-react';

interface HeaderProps {
  // 移除了onRefresh和isLoading props
}

const Header: React.FC<HeaderProps> = () => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Briefcase className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PyGetJobs</h1>
              <p className="text-sm text-gray-600">Boss直聘职位管理平台</p>
            </div>
          </div>
          
          <div className="hidden md:flex items-center space-x-4">
            <a
              href="#all"
              className="text-gray-700 hover:text-blue-600 transition-colors font-medium"
            >
              全部职位
            </a>
            <a
              href="#active"
              className="text-gray-700 hover:text-blue-600 transition-colors font-medium"
            >
              活跃职位
            </a>
            <a
              href="#applied"
              className="text-gray-700 hover:text-blue-600 transition-colors font-medium"
            >
              已投递
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
import React, { useState } from 'react';
import { Search, Filter, X } from 'lucide-react';

interface SearchBarProps {
  onSearch: (params: {
    keyword?: string;
    company?: string;
    location?: string;
  }) => void;
  isLoading?: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading = false }) => {
  const [keyword, setKeyword] = useState('');
  const [company, setCompany] = useState('');
  const [location, setLocation] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      keyword: keyword.trim() || undefined,
      company: company.trim() || undefined,
      location: location.trim() || undefined,
    });
  };

  const handleClear = () => {
    setKeyword('');
    setCompany('');
    setLocation('');
    onSearch({});
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6 border border-gray-200">
      <form onSubmit={handleSubmit}>
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="搜索职位名称、描述或公司..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              />
            </div>
          </div>
          
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 transition"
            >
              <Filter className="w-4 h-4" />
              <span>筛选</span>
            </button>
            
            <button
              type="button"
              onClick={handleClear}
              className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2 transition"
            >
              <X className="w-4 h-4" />
              <span>清空</span>
            </button>
            
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isLoading ? '搜索中...' : '搜索'}
            </button>
          </div>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                公司名称
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="输入公司名称..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                工作地点
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="输入工作地点..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
              />
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default SearchBar;
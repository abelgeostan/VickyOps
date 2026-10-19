import React, { useState } from 'react';
import { Search, Filter, Server, CheckCircle2, AlertTriangle } from 'lucide-react';
import { Service } from '../../types';
import { ServiceCard } from './ServiceCard';

interface ServiceListProps {
  services: Service[];
  onAction: (serviceId: string, action: string) => void;
  onViewDetails: (service: Service) => void;
  isLoading: boolean;
}

export const ServiceList: React.FC<ServiceListProps> = ({
  services,
  onAction,
  onViewDetails,
  isLoading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'git' | 'image' | 'running'>('all');

  const filteredServices = services.filter((s) => {
    const matchesSearch =
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.description && s.description.toLowerCase().includes(searchTerm.toLowerCase()));

    if (!matchesSearch) return false;

    if (filterType === 'git') return s.id === 'vickyai' || s.deployment_type === 'git_compose';
    if (filterType === 'image') return s.deployment_type === 'image_compose';
    if (filterType === 'running') return s.status === 'running';

    return true;
  });

  return (
    <div className="space-y-5">
      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <div className="relative flex-1 sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search services (VickyAI, Nextcloud)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[#161b22] border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
            />
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 overflow-x-auto no-scrollbar">
          {(
            [
              { id: 'all', label: `All (${services.length})` },
              { id: 'git', label: 'Git-Backed (VickyAI)' },
              { id: 'image', label: 'Docker Hub' },
              { id: 'running', label: 'Running' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterType(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition ${
                filterType === tab.id
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                  : 'bg-[#161b22] text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredServices.map((service) => (
          <ServiceCard
            key={service.id}
            service={service}
            onAction={onAction}
            onViewDetails={onViewDetails}
            isLoading={isLoading}
          />
        ))}
      </div>
    </div>
  );
};

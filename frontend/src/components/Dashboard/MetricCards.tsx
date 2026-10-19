import React from 'react';
import { Cpu, MemoryStick as Memory, HardDrive, Network, Layers, ShieldCheck, Globe } from 'lucide-react';
import { ServerMetrics, CloudflareStatus } from '../../types';

interface MetricCardsProps {
  metrics: ServerMetrics | null;
  cloudflare: CloudflareStatus | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics, cloudflare }) => {
  const ramPercent = metrics?.ram?.percent || 0;
  const diskPercent = metrics?.disk?.percent || 0;
  const cpuPercent = metrics?.cpu_percent || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {/* CPU */}
      <div className="bg-[#161b22] border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-medium uppercase tracking-wider">CPU Load</span>
          <Cpu className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono text-white">{cpuPercent}%</span>
          <span className="text-xs text-slate-400 font-mono">
            {metrics?.cpu_load?.load1.toFixed(2) || '0.00'} 1m
          </span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              cpuPercent > 80 ? 'bg-rose-500' : cpuPercent > 50 ? 'bg-amber-500' : 'bg-cyan-400'
            }`}
            style={{ width: `${Math.min(100, Math.max(5, cpuPercent))}%` }}
          ></div>
        </div>
      </div>

      {/* RAM */}
      <div className="bg-[#161b22] border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-medium uppercase tracking-wider">Memory</span>
          <Memory className="w-4 h-4 text-purple-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono text-white">{ramPercent}%</span>
          <span className="text-xs text-slate-400 font-mono">
            {metrics?.ram?.used_human || '0 GB'} / {metrics?.ram?.total_human || '0 GB'}
          </span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              ramPercent > 85 ? 'bg-rose-500' : ramPercent > 70 ? 'bg-amber-500' : 'bg-purple-400'
            }`}
            style={{ width: `${Math.min(100, Math.max(5, ramPercent))}%` }}
          ></div>
        </div>
      </div>

      {/* Disk */}
      <div className="bg-[#161b22] border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-medium uppercase tracking-wider">Storage</span>
          <HardDrive className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-2xl font-bold font-mono text-white">{diskPercent}%</span>
          <span className="text-xs text-slate-400 font-mono">
            {metrics?.disk?.used_human || '0 GB'} / {metrics?.disk?.total_human || '0 GB'}
          </span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
          <div
            className="h-full rounded-full bg-emerald-400 transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, diskPercent))}%` }}
          ></div>
        </div>
      </div>

      {/* Network */}
      <div className="bg-[#161b22] border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-medium uppercase tracking-wider">Traffic</span>
          <Network className="w-4 h-4 text-blue-400" />
        </div>
        <div className="space-y-1">
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Rx In:</span>
            <span className="font-mono text-slate-200">{metrics?.network?.rx_human || '0 MB'}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-slate-400">Tx Out:</span>
            <span className="font-mono text-slate-200">{metrics?.network?.tx_human || '0 MB'}</span>
          </div>
        </div>
      </div>

      {/* Docker */}
      <div className="bg-[#161b22] border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-medium uppercase tracking-wider">Docker Daemon</span>
          <Layers className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
          <span className="text-sm font-semibold text-white">Active</span>
        </div>
        <p className="text-xs text-slate-400 font-mono mt-2 truncate">
          v{metrics?.docker_version || '29.x'}
        </p>
      </div>

      {/* Cloudflare Tunnel */}
      <div className="bg-[#161b22] border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-medium uppercase tracking-wider">Cloudflare Zero Trust</span>
          <Globe className="w-4 h-4 text-amber-400" />
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              (cloudflare?.active_count || 0) > 0 ? 'bg-emerald-500' : 'bg-rose-500'
            }`}
          ></span>
          <span className="text-sm font-semibold text-white">
            {cloudflare?.active_count || 0} / {cloudflare?.tunnel_count || 0} Tunnels
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-2 font-mono">
          {cloudflare?.overall_status === 'operational' ? 'Secure Mesh Active' : 'Check Tunnels'}
        </p>
      </div>
    </div>
  );
};

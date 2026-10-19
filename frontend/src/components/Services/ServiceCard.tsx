import React, { useState } from 'react';
import {
  Rocket,
  RotateCw,
  Square,
  Play,
  HeartPulse,
  GitBranch,
  GitCommit,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Clock,
  FolderGit2,
  HardDriveDownload,
  Info,
  Terminal,
} from 'lucide-react';
import { Service } from '../../types';

interface ServiceCardProps {
  service: Service;
  onAction: (serviceId: string, action: string) => void;
  onViewDetails: (service: Service) => void;
  isLoading?: boolean;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({
  service,
  onAction,
  onViewDetails,
  isLoading,
}) => {
  const isVickyAI = service.id === 'vickyai';
  const isRunning = service.status === 'running';
  const isDegraded = service.status === 'degraded';
  const isGitBased = isVickyAI || service.deployment_type === 'git_compose';

  return (
    <div
      className={`bg-[#161b22] border rounded-2xl p-5 transition-all flex flex-col justify-between shadow-md relative overflow-hidden ${
        isVickyAI
          ? 'border-cyan-500/40 hover:border-cyan-400/70 shadow-cyan-950/20'
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      {/* Top Tag & Header */}
      <div>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2.5">
            <div
              className={`w-3.5 h-3.5 rounded-full flex items-center justify-center ${
                isRunning
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : isDegraded
                  ? 'bg-amber-500/20 text-amber-400'
                  : 'bg-rose-500/20 text-rose-400'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isRunning ? 'bg-emerald-400' : isDegraded ? 'bg-amber-400' : 'bg-rose-500'
                }`}
              ></span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-base text-white tracking-tight">{service.name}</h3>
                {isVickyAI && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                    REFERENCE
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 line-clamp-1 mt-0.5">{service.description || 'Configured service workload'}</p>
            </div>
          </div>

          <button
            onClick={() => onViewDetails(service)}
            className="text-slate-400 hover:text-cyan-400 p-1.5 rounded-lg hover:bg-slate-800 transition"
            title="Service Details & Compatibility"
          >
            <Info className="w-4 h-4" />
          </button>
        </div>

        {/* Status badges & Metadata */}
        <div className="grid grid-cols-2 gap-2 text-xs bg-[#0d1117]/70 rounded-xl p-3 border border-slate-800/80 my-3 font-mono">
          {/* Docker state */}
          <div className="flex items-center space-x-2">
            <span className="text-slate-500">Docker:</span>
            <span
              className={`font-medium ${
                isRunning ? 'text-emerald-400' : isDegraded ? 'text-amber-400' : 'text-slate-400'
              }`}
            >
              {service.docker_status || 'Up'}
            </span>
          </div>

          {/* Health check */}
          <div className="flex items-center space-x-2">
            <span className="text-slate-500">Health:</span>
            <span className="text-slate-300 flex items-center space-x-1">
              {service.health_url ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>HTTP Active</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Containers OK</span>
                </>
              )}
            </span>
          </div>

          {/* Git Branch */}
          <div className="flex items-center space-x-2 col-span-2">
            <span className="text-slate-500 flex items-center space-x-1">
              <GitBranch className="w-3.5 h-3.5 text-slate-400" />
              <span>Branch:</span>
            </span>
            {isGitBased ? (
              <span className="text-cyan-400 font-semibold">{service.branch}</span>
            ) : (
              <span className="text-slate-400">Prebuilt Images (Registry)</span>
            )}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="pt-3 border-t border-slate-800/80 space-y-2">
        {/* Primary Action Button */}
        <button
          onClick={() => onAction(service.id, 'deploy')}
          disabled={isLoading}
          className={`w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-xl text-xs font-semibold tracking-wide transition shadow-md ${
            isVickyAI
              ? 'bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold shadow-cyan-500/20'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
          }`}
        >
          <Rocket className="w-3.5 h-3.5" />
          <span>{isGitBased ? 'Deploy Update' : 'Update & Recreate'}</span>
        </button>

        {/* Secondary quick actions */}
        <div className="grid grid-cols-4 gap-1.5">
          <button
            onClick={() => onAction(service.id, 'restart')}
            disabled={isLoading}
            className="flex items-center justify-center py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs transition"
            title="Restart Service"
          >
            <RotateCw className="w-3.5 h-3.5 mr-1 text-amber-400" />
            <span>Restart</span>
          </button>

          <button
            onClick={() => onAction(service.id, 'health_check')}
            disabled={isLoading}
            className="flex items-center justify-center py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs transition"
            title="Run Health Diagnostics"
          >
            <HeartPulse className="w-3.5 h-3.5 mr-1 text-emerald-400" />
            <span>Health</span>
          </button>

          <button
            onClick={() => onAction(service.id, 'backup')}
            disabled={isLoading}
            className="flex items-center justify-center py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs transition"
            title="Create Compressed Archive Backup"
          >
            <HardDriveDownload className="w-3.5 h-3.5 mr-1 text-purple-400" />
            <span>Backup</span>
          </button>

          <button
            onClick={() => onViewDetails(service)}
            className="flex items-center justify-center py-1.5 px-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs transition"
            title="View Details & Compatibility"
          >
            <Terminal className="w-3.5 h-3.5 mr-1 text-cyan-400" />
            <span>Inspect</span>
          </button>
        </div>
      </div>
    </div>
  );
};

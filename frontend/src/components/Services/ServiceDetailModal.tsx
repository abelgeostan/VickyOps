import React, { useEffect, useState } from 'react';
import { X, CheckCircle2, AlertTriangle, Layers, GitBranch, Folder, Globe, Wrench } from 'lucide-react';
import { Service } from '../../types';
import { fetchServiceCompat } from '../../services/api';

interface ServiceDetailModalProps {
  service: Service | null;
  onClose: () => void;
  onDeploy: (serviceId: string) => void;
}

export const ServiceDetailModal: React.FC<ServiceDetailModalProps> = ({
  service,
  onClose,
  onDeploy,
}) => {
  const [compat, setCompat] = useState<{
    compatible: boolean;
    message: string;
    required_changes: string[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (service) {
      setLoading(true);
      fetchServiceCompat(service.id)
        .then((data) => setCompat(data))
        .catch(() => setCompat(null))
        .finally(() => setLoading(false));
    }
  }, [service]);

  if (!service) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#161b22] border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
              <Layers className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{service.name}</h2>
              <p className="text-xs text-slate-400 font-mono">{service.path}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto space-y-6 text-sm">
          {/* Phase 3 Compatibility Box */}
          <div
            className={`p-4 rounded-xl border ${
              compat?.compatible
                ? 'bg-emerald-950/20 border-emerald-800/40 text-emerald-300'
                : 'bg-amber-950/20 border-amber-800/40 text-amber-300'
            }`}
          >
            <div className="flex items-start space-x-3">
              {compat?.compatible ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              )}
              <div className="space-y-2">
                <h4 className="font-semibold text-white">
                  {compat?.compatible ? 'Standardized Deployment Ready' : 'Deployment Compatibility Notice'}
                </h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {compat?.message || 'Inspecting deployment structure against the reference model...'}
                </p>

                {compat?.required_changes && compat.required_changes.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-amber-800/30">
                    <p className="text-xs font-semibold text-amber-400 mb-1.5">Required Changes to Standardize:</p>
                    <ul className="list-disc list-inside space-y-1 text-xs text-slate-300">
                      {compat.required_changes.map((change, idx) => (
                        <li key={idx}>{change}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Configuration Grid */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-[#0d1117] p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block mb-1">Deployment Architecture:</span>
              <span className="font-mono text-cyan-400 font-semibold">{service.deployment_type}</span>
            </div>

            <div className="bg-[#0d1117] p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block mb-1">Compose File:</span>
              <span className="font-mono text-slate-300">{service.compose_file}</span>
            </div>

            <div className="bg-[#0d1117] p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block mb-1">Git Repository:</span>
              <span className="font-mono text-slate-300 truncate block">
                {service.repository || 'None configured (prebuilt images)'}
              </span>
            </div>

            <div className="bg-[#0d1117] p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 block mb-1">Health Endpoint:</span>
              <span className="font-mono text-slate-300 truncate block">
                {service.health_url || 'Container daemon check'}
              </span>
            </div>
          </div>

          {/* Connected Containers */}
          {service.containers && service.containers.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Running Containers ({service.containers.length})
              </h4>
              <div className="space-y-1.5 font-mono text-xs">
                {service.containers.map((c) => (
                  <div
                    key={c.id || c.name}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-[#0d1117] border border-slate-800"
                  >
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      <span className="text-white font-medium">{c.name}</span>
                    </div>
                    <span className="text-slate-400 text-[11px]">{c.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-[#0d1117]/60 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
          >
            Close
          </button>
          <button
            onClick={() => {
              onClose();
              onDeploy(service.id);
            }}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-slate-950 transition shadow-lg shadow-cyan-500/20"
          >
            Trigger Action in AI Agent
          </button>
        </div>
      </div>
    </div>
  );
};

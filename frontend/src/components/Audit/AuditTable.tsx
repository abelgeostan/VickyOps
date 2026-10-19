import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, Search, Clock, Terminal, ChevronDown, ChevronUp } from 'lucide-react';
import { AuditRecord } from '../../types';

interface AuditTableProps {
  logs: AuditRecord[];
  isLoading: boolean;
  onRefresh: () => void;
}

export const AuditTable: React.FC<AuditTableProps> = ({ logs, isLoading, onRefresh }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);

  const filteredLogs = logs.filter((l) => {
    const term = searchTerm.toLowerCase();
    return (
      l.tool_name.toLowerCase().includes(term) ||
      (l.service_id && l.service_id.toLowerCase().includes(term)) ||
      (l.user_request && l.user_request.toLowerCase().includes(term)) ||
      (l.agent_plan && l.agent_plan.toLowerCase().includes(term))
    );
  });

  return (
    <div className="bg-[#161b22] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
      {/* Table Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span>Immutable Audit Log</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Every executed backend tool, user prompt, approval status, and duration is permanently recorded.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by tool or service..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition w-56"
            />
          </div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-[#0d1117] text-slate-400 font-mono uppercase text-[10px] tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Timestamp</th>
              <th className="py-3 px-4">Tool</th>
              <th className="py-3 px-4">Service</th>
              <th className="py-3 px-4">Approval</th>
              <th className="py-3 px-4">Duration</th>
              <th className="py-3 px-4">Result</th>
              <th className="py-3 px-4 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 font-mono">
            {filteredLogs.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-8 text-slate-500">
                  {isLoading ? 'Loading audit records...' : 'No audit records found.'}
                </td>
              </tr>
            ) : (
              filteredLogs.map((log) => {
                const isSuccess = log.final_result === 'success';
                const isExpanded = selectedRecord?.id === log.id;
                return (
                  <React.Fragment key={log.id}>
                    <tr className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-semibold text-cyan-400">{log.tool_name}</td>
                      <td className="py-3 px-4 text-slate-300">{log.service_id || '—'}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] ${
                            log.approval_status === 'manually_approved'
                              ? 'bg-purple-950 text-purple-300 border border-purple-800'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {log.approval_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{(log.duration_ms / 1000).toFixed(2)}s</td>
                      <td className="py-3 px-4">
                        <span
                          className={`flex items-center space-x-1 ${
                            isSuccess ? 'text-emerald-400' : 'text-rose-400'
                          }`}
                        >
                          {isSuccess ? (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          ) : (
                            <XCircle className="w-3.5 h-3.5" />
                          )}
                          <span className="capitalize">{log.final_result}</span>
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedRecord(isExpanded ? null : log)}
                          className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition"
                        >
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Detail Row */}
                    {isExpanded && (
                      <tr className="bg-slate-950/80">
                        <td colSpan={7} className="p-4 space-y-2 border-b border-slate-800">
                          <div className="grid grid-cols-2 gap-4 text-xs font-sans">
                            <div>
                              <span className="text-slate-500 font-semibold block mb-1">User Prompt:</span>
                              <p className="text-slate-300 font-mono bg-slate-900 p-2 rounded-lg border border-slate-800">
                                {log.user_request || 'Direct Dashboard Execution'}
                              </p>
                            </div>
                            <div>
                              <span className="text-slate-500 font-semibold block mb-1">Agent Plan:</span>
                              <p className="text-slate-300 font-mono bg-slate-900 p-2 rounded-lg border border-slate-800">
                                {log.agent_plan || 'Direct Tool Invocation'}
                              </p>
                            </div>
                          </div>

                          {/* Raw Output Log */}
                          <div>
                            <span className="text-slate-500 font-semibold block mb-1 font-sans">
                              Execution Output / Telemetry:
                            </span>
                            <pre className="p-3 bg-slate-900 text-slate-300 rounded-lg font-mono text-[11px] whitespace-pre-wrap max-h-48 overflow-y-auto border border-slate-800">
                              {log.output || log.error || 'No output text returned.'}
                            </pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

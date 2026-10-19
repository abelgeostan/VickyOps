import React from 'react';
import {
  Circle,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Terminal,
  Check,
  Ban,
} from 'lucide-react';
import { Operation, StepDetail } from '../../types';

interface OperationTimelineProps {
  operation: Operation | null;
  onApprove?: (operationId: string) => void;
  onReject?: (operationId: string) => void;
  isDeciding?: boolean;
}

export const OperationTimeline: React.FC<OperationTimelineProps> = ({
  operation,
  onApprove,
  onReject,
  isDeciding,
}) => {
  if (!operation) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center text-slate-500 bg-[#161b22] border border-slate-800 rounded-2xl">
        <Terminal className="w-10 h-10 mb-3 text-slate-600" />
        <h4 className="font-semibold text-slate-300">No Active Operation</h4>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          Select an action like "Deploy Update" from a service card or ask the AI DevOps assistant to execute a workflow.
        </p>
      </div>
    );
  }

  const isRequiresApproval = operation.status === 'requires_approval';
  const isRunning = operation.status === 'running';
  const isCompleted = operation.status === 'completed';
  const isFailed = operation.status === 'failed';

  return (
    <div className="bg-[#161b22] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-6">
      {/* Top Status Banner */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2.5">
            <h3 className="font-bold text-white text-base tracking-tight">{operation.name}</h3>
            <span
              className={`text-xs px-2.5 py-0.5 rounded-full font-medium flex items-center space-x-1.5 ${
                isRunning
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  : isCompleted
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                  : isRequiresApproval
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse'
                  : isFailed
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {isRunning && <Loader2 className="w-3 h-3 animate-spin" />}
              {isCompleted && <CheckCircle2 className="w-3 h-3" />}
              {isRequiresApproval && <AlertTriangle className="w-3 h-3" />}
              {isFailed && <XCircle className="w-3 h-3" />}
              <span className="capitalize">{operation.status.replace('_', ' ')}</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            ID: {operation.id} • Initiator: {operation.initiator}
          </p>
        </div>

        {operation.duration_seconds > 0 && (
          <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
            <Clock className="w-3.5 h-3.5" />
            <span>{operation.duration_seconds.toFixed(2)}s</span>
          </div>
        )}
      </div>

      {/* Approval Confirmation Warning Box */}
      {isRequiresApproval && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 animate-pulse-slow">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1 space-y-2">
              <h4 className="font-semibold text-sm text-white">Confirmation Required</h4>
              <p className="text-xs leading-relaxed text-amber-100">
                {operation.approval_prompt || 'This operation will modify server services and requires explicit approval.'}
              </p>
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => onApprove && onApprove(operation.id)}
                  disabled={isDeciding}
                  className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition shadow-md shadow-emerald-500/20"
                >
                  <Check className="w-4 h-4" />
                  <span>Approve & Execute</span>
                </button>
                <button
                  onClick={() => onReject && onReject(operation.id)}
                  disabled={isDeciding}
                  className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                >
                  <Ban className="w-4 h-4 text-rose-400" />
                  <span>Cancel Operation</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Live Timeline Steps */}
      <div className="space-y-4">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Execution Steps
        </h4>
        <div className="relative pl-6 space-y-6 before:absolute before:left-[11px] before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-800">
          {operation.steps?.map((step: StepDetail, idx: number) => {
            const isStepRunning = step.status === 'running';
            const isStepCompleted = step.status === 'completed';
            const isStepFailed = step.status === 'failed';
            const isStepAwaiting = step.status === 'awaiting_approval';

            return (
              <div key={idx} className="relative group">
                {/* Node icon */}
                <div
                  className={`absolute -left-[30px] top-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold z-10 transition-all ${
                    isStepCompleted
                      ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/30'
                      : isStepRunning
                      ? 'bg-cyan-500 text-slate-950 animate-pulse shadow-md shadow-cyan-500/40 ring-4 ring-cyan-500/20'
                      : isStepFailed
                      ? 'bg-rose-500 text-white shadow-md shadow-rose-500/30'
                      : isStepAwaiting
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {isStepCompleted && <CheckCircle2 className="w-3.5 h-3.5" />}
                  {isStepRunning && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  {isStepFailed && <XCircle className="w-3.5 h-3.5" />}
                  {isStepAwaiting && <AlertTriangle className="w-3.5 h-3.5" />}
                  {!isStepCompleted && !isStepRunning && !isStepFailed && !isStepAwaiting && (
                    <Circle className="w-2.5 h-2.5 text-slate-500" />
                  )}
                </div>

                {/* Step content */}
                <div className="bg-[#0d1117]/80 rounded-xl p-3 border border-slate-800/80 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-sm text-white">{step.name}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400">
                        {step.tool_name}
                      </span>
                    </div>
                    {step.duration_ms ? (
                      <span className="text-[11px] font-mono text-slate-400">
                        {(step.duration_ms / 1000).toFixed(2)}s
                      </span>
                    ) : null}
                  </div>

                  <p className="text-xs text-slate-400">{step.description}</p>

                  {/* Active running pulse text */}
                  {isStepRunning && (
                    <div className="flex items-center space-x-2 text-xs text-cyan-400 font-mono py-1.5 px-2 bg-cyan-950/40 border border-cyan-800/40 rounded-lg animate-pulse">
                      <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0 text-cyan-400" />
                      <span>Executing step: {step.name}...</span>
                    </div>
                  )}

                  {/* Step log output if completed or failed */}
                  {step.log && (
                    <div className="mt-2 pt-2 border-t border-slate-800/80 font-mono text-[11px] text-slate-300 whitespace-pre-wrap bg-slate-950/70 p-2.5 rounded-lg overflow-x-auto max-h-48 border border-slate-800">
                      {step.log}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Operation Log output */}
      {operation.output_log && (
        <div className="space-y-2 pt-4 border-t border-slate-800">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
            <Terminal className="w-3.5 h-3.5 text-cyan-400" />
            <span>Operation Summary & Logs</span>
          </h4>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/90 font-mono text-xs text-emerald-400/90 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
            {operation.output_log}
          </div>
        </div>
      )}
    </div>
  );
};

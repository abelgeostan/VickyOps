import React, { useState } from 'react';
import { HardDrive, HardDriveDownload, RotateCcw, AlertTriangle, CheckCircle2, Plus } from 'lucide-react';
import { BackupItem, Service } from '../../types';
import { createBackup, restoreBackup } from '../../services/api';

interface BackupListProps {
  backups: BackupItem[];
  services: Service[];
  onRefresh: () => void;
  isLoading: boolean;
}

export const BackupList: React.FC<BackupListProps> = ({
  backups,
  services,
  onRefresh,
  isLoading,
}) => {
  const [selectedService, setSelectedService] = useState(services[0]?.id || 'vickyai');
  const [isCreating, setIsCreating] = useState(false);
  const [restoreConfirm, setRestoreConfirm] = useState<BackupItem | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleCreate = async () => {
    const s = services.find((x) => x.id === selectedService);
    if (!s) return;
    setIsCreating(true);
    setStatusMsg(null);
    try {
      await createBackup(s.id, s.path);
      setStatusMsg({ type: 'success', text: `Backup created for ${s.name} successfully!` });
      onRefresh();
    } catch (e: any) {
      setStatusMsg({ type: 'error', text: e.message || 'Failed to create backup' });
    } finally {
      setIsCreating(false);
    }
  };

  const handleRestore = async () => {
    if (!restoreConfirm) return;
    try {
      const s = services.find((x) => restoreConfirm.filename.startsWith(x.id));
      const targetPath = s ? s.path : `/home/stan/${restoreConfirm.filename.split('_')[0]}`;
      await restoreBackup(restoreConfirm.filename, targetPath);
      setStatusMsg({ type: 'success', text: `Backup ${restoreConfirm.filename} restored successfully!` });
      setRestoreConfirm(null);
      onRefresh();
    } catch (e: any) {
      setStatusMsg({ type: 'error', text: e.message || 'Restore failed' });
    }
  };

  return (
    <div className="bg-[#161b22] border border-slate-800 rounded-2xl p-5 shadow-lg space-y-6">
      {/* Header and Create Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <HardDrive className="w-5 h-5 text-purple-400" />
            <span>Service Backups & Snapshots</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Create on-demand timestamped tar.gz archives before deployments or restore previous states.
          </p>
        </div>

        {/* Create Backup Bar */}
        <div className="flex items-center space-x-2">
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
          >
            {services.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>

          <button
            onClick={handleCreate}
            disabled={isCreating}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white transition shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>{isCreating ? 'Archiving...' : 'Create Backup'}</span>
          </button>
        </div>
      </div>

      {statusMsg && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center space-x-2 ${
            statusMsg.type === 'success'
              ? 'bg-emerald-950/30 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/30 border-rose-800 text-rose-300'
          }`}
        >
          {statusMsg.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Restore Confirmation Prompt */}
      {restoreConfirm && (
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/40 text-amber-200 space-y-3">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-sm text-white">Confirm Destructive Restore</h4>
              <p className="text-xs text-slate-300 mt-1">
                Restoring <span className="font-mono text-cyan-400 font-bold">{restoreConfirm.filename}</span> will overwrite existing service files with the snapshot data.
              </p>
              <div className="flex space-x-3 mt-3">
                <button
                  onClick={handleRestore}
                  className="px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition"
                >
                  Proceed with Restore
                </button>
                <button
                  onClick={() => setRestoreConfirm(null)}
                  className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs transition border border-slate-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Backups List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {backups.length === 0 ? (
          <div className="col-span-full text-center py-8 text-slate-500 font-mono text-xs">
            {isLoading ? 'Scanning backups...' : 'No backup archives created yet.'}
          </div>
        ) : (
          backups.map((b, idx) => (
            <div
              key={idx}
              className="bg-[#0d1117] border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between space-y-3 hover:border-slate-700 transition"
            >
              <div>
                <div className="flex items-center space-x-2 text-purple-400 mb-1.5">
                  <HardDriveDownload className="w-4 h-4" />
                  <span className="font-mono text-xs font-semibold truncate text-white">{b.filename}</span>
                </div>
                <div className="flex justify-between text-xs text-slate-400 font-mono">
                  <span>Size: {b.size}</span>
                  <span>{b.date}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-end">
                <button
                  onClick={() => setRestoreConfirm(b)}
                  className="text-xs text-amber-400 hover:text-amber-300 flex items-center space-x-1 font-semibold transition"
                >
                  <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  <span>Restore Snapshot</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

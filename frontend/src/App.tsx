import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchServices,
  fetchOperations,
  fetchOperation,
  fetchServerMetrics,
  fetchCloudflareStatus,
  fetchAuditLogs,
  fetchBackups,
  triggerServiceAction,
  decideOperation,
} from './services/api';
import { wsClient } from './services/websocket';
import { Service, Operation, ServerMetrics, CloudflareStatus, AuditRecord, BackupItem } from './types';
import { Navbar } from './components/Common/Navbar';
import { MetricCards } from './components/Dashboard/MetricCards';
import { ServiceList } from './components/Services/ServiceList';
import { ServiceDetailModal } from './components/Services/ServiceDetailModal';
import { OperationTimeline } from './components/Activity/OperationTimeline';
import { ChatDrawer } from './components/Chat/ChatDrawer';
import { AuditTable } from './components/Audit/AuditTable';
import { BackupList } from './components/Backups/BackupList';
import { Terminal, Shield, Sparkles, Layers } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [services, setServices] = useState<Service[]>([]);
  const [operations, setOperations] = useState<Operation[]>([]);
  const [activeOperation, setActiveOperation] = useState<Operation | null>(null);
  const [metrics, setMetrics] = useState<ServerMetrics | null>(null);
  const [cloudflare, setCloudflare] = useState<CloudflareStatus | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [backups, setBackups] = useState<BackupItem[]>([]);

  const [inspectService, setInspectService] = useState<Service | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isDeciding, setIsDeciding] = useState(false);

  // Load initial data
  const loadAllData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [sData, mData, cfData, opsData, auditData, bData] = await Promise.allSettled([
        fetchServices(),
        fetchServerMetrics(),
        fetchCloudflareStatus(),
        fetchOperations(),
        fetchAuditLogs(50),
        fetchBackups(),
      ]);

      if (sData.status === 'fulfilled') setServices(sData.value);
      if (mData.status === 'fulfilled') setMetrics(mData.value);
      if (cfData.status === 'fulfilled') setCloudflare(cfData.value);
      if (opsData.status === 'fulfilled') {
        setOperations(opsData.value);
        if (!activeOperation && opsData.value.length > 0) {
          setActiveOperation(opsData.value[0]);
        }
      }
      if (auditData.status === 'fulfilled') setAuditLogs(auditData.value);
      if (bData.status === 'fulfilled') setBackups(bData.value);
    } catch (e) {
      console.error('Failed to refresh data', e);
    } finally {
      setIsRefreshing(false);
    }
  }, [activeOperation]);

  useEffect(() => {
    loadAllData();
    // Refresh metrics periodically
    const interval = setInterval(loadAllData, 10000);
    return () => clearInterval(interval);
  }, []);

  // Listen to WebSocket events
  useEffect(() => {
    const unsubStep = wsClient.on('step_progress', async (data: any) => {
      if (activeOperation && activeOperation.id === data.operation_id) {
        const updated = await fetchOperation(data.operation_id);
        setActiveOperation(updated);
      }
      // Refresh operations list
      fetchOperations().then(setOperations);
    });

    const unsubOp = wsClient.on('operation_update', async (data: any) => {
      if (activeOperation && activeOperation.id === data.operation_id) {
        const updated = await fetchOperation(data.operation_id);
        setActiveOperation(updated);
      }
      fetchOperations().then(setOperations);
      fetchServices().then(setServices);
    });

    const unsubApprove = wsClient.on('operation_approval_required', async (data: any) => {
      const updated = await fetchOperation(data.operation_id);
      setActiveOperation(updated);
      setActiveTab('operations');
      fetchOperations().then(setOperations);
    });

    return () => {
      unsubStep();
      unsubOp();
      unsubApprove();
    };
  }, [activeOperation]);

  // Handler for dashboard actions: "Deploy Update", "Restart", etc.
  const handleServiceAction = async (serviceId: string, action: string) => {
    try {
      const op = await triggerServiceAction(serviceId, action);
      setActiveOperation(op);
      setActiveTab('operations'); // Core requirement: transition into activity/timeline view!
      setIsChatOpen(true); // Open AI DevOps panel so user can follow along and chat
      await fetchOperations().then(setOperations);
    } catch (e: any) {
      alert(`Action error: ${e.message}`);
    }
  };

  const handleApprove = async (opId: string) => {
    setIsDeciding(true);
    try {
      const op = await decideOperation(opId, 'approve');
      setActiveOperation(op);
      await fetchOperations().then(setOperations);
    } catch (e: any) {
      alert(`Approval error: ${e.message}`);
    } finally {
      setIsDeciding(false);
    }
  };

  const handleReject = async (opId: string) => {
    setIsDeciding(true);
    try {
      const op = await decideOperation(opId, 'reject');
      setActiveOperation(op);
      await fetchOperations().then(setOperations);
    } catch (e: any) {
      alert(`Rejection error: ${e.message}`);
    } finally {
      setIsDeciding(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0f17] text-slate-100">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        metrics={metrics}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
        onOpenChat={() => setIsChatOpen(!isChatOpen)}
        isChatOpen={isChatOpen}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8 space-y-8">
        {/* Hardware & Cloudflare Metrics Bar */}
        <section>
          <MetricCards metrics={metrics} cloudflare={cloudflare} />
        </section>

        {/* Tab 1: Dashboard / Overview */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8 animate-fade-in">
            {/* Services Grid */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                    <Layers className="w-5 h-5 text-cyan-400" />
                    <span>Configured Workloads & Services</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Select a service to inspect status, run health checks, or trigger standardized deployments.
                  </p>
                </div>
              </div>

              <ServiceList
                services={services}
                onAction={handleServiceAction}
                onViewDetails={(s) => setInspectService(s)}
                isLoading={isRefreshing}
              />
            </section>

            {/* Recent Operations Activity Widget */}
            {activeOperation && (
              <section className="space-y-3">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2">
                  <Terminal className="w-4 h-4 text-cyan-400" />
                  <span>Current / Last Activity</span>
                </h3>
                <OperationTimeline
                  operation={activeOperation}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  isDeciding={isDeciding}
                />
              </section>
            )}
          </div>
        )}

        {/* Tab 2: Services Full Page */}
        {activeTab === 'services' && (
          <section className="space-y-4 animate-fade-in">
            <div>
              <h2 className="text-lg font-bold text-white">Service Management</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Manage, deploy, and inspect configuration for all hosted Docker Compose projects.
              </p>
            </div>
            <ServiceList
              services={services}
              onAction={handleServiceAction}
              onViewDetails={(s) => setInspectService(s)}
              isLoading={isRefreshing}
            />
          </section>
        )}

        {/* Tab 3: Operations & Activity Timeline */}
        {activeTab === 'operations' && (
          <section className="space-y-6 animate-fade-in">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-cyan-400" />
                <span>Live Activity & Operation Timeline</span>
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Real-time execution telemetry, step-by-step progress streaming, and approval control.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Recent Operations list */}
              <div className="bg-[#161b22] border border-slate-800 rounded-2xl p-4 space-y-3 h-[600px] flex flex-col">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Operations History ({operations.length})
                </h3>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  {operations.map((op) => {
                    const isSelected = activeOperation?.id === op.id;
                    return (
                      <button
                        key={op.id}
                        onClick={() => setActiveOperation(op)}
                        className={`w-full text-left p-3 rounded-xl border transition flex flex-col space-y-1 ${
                          isSelected
                            ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300'
                            : 'bg-[#0d1117] border-slate-800/80 text-slate-300 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-white truncate">{op.name}</span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded capitalize font-mono ${
                              op.status === 'completed'
                                ? 'bg-emerald-950 text-emerald-400'
                                : op.status === 'running'
                                ? 'bg-cyan-950 text-cyan-400 animate-pulse'
                                : op.status === 'requires_approval'
                                ? 'bg-amber-950 text-amber-400'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {op.status}
                          </span>
                        </div>
                        <span className="text-[11px] text-slate-400 font-mono truncate">
                          {op.id} • {op.action_type}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Right Column: Timeline Detail */}
              <div className="lg:col-span-2">
                <OperationTimeline
                  operation={activeOperation}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  isDeciding={isDeciding}
                />
              </div>
            </div>
          </section>
        )}

        {/* Tab 4: Audit Log */}
        {activeTab === 'audit' && (
          <section className="animate-fade-in">
            <AuditTable
              logs={auditLogs}
              isLoading={isRefreshing}
              onRefresh={loadAllData}
            />
          </section>
        )}

        {/* Tab 5: Backups */}
        {activeTab === 'backups' && (
          <section className="animate-fade-in">
            <BackupList
              backups={backups}
              services={services}
              onRefresh={loadAllData}
              isLoading={isRefreshing}
            />
          </section>
        )}
      </main>

      {/* Service Detail Modal */}
      <ServiceDetailModal
        service={inspectService}
        onClose={() => setInspectService(null)}
        onDeploy={(id) => handleServiceAction(id, 'deploy')}
      />

      {/* Persistent ChatGPT-style AI DevOps Drawer */}
      <ChatDrawer
        isOpen={isChatOpen}
        onToggle={() => setIsChatOpen(!isChatOpen)}
        onSelectOperation={async (opId) => {
          const op = await fetchOperation(opId);
          setActiveOperation(op);
          setActiveTab('operations');
        }}
        onApproveOperation={handleApprove}
        onRejectOperation={handleReject}
      />
    </div>
  );
};

export default App;

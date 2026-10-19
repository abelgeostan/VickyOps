import {
  Service,
  Operation,
  ServerMetrics,
  CloudflareStatus,
  AuditRecord,
  BackupItem,
} from '../types';

const API_BASE = '/api';

export async function fetchServices(): Promise<Service[]> {
  const res = await fetch(`${API_BASE}/services`);
  if (!res.ok) throw new Error('Failed to fetch services');
  return res.json();
}

export async function fetchServiceCompat(serviceId: string): Promise<{
  service_id: string;
  compatible: boolean;
  model: string;
  message: string;
  required_changes: string[];
}> {
  const res = await fetch(`${API_BASE}/services/${serviceId}/compat`);
  if (!res.ok) throw new Error('Failed to fetch compatibility check');
  return res.json();
}

export async function triggerServiceAction(
  serviceId: string,
  action: string,
  params?: Record<string, any>
): Promise<Operation> {
  const res = await fetch(`${API_BASE}/services/${serviceId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, parameters: params || {} }),
  });
  if (!res.ok) throw new Error(`Failed to trigger action '${action}'`);
  return res.json();
}

export async function fetchOperations(): Promise<Operation[]> {
  const res = await fetch(`${API_BASE}/operations?limit=30`);
  if (!res.ok) throw new Error('Failed to fetch operations');
  return res.json();
}

export async function fetchOperation(operationId: string): Promise<Operation> {
  const res = await fetch(`${API_BASE}/operations/${operationId}`);
  if (!res.ok) throw new Error('Failed to fetch operation');
  return res.json();
}

export async function decideOperation(
  operationId: string,
  decision: 'approve' | 'reject',
  notes?: string
): Promise<Operation> {
  const res = await fetch(`${API_BASE}/operations/${operationId}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, notes }),
  });
  if (!res.ok) throw new Error('Failed to submit approval decision');
  return res.json();
}

export async function sendChatMessage(message: string): Promise<{
  reply: string;
  operation_id?: string;
  requires_approval: boolean;
  approval_prompt?: string;
  plan_title?: string;
  steps: any[];
}> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error('Chat request failed');
  return res.json();
}

export async function fetchServerMetrics(): Promise<ServerMetrics> {
  const res = await fetch(`${API_BASE}/metrics/server`);
  if (!res.ok) throw new Error('Failed to fetch server metrics');
  return res.json();
}

export async function fetchCloudflareStatus(): Promise<CloudflareStatus> {
  const res = await fetch(`${API_BASE}/metrics/cloudflare`);
  if (!res.ok) throw new Error('Failed to fetch Cloudflare status');
  return res.json();
}

export async function fetchAuditLogs(limit = 100, serviceId?: string): Promise<AuditRecord[]> {
  const url = new URL(`${API_BASE}/audit`, window.location.origin);
  url.searchParams.set('limit', String(limit));
  if (serviceId) url.searchParams.set('service_id', serviceId);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch audit logs');
  return res.json();
}

export async function fetchBackups(): Promise<BackupItem[]> {
  const res = await fetch(`${API_BASE}/backups`);
  if (!res.ok) throw new Error('Failed to fetch backups');
  const data = await res.json();
  return data.backups || [];
}

export async function createBackup(serviceId: string, servicePath: string): Promise<any> {
  const res = await fetch(`${API_BASE}/backups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ service_id: serviceId, service_path: servicePath }),
  });
  if (!res.ok) throw new Error('Failed to create backup');
  return res.json();
}

export async function restoreBackup(filename: string, targetPath: string): Promise<any> {
  const res = await fetch(`${API_BASE}/backups/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ backup_filename: filename, target_path: targetPath }),
  });
  if (!res.ok) throw new Error('Failed to restore backup');
  return res.json();
}

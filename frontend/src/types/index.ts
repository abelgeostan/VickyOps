export interface ContainerInfo {
  id: string;
  name: string;
  image: string;
  status: string;
  state?: string;
  ports?: string;
  created?: string;
}

export interface Service {
  id: string;
  name: string;
  description?: string;
  repository?: string;
  branch: string;
  path: string;
  compose_file: string;
  health_url?: string;
  deployment_type: string;
  requires_approval: boolean;
  status: 'running' | 'stopped' | 'degraded' | 'unknown';
  docker_status?: string;
  current_commit?: string;
  remote_commit?: string;
  last_deployment?: string;
  health_status?: string;
  containers: ContainerInfo[];
}

export interface StepDetail {
  step_index: number;
  name: string;
  tool_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'awaiting_approval' | 'skipped';
  description: string;
  log?: string;
  duration_ms?: number;
}

export interface Operation {
  id: string;
  name: string;
  service_id?: string;
  action_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'requires_approval' | 'cancelled';
  initiator: string;
  prompt?: string;
  current_step_index: number;
  current_step_name?: string;
  requires_approval: string;
  approval_prompt?: string;
  approval_status: 'not_required' | 'awaiting' | 'approved' | 'rejected';
  steps: StepDetail[];
  output_log?: string;
  error_details?: string;
  duration_seconds: number;
  created_at?: string;
}

export interface ServerMetrics {
  hostname: string;
  uptime: string;
  kernel: string;
  docker_version: string;
  cpu_percent: number;
  cpu_load: { load1: number; load5: number; load15: number };
  ram: { percent: number; used_human: string; total_human: string; used_bytes?: number; total_bytes?: number };
  disk: { percent: number; used_human: string; total_human: string };
  network: { rx_human: string; tx_human: string };
}

export interface CloudflareTunnel {
  name: string;
  status: string;
  is_connected: boolean;
  health: string;
}

export interface CloudflareStatus {
  tunnel_count: number;
  active_count: number;
  overall_status: string;
  tunnels: CloudflareTunnel[];
}

export interface AuditRecord {
  id: number;
  timestamp: string;
  operation_id?: string;
  user_request?: string;
  agent_plan?: string;
  tool_name: string;
  service_id?: string;
  parameters: Record<string, any>;
  approval_status: string;
  output?: string;
  error?: string;
  exit_code: number;
  duration_ms: number;
  final_result: string;
}

export interface BackupItem {
  filename: string;
  size: string;
  date: string;
  path: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  operation_id?: string;
  requires_approval?: boolean;
  approval_prompt?: string;
  plan_title?: string;
  steps?: StepDetail[];
}

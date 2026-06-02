import { client } from '@/lib/api';

export type MaintenanceLanguage = 'en' | 'zh';

export type MaintenanceSignal = {
  id: string;
  category: string;
  title: string;
  description: string;
  responsibility: string;
  cadence: string;
  evidence_paths: string[];
  weight: number;
};

export type MaintenanceEvidenceProfile = {
  project: {
    name: string;
    display_name: string;
    repository_url: string;
    domain: string;
  };
  maintainer_role: string;
  evidence_score: number;
  active_maintenance_summary: string;
  form_answer: string;
  signals: MaintenanceSignal[];
  responsibilities: string[];
  release_management: {
    current_stage: string;
    release_readiness_controls: string[];
    client_delivery_policy: string;
  };
  application_guardrails: string[];
};

type MaintenanceEvidenceResponse = {
  success: boolean;
  data: MaintenanceEvidenceProfile;
};

export type ReleaseValidationState = 'pass' | 'fail' | 'not_run' | 'waived';

export type ReleaseCheck = {
  id: string;
  title: string;
  category: string;
  required: boolean;
  owner: string;
  evidence_paths: string[];
  validation_command?: string | null;
  manual_note?: string | null;
  validation_state: ReleaseValidationState;
  blocks_release: boolean;
};

export type ReleaseReadinessResult = {
  status: string;
  release_allowed: boolean;
  required_check_count: number;
  passed_or_waived_required_count: number;
  blocking_check_ids: string[];
  failed_check_ids: string[];
  not_run_check_ids: string[];
  checks: ReleaseCheck[];
  summary: string;
};

export type ReleaseValidationCommand = {
  check_id: string;
  command: string;
};

type ReleaseReadinessResponse = {
  success: boolean;
  data: ReleaseReadinessResult;
  validation_commands: ReleaseValidationCommand[];
};

export async function getMaintenanceEvidence(language: MaintenanceLanguage): Promise<MaintenanceEvidenceProfile> {
  const resp = await client.apiCall.invoke({
    url: `/api/v1/maintenance/oss-evidence?language=${language}`,
    method: 'GET',
  });
  const payload = (resp?.data ?? resp) as MaintenanceEvidenceResponse | MaintenanceEvidenceProfile;
  if ('success' in payload && 'data' in payload) {
    return payload.data;
  }
  return payload as MaintenanceEvidenceProfile;
}

export async function getReleaseReadiness(): Promise<ReleaseReadinessResponse> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/maintenance/release-readiness',
    method: 'GET',
  });
  return (resp?.data ?? resp) as ReleaseReadinessResponse;
}

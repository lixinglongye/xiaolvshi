import { client } from '@/lib/api';

export type FeedbackCapturePlan = {
  status: 'ready_to_create' | 'needs_context' | string;
  capture_summary: {
    priority: string;
    assignee: string;
    sla_hours: number;
    linked_need_id?: string | null;
    roadmap_alignment_status?: string | null;
    release_gate_links: string[];
    missing_required_fields: string[];
    high_risk: boolean;
  };
  ticket_defaults: {
    status: string;
    priority: string;
    assignee: string;
    resolution_note: string;
  };
  roadmap_alignment: {
    status?: string;
    top_need_id?: string | null;
    match_count: number;
    recommended_actions: string[];
  };
  lifecycle: {
    state?: string;
    next_allowed_states: string[];
    blocking_check_ids: string[];
    required_actions: string[];
  };
  public_acknowledgement: string;
  privacy_boundary: {
    stores_raw_feedback: boolean;
    returns_raw_feedback_text: boolean;
    calls_ai_model: boolean;
    calls_external_network: boolean;
    writes_database: boolean;
  };
};

type FeedbackCapturePlanResponse = {
  data?: FeedbackCapturePlan;
};

export type FeedbackCapturePlanRequest = {
  category: string;
  content: string;
  affected_artifact_id?: string;
  account_context?: string;
};

export async function previewFeedbackCapturePlan(
  data: FeedbackCapturePlanRequest,
): Promise<FeedbackCapturePlan> {
  const resp = await client.apiCall.invoke({
    url: '/api/v1/entities/feedback_tickets/capture-plan',
    method: 'POST',
    data,
  });
  return ((resp as FeedbackCapturePlanResponse)?.data ?? resp) as FeedbackCapturePlan;
}

export type ActionType = "auto_match" | "review_weak" | "review_ambiguous" | "no_match";

export interface RecordData {
  record_id: string;
  vendor_name: string | null;
  reference: string | null;
  amount: string;
  record_date: string;
  tax_identity: string | null;
}

export interface EvaluatedHypothesis {
  hypothesis_identity: string[][];
  eligibility: string;
  semantic_findings: string[];
  base_score: number | null; // e.g. 10000 for 1.0, to be divided by 10000
  coverage: number | null;
  relationship_score: number | null;
  provider_projection_identities: string[];
}

export interface ExplanationNode {
  type: string;
  text: string;
  children: ExplanationNode[];
}

export interface ReviewPacket {
  packet_id: string;
  action: ActionType;
  headline: string;
  purchases: RecordData[];
  gsts: RecordData[];
  explanation: ExplanationNode | null;
  competitors: any[];
}

export interface AutoMatch {
  action: ActionType;
  selected_hypothesis: EvaluatedHypothesis;
  rationale: string;
}

export interface DecisionTrace {
  trace_id: string;
  engine_version: string;
  config_hash: string;
  events: any[];
}

export interface ReconciliationResult {
  auto_matches: AutoMatch[];
  review_packets: ReviewPacket[];
  traces: DecisionTrace[];
  engine_version: string;
  differential_results: any[];
}

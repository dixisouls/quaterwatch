// ── Auth ─────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

// ── Jobs ──────────────────────────────────────────────────────

export type JobStatus =
  | "pending"
  | "processing"
  | "awaiting_upload"
  | "complete"
  | "failed";

export type Quarter = "Q1" | "Q2" | "Q3" | "Q4";

export interface JobStatusResponse {
  id: string;
  status: JobStatus;
  ticker: string;
  quarter: Quarter;
  year: number;
  error_message: string | null;
  segmentation_notice: string | null;
  pipeline_stage: number | null;
  created_at: string;
}

export interface JobListItem {
  id: string;
  ticker: string;
  quarter: Quarter;
  year: number;
  status: JobStatus;
  created_at: string;
}

// ── Pipeline Results ──────────────────────────────────────────

export type SentimentStatus = "available" | "insufficient_data" | "unavailable";
export type ScoringMethod = "gemini" | "heuristic";
export type SummaryMethod = "generative" | "extractive";
export type FaithfulnessStatus = "verified" | "partially_verified" | "unverified";

export interface SentimentResult {
  status: SentimentStatus;
  score: number | null;
  magnitude: number | null;
}

export interface ConfidenceResult {
  score: number | null;
  scoring_method: ScoringMethod;
  key_phrases: string[] | null;
  hedging_phrases: string[] | null;
}

export interface Entity {
  name: string;
  entity_type: string | null;
  source: string | null;
  salience: number | null;
}

export interface Summary {
  text: string;
  key_points: string[] | null;
  summary_method: SummaryMethod;
  faithfulness_score: number | null;
  faithfulness_status: FaithfulnessStatus;
  flagged_claims: string[] | null;
}

export interface Segment {
  id: string;
  name: string;
  order_index: number;
  text: string;
  word_count: number;
  sentiment: SentimentResult | null;
  confidence: ConfidenceResult | null;
  entities: Entity[];
  summary: Summary | null;
}

export interface PriceData {
  call_date: string | null;
  price_on_call_date: number | null;
  price_day_after: number | null;
  price_week_after: number | null;
  price_available: boolean;
}

export interface JobResults {
  job_id: string;
  ticker: string;
  quarter: Quarter;
  year: number;
  status: JobStatus;
  segmentation_notice: string | null;
  segments: Segment[];
  price_data: PriceData | null;
}

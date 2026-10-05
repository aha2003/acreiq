export interface TimeSeriesPoint {
  month_year?: string;
  period?: string;
  volume?: number;
  total_volume?: number;
  monthly_avg_sqm?: number;
  overall_price_sqm?: number;
  ready_avg_sqm?: number;
  ready_price_sqm?: number;
  offplan_avg_sqm?: number;
  offplan_price_sqm?: number;
  area1_name?: string;
  area2_name?: string;
  area1_avg_sqm?: number;
  area2_avg_sqm?: number;
  area1_volume?: number;
  area2_volume?: number;
}

export interface MarketSignal {
  type: string;
  severity: string;
  title: string;
  period: string;
  description: string;
  drilldown_prompt: string;
}

export interface PeriodDelta {
  start_period: string;
  end_period: string;
  volume_change_pct: number;
  price_sqm_change_pct: number;
  start_price_sqm?: number;
  end_price_sqm?: number;
}

export interface AuditCheckItem {
  name: string;
  passed: boolean;
  detail: string;
}

export interface ChatResponse {
  request_id: string;
  is_grounded: boolean;
  final_output: string;
  discrepancies: string[];
  source_trace_ids: string[];
  latency_ms: number;
  timeseries?: TimeSeriesPoint[];
  market_signals?: MarketSignal[];
  delta?: PeriodDelta;
  audit_checks?: AuditCheckItem[];
  suggested_prompts?: string[];
  is_comparison?: boolean;
  area1_label?: string;
  area2_label?: string;
}
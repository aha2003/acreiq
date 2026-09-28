export interface TimeSeriesPoint {
  month_year: string;
  volume: number;
  monthly_avg_price: number;
  monthly_median_price: number;
  monthly_avg_sqm: number;
  ready_avg_sqm?: number;
  offplan_avg_sqm?: number;
}

export interface ChatResponse {
  request_id: string;
  is_grounded: boolean;
  final_output: string;
  discrepancies: string[];
  source_trace_ids: string[];
  latency_ms: number;
  timeseries?: TimeSeriesPoint[];
}
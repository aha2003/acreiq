import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Bar, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { 
  ShieldCheck, 
  AlertTriangle, 
  Clock, 
  Database, 
  Search, 
  Building2, 
  TrendingUp,
  Calendar,
  Layers
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ChatResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/v1/chat";

export default function App() {
  const [baseArea, setBaseArea] = useState("Business Bay");
  const [timeHorizon, setTimeHorizon] = useState<"ALL" | "1Y" | "6M" | "3M">("ALL");
  const [marketType, setMarketType] = useState<"ALL" | "Ready" | "Off-Plan">("ALL");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);

  const executeSearch = async (area: string, horizon: string, market: string) => {
    setLoading(true);
    setError(null);

    // Build natural-language prompt containing temporal and segmentation modifiers
    let constructedQuery = `Summarize transaction prices in ${area}`;
    if (market !== "ALL") {
      constructedQuery += ` for ${market} properties`;
    }
    if (horizon === "3M") {
      constructedQuery += " over the last 3 months";
    } else if (horizon === "6M") {
      constructedQuery += " over the last 6 months";
    } else if (horizon === "1Y") {
      constructedQuery += " in the past year";
    }

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: constructedQuery }),
      });

      if (!res.ok) {
        throw new Error(`API returned ${res.status}: ${res.statusText}`);
      }

      const data: ChatResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to reach AcreIQ API");
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!baseArea.trim()) return;
    executeSearch(baseArea, timeHorizon, marketType);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 flex justify-between items-center sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 font-bold">
            A
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight text-white flex items-center gap-2">
              AcreIQ Terminal
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                v1.1 DLD Segmented
              </span>
            </h1>
            <p className="text-xs text-slate-400">Deterministic UAE Real Estate Market Operations</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            DuckDB Engine Active
          </span>
          <span className="hidden sm:inline text-slate-500">|</span>
          <span className="text-slate-400 hidden sm:inline">me-central1 (Dubai)</span>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm flex flex-col gap-3">
          <form onSubmit={handleFormSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3.5 text-slate-500" size={16} />
              <input
                type="text"
                value={baseArea}
                onChange={(e) => setBaseArea(e.target.value)}
                placeholder="Enter community (e.g. 'Business Bay', 'Dubai Marina', 'Wadi Al Safa')..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition-colors"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold px-6 py-2.5 rounded-lg text-sm transition-colors disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  Auditing DLD...
                </>
              ) : (
                "Query Registry"
              )}
            </button>
          </form>

          {/* Filter Toolbar: Community Chips + Time Horizon + Market Segment */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-slate-800/60 text-xs">
            {/* Quick Communities */}
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <span className="text-slate-500 font-medium">Areas:</span>
              {["Business Bay", "Wadi Al Safa", "Nad Al Sheba", "Dubai Marina", "Downtown Dubai"].map((area) => (
                <button
                  key={area}
                  type="button"
                  onClick={() => {
                    setBaseArea(area);
                    executeSearch(area, timeHorizon, marketType);
                  }}
                  className={`px-2 py-0.5 rounded border transition-colors cursor-pointer whitespace-nowrap ${
                    baseArea.toLowerCase() === area.toLowerCase()
                      ? "bg-cyan-950 border-cyan-800 text-cyan-400 font-medium"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {area}
                </button>
              ))}
            </div>

            {/* Time Horizon & Market Type Toggles */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Market Type */}
              <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 p-0.5 rounded-lg">
                <Layers size={13} className="text-slate-500 ml-1.5" />
                {(["ALL", "Ready", "Off-Plan"] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => {
                      setMarketType(type);
                      executeSearch(baseArea, timeHorizon, type);
                    }}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
                      marketType === type
                        ? "bg-slate-800 text-cyan-400 shadow-sm"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {type === "ALL" ? "All Types" : type}
                  </button>
                ))}
              </div>

              {/* Time Duration */}
              <div className="flex items-center gap-1 bg-slate-950 border border-slate-800 p-0.5 rounded-lg">
                <Calendar size={13} className="text-slate-500 ml-1.5" />
                {(["ALL", "1Y", "6M", "3M"] as const).map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => {
                      setTimeHorizon(h);
                      executeSearch(baseArea, h, marketType);
                    }}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors cursor-pointer ${
                      timeHorizon === h
                        ? "bg-slate-800 text-cyan-400 shadow-sm"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {h === "ALL" ? "All Time" : h}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {error && (
          <div className="p-4 bg-rose-950/50 border border-rose-900 rounded-xl text-rose-300 text-sm flex items-center gap-2">
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span
                  className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${
                    result.is_grounded
                      ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                      : "bg-rose-950 text-rose-400 border border-rose-800"
                  }`}
                >
                  {result.is_grounded ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
                  {result.is_grounded ? "AUDITOR VERIFIED (0 DISCREPANCIES)" : "GROUNDING FAILED"}
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
                  <Clock size={12} /> {result.latency_ms}ms
                </span>
              </div>

              <div className="text-sm text-slate-300 leading-relaxed font-sans space-y-2 [&>p]:mb-2 [&>ul]:list-disc [&>ul]:ml-5 [&>ul>li]:mb-1 [&>strong]:text-slate-100">
                <ReactMarkdown>{result.final_output}</ReactMarkdown>
              </div>

              {result.discrepancies.length > 0 && (
                <div className="bg-rose-950/30 border border-rose-900/60 p-3 rounded-lg text-xs text-rose-300">
                  <p className="font-semibold mb-1">Auditor Discrepancy Log:</p>
                  <ul className="list-disc list-inside space-y-0.5">
                    {result.discrepancies.map((d, i) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="border-t border-slate-800 pt-3">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Database size={13} /> Official DLD Registry Trace IDs
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.source_trace_ids.map((id) => (
                    <span
                      key={id}
                      className="font-mono text-[11px] bg-slate-950 border border-slate-800 px-2 py-0.5 rounded text-cyan-400"
                    >
                      {id}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <TrendingUp size={15} className="text-cyan-400" />
                    Market Dynamics: Price / m² & Volume
                  </h3>
                  <p className="text-[11px] text-slate-500">Segmented Ready vs. Off-Plan trajectories</p>
                </div>
                <span className="text-xs text-slate-500 font-mono">DLD Registry Timeseries</span>
              </div>

              {result.timeseries && result.timeseries.length > 0 ? (
                <div className="h-72 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={result.timeseries}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                      <XAxis 
                        dataKey="month_year" 
                        stroke="#64748b" 
                        fontSize={11} 
                        tickLine={false} 
                      />
                      <YAxis 
                        yAxisId="left" 
                        stroke="#06b6d4" 
                        fontSize={11} 
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                      />
                      <YAxis 
                        yAxisId="right" 
                        orientation="right" 
                        stroke="#64748b" 
                        fontSize={11} 
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: "#020617", 
                          borderColor: "#334155", 
                          borderRadius: "8px",
                          fontSize: "12px" 
                        }} 
                      />
                      <Legend 
                        wrapperStyle={{ fontSize: "11px", paddingTop: "12px", color: "#94a3b8" }} 
                        formatter={(value) => <span className="text-slate-300 font-medium">{value}</span>}
                      />
                      <Bar 
                        yAxisId="right" 
                        dataKey="volume" 
                        name="Volume (Deals)" 
                        fill="#1e293b" 
                        stroke="#334155"
                        radius={[4, 4, 0, 0]} 
                      />
                      {(marketType === "ALL" || marketType === "Ready") && (
                        <Line 
                          yAxisId="left" 
                          type="monotone" 
                          dataKey="ready_avg_sqm" 
                          name="Ready (AED/m²)" 
                          stroke="#06b6d4" 
                          strokeWidth={2} 
                          connectNulls={true}
                          dot={{ fill: "#06b6d4", r: 4 }} 
                        />
                      )}
                      {(marketType === "ALL" || marketType === "Off-Plan") && (
                        <Line 
                          yAxisId="left" 
                          type="monotone" 
                          dataKey="offplan_avg_sqm" 
                          name="Off-Plan (AED/m²)" 
                          stroke="#f59e0b" 
                          strokeWidth={2} 
                          connectNulls={true}
                          dot={{ fill: "#f59e0b", r: 4 }} 
                        />
                      )}
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-72 border border-dashed border-slate-800 rounded-lg text-slate-500 text-xs">
                  <Building2 size={24} className="mb-2 opacity-50" />
                  No monthly timeseries breakdown available for this query slice.
                </div>
              )}

              {result.timeseries && result.timeseries.length > 0 && (
                <div className="grid grid-cols-3 gap-3 border-t border-slate-800 pt-3">
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                  <p className="text-[10px] text-slate-500 uppercase font-mono">Period Buckets</p>
                  <p className="text-sm font-semibold text-slate-200 mt-0.5">{result.timeseries.length} Months</p>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                  <p className="text-[10px] text-slate-500 uppercase font-mono">Peak Ready Rate</p>
                  <p className="text-sm font-semibold text-cyan-400 mt-0.5">
                    {Math.max(...result.timeseries.map(t => t.ready_avg_sqm || 0)) > 0 
                      ? `AED ${Math.max(...result.timeseries.map(t => t.ready_avg_sqm || 0)).toLocaleString()}/m²`
                      : "N/A (Off-Plan Slice)"}
                  </p>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                  <p className="text-[10px] text-slate-500 uppercase font-mono">Peak Off-Plan Rate</p>
                  <p className="text-sm font-semibold text-amber-400 mt-0.5">
                    {Math.max(...result.timeseries.map(t => t.offplan_avg_sqm || 0)) > 0 
                      ? `AED ${Math.max(...result.timeseries.map(t => t.offplan_avg_sqm || 0)).toLocaleString()}/m²`
                      : "N/A (Ready Slice)"}
                  </p>
                </div>
              </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
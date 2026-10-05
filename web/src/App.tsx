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
  TrendingDown,
  Sparkles,
  Compass,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  ArrowRight,
  GitCompare
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ChatResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080/v1/chat";

export default function App() {
  const [queryInput, setQueryInput] = useState("Compare price/m² trends between Business Bay and Al Furjan");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [auditExpanded, setAuditExpanded] = useState(false);

  const executeSearch = async (promptText: string) => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: promptText }),
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
    if (!queryInput.trim()) return;
    executeSearch(queryInput);
  };

  const parseSections = (text: string) => {
    if (!text) return { summary: "", advice: "" };
    const parts = text.split(/Market advice:|Strategic Investor Advisory:|Strategic Advisory:/i);
    if (parts.length > 1) {
      return { summary: parts[0].trim(), advice: parts[1].trim() };
    }
    return { summary: text, advice: "" };
  };

  const { summary, advice } = result ? parseSections(result.final_output) : { summary: "", advice: "" };

  // Detect whether backend payload is in comparison mode
  const isComparisonMode = Boolean(
    result?.is_comparison || 
    (result?.timeseries && result.timeseries.length > 0 && result.timeseries[0].area1_avg_sqm !== undefined)
  );

  const area1Title = result?.area1_label || result?.timeseries?.[0]?.area1_name || "Primary Area";
  const area2Title = result?.area2_label || result?.timeseries?.[0]?.area2_name || "Secondary Area";

  return (
    <div className="min-h-screen bg-[#FAF9F5] text-[#191919] flex flex-col font-sans selection:bg-[#E8E6DF]">
      {/* Top Header */}
      <header className="border-b border-[#E5E3DC] bg-[#FAF9F5]/90 backdrop-blur px-8 py-4 flex justify-between items-center sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-md bg-[#191919] text-[#FAF9F5] flex items-center justify-center font-serif font-bold text-sm shadow-sm">
            A
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-tight text-[#191919] flex items-center gap-2">
              AcreIQ Terminal
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-[#EDECE6] text-[#66645E] border border-[#DDDCD5]">
                v1.2 In-Memory OLAP
              </span>
            </h1>
            <p className="text-[11px] text-[#73716B]">Institutional DLD Market Intelligence & Quantitative Audit</p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 text-[#2B6E44] bg-[#EBF4EE] px-2.5 py-1 rounded-md border border-[#D1E6D8]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#2B6E44] animate-pulse" />
            DuckDB Active
          </span>
          <span className="text-[#DDDCD5]">|</span>
          <span className="text-[#8C8980]">me-central1</span>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto p-8 flex flex-col gap-6">
        {/* Search & Natural Language Query Console */}
        <section className="bg-white border border-[#E5E3DC] rounded-xl p-5 shadow-[0_1px_3px_rgba(0,0,0,0.03)] flex flex-col gap-4">
          <form onSubmit={handleFormSubmit} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3.5 text-[#8C8980]" size={16} />
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Ask AcreIQ (e.g. 'Compare price/m² trends between Business Bay and Al Furjan')..."
                className="w-full bg-[#FAF9F5] border border-[#DDDCD5] rounded-lg pl-10 pr-4 py-2.5 text-sm text-[#191919] placeholder-[#8C8980] focus:outline-none focus:border-[#191919] focus:bg-white transition-all shadow-inner"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-[#191919] hover:bg-[#33312E] text-[#FAF9F5] font-medium px-6 py-2.5 rounded-lg text-sm transition-all disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer shadow-sm"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-[#FAF9F5] border-t-transparent rounded-full animate-spin" />
                  Auditing DLD...
                </>
              ) : (
                "Analyze Market"
              )}
            </button>
          </form>

          {/* Quick Filter Areas & Dynamic Suggestions */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#F0EFEA] text-xs">
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <span className="text-[#8C8980] font-medium">Quick Areas:</span>
              {["Al Furjan", "Business Bay", "Dubai Marina", "Downtown Dubai"].map((area) => (
                <button
                  key={area}
                  type="button"
                  onClick={() => {
                    const q = `Summarize transaction prices and market advice in ${area} over the last 6 months`;
                    setQueryInput(q);
                    executeSearch(q);
                  }}
                  className="px-2.5 py-1 rounded-md border border-[#E5E3DC] bg-[#FAF9F5] hover:bg-[#F3F1EC] text-[#595752] transition-colors cursor-pointer text-[11px]"
                >
                  {area}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 overflow-x-auto">
              <span className="text-[#8C8980] font-medium hidden md:inline">Suggested:</span>
              {(result?.suggested_prompts && result.suggested_prompts.length > 0
                ? result.suggested_prompts
                : [
                    "Compare price/m² trends between Business Bay and Al Furjan",
                    "Why did transaction volume spike in June for Al Furjan?",
                  ]
              ).slice(0, 2).map((prompt, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setQueryInput(prompt);
                    executeSearch(prompt);
                  }}
                  className="text-[11px] text-[#9E5D2A] hover:text-[#7D461D] bg-[#FDF8F3] border border-[#F2E0D0] hover:border-[#E4C5AC] px-2.5 py-1 rounded-md flex items-center gap-1.5 cursor-pointer transition-colors"
                >
                  <span>"{prompt}"</span>
                  <ArrowRight size={11} className="shrink-0" />
                </button>
              ))}
            </div>
          </div>
        </section>

        {error && (
          <div className="p-4 bg-[#FDF2F2] border border-[#F5C2C2] rounded-xl text-[#B92B27] text-sm flex items-center gap-2">
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        {/* Market Signals Strip */}
        {result?.market_signals && result.market_signals.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {result.market_signals.map((signal, idx) => (
              <div 
                key={idx}
                className="bg-white border border-[#E5E3DC] hover:border-[#C4C2BA] transition-colors rounded-xl p-4 flex items-start justify-between gap-3 shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
              >
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#F8EFE6] text-[#9E5D2A] border border-[#EED9C7] font-semibold">
                      {signal.period}
                    </span>
                    <h4 className="text-xs font-semibold text-[#191919]">{signal.title}</h4>
                  </div>
                  <p className="text-xs text-[#595752] leading-relaxed">{signal.description}</p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setQueryInput(signal.drilldown_prompt);
                    executeSearch(signal.drilldown_prompt);
                  }}
                  className="shrink-0 text-[11px] bg-[#FAF9F5] hover:bg-[#F3F1EC] text-[#191919] border border-[#D5D3CA] px-2.5 py-1 rounded-md flex items-center gap-1 cursor-pointer font-medium transition-colors"
                >
                  Why? <HelpCircle size={12} className="text-[#8C8980]" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* What Changed? Period Delta */}
        {result?.delta && (
          <div className="bg-white border border-[#E5E3DC] rounded-xl px-5 py-3.5 flex flex-wrap items-center justify-between gap-4 text-xs shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-[#191919] uppercase tracking-wider text-[11px]">Period Movement</span>
              <span className="text-[#8C8980] font-mono text-[11px]">
                ({result.delta.start_period} → {result.delta.end_period})
              </span>
            </div>

            <div className="flex items-center gap-6 font-mono text-[11px]">
              <div className="flex items-center gap-1.5">
                <span className="text-[#73716B]">Volume Delta:</span>
                <span className={`font-semibold flex items-center gap-0.5 ${
                  result.delta.volume_change_pct >= 0 ? "text-[#2B6E44]" : "text-[#B92B27]"
                }`}>
                  {result.delta.volume_change_pct >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  {result.delta.volume_change_pct > 0 ? `+${result.delta.volume_change_pct}%` : `${result.delta.volume_change_pct}%`}
                </span>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-[#73716B]">Price/m² Delta:</span>
                <span className={`font-semibold flex items-center gap-0.5 ${
                  result.delta.price_sqm_change_pct >= 0 ? "text-[#2B6E44]" : "text-[#B92B27]"
                }`}>
                  {result.delta.price_sqm_change_pct >= 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                  {result.delta.price_sqm_change_pct > 0 ? `+${result.delta.price_sqm_change_pct}%` : `${result.delta.price_sqm_change_pct}%`}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                const prompt = `Explain the volume and price shift between ${result.delta?.start_period} and ${result.delta?.end_period}`;
                setQueryInput(prompt);
                executeSearch(prompt);
              }}
              className="text-[#9E5D2A] hover:underline cursor-pointer text-[11px] flex items-center gap-1 font-medium"
            >
              Investigate Drift <ArrowRight size={11} />
            </button>
          </div>
        )}

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Text Cards & Auditor */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              {/* Expandable Auditor Ledger */}
              <div className="bg-white border border-[#E5E3DC] rounded-xl overflow-hidden shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                <div 
                  onClick={() => setAuditExpanded(!auditExpanded)}
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-[#FAF9F5] transition-colors"
                >
                  <span
                    className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md ${
                      result.is_grounded
                        ? "bg-[#EBF4EE] text-[#2B6E44] border border-[#D1E6D8]"
                        : "bg-[#FDF2F2] text-[#B92B27] border border-[#F5C2C2]"
                    }`}
                  >
                    {result.is_grounded ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
                    {result.is_grounded ? "AUDITOR VERIFIED (0 DISCREPANCIES)" : "GROUNDING FAILED"}
                  </span>
                  <div className="flex items-center gap-2 text-xs text-[#8C8980] font-mono">
                    <Clock size={12} /> {result.latency_ms}ms
                    {auditExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </div>
                </div>

                {auditExpanded && result.audit_checks && (
                  <div className="border-t border-[#E5E3DC] p-4 bg-[#FAF9F5] flex flex-col gap-2">
                    <p className="text-[10px] font-mono text-[#8C8980] uppercase tracking-wider">
                      Deterministic Checks ({result.audit_checks.filter(c => c.passed).length}/{result.audit_checks.length} Passed)
                    </p>
                    <div className="space-y-1.5">
                      {result.audit_checks.map((check, i) => (
                        <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-[#EBEAE4] last:border-0">
                          <span className="flex items-center gap-1.5 text-[#33312E]">
                            <CheckCircle2 size={12} className="text-[#2B6E44]" />
                            {check.name}
                          </span>
                          <span className="text-[11px] font-mono text-[#8C8980]">{check.detail}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Cadastral Market Summary */}
              <div className="bg-white border border-[#E5E3DC] rounded-xl p-5 flex flex-col gap-3 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between border-b border-[#F0EFEA] pb-2">
                  <div className="flex items-center gap-2 text-[#191919] font-semibold text-xs tracking-wider uppercase">
                    <Sparkles size={14} className="text-[#9E5D2A]" /> Cadastral Summary
                  </div>
                  <span className="text-[10px] font-mono text-[#73716B] bg-[#FAF9F5] px-2 py-0.5 rounded border border-[#E5E3DC]">
                    [DLD Evidence]
                  </span>
                </div>
                <div className="text-sm text-[#33312E] leading-relaxed font-sans space-y-2 [&>p]:mb-2 [&>ul]:list-disc [&>ul]:ml-4 [&>ul>li]:mb-1 [&>strong]:text-[#191919]">
                  <ReactMarkdown>{summary}</ReactMarkdown>
                </div>
              </div>

              {/* Strategic Advisory */}
              {advice && (
                <div className="bg-[#FAF8F5] border border-[#EADECE] rounded-xl p-5 flex flex-col gap-3 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                  <div className="flex items-center justify-between border-b border-[#EADECE]/80 pb-2">
                    <div className="flex items-center gap-2 text-[#9E5D2A] font-semibold text-xs tracking-wider uppercase">
                      <Compass size={14} /> Decision Support
                    </div>
                    <span className="text-[10px] font-mono text-[#9E5D2A] bg-white px-2 py-0.5 rounded border border-[#EADECE]">
                      [AcreIQ Analysis]
                    </span>
                  </div>
                  <div className="text-sm text-[#4A4742] leading-relaxed font-sans space-y-1.5 [&>p]:mb-1.5 [&>ul]:list-disc [&>ul]:ml-4 [&>ul>li]:mb-1 [&>strong]:text-[#191919]">
                    <ReactMarkdown>{advice}</ReactMarkdown>
                  </div>
                </div>
              )}

              {/* Provenance Trace IDs */}
              <div className="bg-white border border-[#E5E3DC] rounded-xl p-4 flex flex-col gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                <p className="text-[11px] font-semibold text-[#8C8980] uppercase tracking-wider flex items-center gap-1.5">
                  <Database size={13} /> Official DLD Registry Trace IDs
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.source_trace_ids.map((id) => (
                    <span
                      key={id}
                      className="font-mono text-[11px] bg-[#FAF9F5] border border-[#DDDCD5] px-2 py-0.5 rounded text-[#595752]"
                    >
                      {id}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Chart (Adaptive Comparison vs Single-Area) */}
            <div className="lg:col-span-7 flex flex-col gap-4">
              <div className="bg-white border border-[#E5E3DC] rounded-xl p-6 flex flex-col gap-4 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
                <div className="flex items-center justify-between border-b border-[#F0EFEA] pb-3">
                  <div>
                    <h3 className="text-sm font-semibold text-[#191919] flex items-center gap-2">
                      {isComparisonMode ? (
                        <>
                          <GitCompare size={15} className="text-[#9E5D2A]" />
                          Comparative Price / m²: {area1Title} vs. {area2Title}
                        </>
                      ) : (
                        <>
                          <TrendingUp size={15} className="text-[#191919]" />
                          Price / m² & Transaction Volume
                        </>
                      )}
                    </h3>
                    <p className="text-[11px] text-[#8C8980]">
                      {isComparisonMode 
                        ? `Monthly average price/m² trajectories across both locations`
                        : "Dual-axis timeseries with Ready vs. Off-Plan trajectories"}
                    </p>
                  </div>
                  <span className="text-xs text-[#8C8980] font-mono">DLD Timeseries</span>
                </div>

                {result.timeseries && result.timeseries.length > 0 ? (
                  <div className="h-80 w-full pt-2">
                    <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={result.timeseries}>
                      <CartesianGrid strokeDasharray="2 2" stroke="#EFEFEA" vertical={false} />
                      <XAxis 
                        dataKey={(d) => d.month_year || d.period} 
                        stroke="#8C8980" 
                        fontSize={11} 
                        tickLine={false} 
                      />
                      {/* Left Y-Axis: Price / m² */}
                      <YAxis 
                        yAxisId="left" 
                        stroke="#191919" 
                        fontSize={11} 
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(val) => `${(val / 1000).toFixed(0)}k`}
                      />
                      {/* Right Y-Axis: Transaction Volume (Always Active) */}
                      <YAxis 
                        yAxisId="right" 
                        orientation="right" 
                        stroke="#8C8980" 
                        fontSize={11} 
                        tickLine={false}
                        axisLine={false}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: "#FFFFFF", 
                          borderColor: "#E5E3DC", 
                          borderRadius: "8px",
                          fontSize: "12px",
                          boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                          color: "#191919"
                        }} 
                      />
                      <Legend 
                        wrapperStyle={{ fontSize: "11px", paddingTop: "14px", color: "#595752" }} 
                        formatter={(value) => <span className="text-[#33312E] font-medium">{value}</span>}
                      />

                      {/* Dynamic Series Branching */}
                      {isComparisonMode ? (
                        <>
                          {/* Area 1 Deal Volume Bar */}
                          <Bar 
                            yAxisId="right" 
                            dataKey="area1_volume" 
                            name={`${area1Title} Deals`} 
                            fill="#E5E3DC" 
                            radius={[2, 2, 0, 0]} 
                          />
                          {/* Area 2 Deal Volume Bar */}
                          <Bar 
                            yAxisId="right" 
                            dataKey="area2_volume" 
                            name={`${area2Title} Deals`} 
                            fill="#D6C4B4" 
                            radius={[2, 2, 0, 0]} 
                          />
                          {/* Area 1 Price/m² Line */}
                          <Line 
                            yAxisId="left" 
                            type="monotone" 
                            dataKey="area1_avg_sqm" 
                            name={`${area1Title} (AED/m²)`} 
                            stroke="#191919" 
                            strokeWidth={2.5} 
                            connectNulls={true}
                            dot={{ fill: "#191919", r: 4 }} 
                          />
                          {/* Area 2 Price/m² Line */}
                          <Line 
                            yAxisId="left" 
                            type="monotone" 
                            dataKey="area2_avg_sqm" 
                            name={`${area2Title} (AED/m²)`} 
                            stroke="#C26A29" 
                            strokeWidth={2.5} 
                            connectNulls={true}
                            dot={{ fill: "#C26A29", r: 4 }} 
                          />
                        </>
                      ) : (
                        <>
                          {/* Single Area Mode: Total Deals */}
                          <Bar 
                            yAxisId="right" 
                            dataKey={(d) => d.volume ?? d.total_volume ?? 0} 
                            name="Volume (Deals)" 
                            fill="#EDECE6" 
                            stroke="#DDDCD5"
                            radius={[3, 3, 0, 0]} 
                          />
                          {/* Ready Units Line */}
                          <Line 
                            yAxisId="left" 
                            type="monotone" 
                            dataKey={(d) => d.ready_avg_sqm ?? d.ready_price_sqm} 
                            name="Ready (AED/m²)" 
                            stroke="#191919" 
                            strokeWidth={2} 
                            connectNulls={true}
                            dot={{ fill: "#191919", r: 3.5 }} 
                          />
                          {/* Off-Plan Line */}
                          <Line 
                            yAxisId="left" 
                            type="monotone" 
                            dataKey={(d) => d.offplan_avg_sqm ?? d.offplan_price_sqm} 
                            name="Off-Plan (AED/m²)" 
                            stroke="#C26A29" 
                            strokeWidth={2} 
                            connectNulls={true}
                            dot={{ fill: "#C26A29", r: 3.5 }} 
                          />
                        </>
                      )}
                    </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-80 border border-dashed border-[#E5E3DC] rounded-lg text-[#8C8980] text-xs">
                    <Building2 size={24} className="mb-2 opacity-40" />
                    No monthly timeseries breakdown available for this query slice.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
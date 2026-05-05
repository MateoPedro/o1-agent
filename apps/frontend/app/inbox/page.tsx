"use client"

import { useState } from "react"
import { RefreshCw } from "lucide-react"
import { useInbox, usePipeline, useEvidence } from "@/lib/queries"
import { OpportunityCard } from "@/components/OpportunityCard"
import { Nav } from "@/components/Nav"

const SLICE_TABS = [
  { label: "Speaking", types: ["talk", "judge", "blog", "article"] },
  { label: "Media", types: ["media"] },
  { label: "Memberships", types: ["member"] },
]

export default function InboxPage() {
  const [limit, setLimit] = useState(20)
  const [slice, setSlice] = useState(0)
  const activeTypes = SLICE_TABS[slice].types
  const { data: opportunities, isLoading, error, refetch, isFetching } = useInbox(limit, activeTypes)
  const { data: pipeline } = usePipeline()
  const { data: evidence } = useEvidence()

  const avgScore =
    opportunities && opportunities.length > 0
      ? opportunities.reduce((s, o) => s + (o.priority_score ?? 0), 0) / opportunities.length
      : null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav
        pipelineCount={pipeline?.filter(o => o.status === "in_progress" || o.status === "submitted").length}
        evidenceCount={evidence?.length}
      />

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Slice tabs */}
        <div className="flex gap-1 mb-6 border-b border-slate-200">
          {SLICE_TABS.map((t, i) => (
            <button
              key={t.label}
              onClick={() => setSlice(i)}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                slice === i
                  ? "text-indigo-600 border-b-2 border-indigo-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
              {slice === i && opportunities && opportunities.length > 0 && (
                <span className="ml-1.5 text-xs px-1.5 py-0.5 rounded-full font-semibold bg-indigo-100 text-indigo-600">
                  {opportunities.length}
                </span>
              )}
            </button>
          ))}

          {/* Stats + controls pushed to the right */}
          <div className="flex items-center gap-4 ml-auto pb-1">
            {opportunities && opportunities.length > 0 && (
              <div className="flex items-center gap-4 text-sm">
                <span className="text-slate-500">
                  <strong className="text-slate-900">{opportunities.length}</strong> opportunities
                </span>
                {avgScore !== null && (
                  <span className="text-slate-500">
                    Avg score: <strong className="text-slate-900">{(avgScore * 100).toFixed(0)}</strong>
                  </span>
                )}
              </div>
            )}

            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 border border-slate-200 hover:bg-slate-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw size={14} className={isFetching ? "animate-spin" : ""} />
              Refresh
            </button>

            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="border border-slate-200 rounded-lg px-3 py-1.5 text-sm bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {[5, 10, 20].map((n) => (
                <option key={n} value={n}>Show {n}</option>
              ))}
            </select>
          </div>
        </div>

        {isLoading && (
          <div className="text-center py-24 text-slate-400">
            <div className="animate-pulse text-lg">Loading opportunities...</div>
          </div>
        )}

        {error && (
          <div className="text-center py-24">
            <p className="text-red-500 font-medium">Could not reach the API.</p>
            <p className="text-slate-400 text-sm mt-1">Make sure the backend is running on port 8000.</p>
          </div>
        )}

        {!isLoading && opportunities?.length === 0 && (
          <div className="text-center py-24">
            <p className="text-slate-500 font-medium">No {SLICE_TABS[slice].label.toLowerCase()} opportunities yet.</p>
            <p className="text-slate-400 text-sm mt-1">
              {slice === 0
                ? "Run the speaking discovery task to populate the inbox."
                : "Run the membership discovery task to populate the inbox."}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {opportunities?.map((opp) => (
            <OpportunityCard key={opp.id} opp={opp} />
          ))}
        </div>
      </main>
    </div>
  )
}

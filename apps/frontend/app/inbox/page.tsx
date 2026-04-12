"use client"

import { useState } from "react"
import { RefreshCw } from "lucide-react"
import { useInbox, usePipeline } from "@/lib/queries"
import { OpportunityCard } from "@/components/OpportunityCard"
import { Nav } from "@/components/Nav"

export default function InboxPage() {
  const [limit, setLimit] = useState(10)
  const { data: opportunities, isLoading, error, refetch, isFetching } = useInbox(limit)
  const { data: pipeline } = usePipeline()

  const avgScore =
    opportunities && opportunities.length > 0
      ? opportunities.reduce((s, o) => s + (o.priority_score ?? 0), 0) / opportunities.length
      : null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav pipelineCount={pipeline?.length} />

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats bar */}
        <div className="flex items-center gap-6 mb-6">
          <div className="flex items-center gap-6 text-sm flex-1">
            {opportunities && (
              <>
                <span className="text-slate-500">
                  <strong className="text-slate-900 text-base">{opportunities.length}</strong>{" "}
                  opportunities
                </span>
                {avgScore !== null && (
                  <span className="text-slate-500">
                    Avg score:{" "}
                    <strong className="text-slate-900">{(avgScore * 100).toFixed(0)}</strong>
                  </span>
                )}
              </>
            )}
          </div>

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
              <option key={n} value={n}>
                Show {n}
              </option>
            ))}
          </select>
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

        {opportunities && opportunities.length === 0 && (
          <div className="text-center py-24">
            <p className="text-slate-500 font-medium">No scored opportunities yet.</p>
            <p className="text-slate-400 text-sm mt-1">Run the discovery task to populate the inbox.</p>
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

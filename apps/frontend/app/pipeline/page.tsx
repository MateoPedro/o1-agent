"use client"

import { useState } from "react"
import { usePipeline } from "@/lib/queries"
import { ActionPlanCard } from "@/components/ActionPlanCard"
import { Nav } from "@/components/Nav"

const TABS = [
  { label: "In Progress", statuses: ["in_progress", "submitted"] },
  { label: "Accepted", statuses: ["accepted"] },
  { label: "Completed", statuses: ["completed", "rejected"] },
]

export default function PipelinePage() {
  const { data: opportunities, isLoading, error } = usePipeline()
  const [tab, setTab] = useState(0)

  const filtered = opportunities?.filter((o) =>
    TABS[tab].statuses.includes(o.status)
  )

  const countFor = (i: number) =>
    opportunities?.filter((o) => TABS[i].statuses.includes(o.status)).length ?? 0

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav pipelineCount={opportunities?.filter(o => o.status === "in_progress" || o.status === "submitted").length} />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900">Pipeline</h2>
          <p className="text-sm text-slate-500 mt-0.5">Opportunities you are actively pursuing.</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 border-b border-slate-200">
          {TABS.map((t, i) => (
            <button
              key={t.label}
              onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm font-medium transition-colors relative ${
                tab === i
                  ? "text-indigo-600 border-b-2 border-indigo-600 -mb-px"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
              {countFor(i) > 0 && (
                <span className={`ml-1.5 text-xs px-1.5 py-0.5 rounded-full font-semibold ${
                  tab === i ? "bg-indigo-100 text-indigo-600" : "bg-slate-100 text-slate-500"
                }`}>
                  {countFor(i)}
                </span>
              )}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="text-center py-24 text-slate-400 animate-pulse">Loading pipeline...</div>
        )}

        {error && (
          <div className="text-center py-24">
            <p className="text-red-500 font-medium">Could not reach the API.</p>
            <p className="text-slate-400 text-sm mt-1">Make sure the backend is running on port 8000.</p>
          </div>
        )}

        {!isLoading && filtered?.length === 0 && (
          <div className="text-center py-24">
            <p className="text-slate-500 font-medium">Nothing here yet.</p>
            {tab === 0 && (
              <p className="text-slate-400 text-sm mt-1">Click "Get Started" on any inbox opportunity to create an action plan.</p>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filtered?.map((opp) => (
            <ActionPlanCard key={opp.id} opp={opp} />
          ))}
        </div>
      </main>
    </div>
  )
}

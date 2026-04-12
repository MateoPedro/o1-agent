"use client"

import { usePipeline } from "@/lib/queries"
import { ActionPlanCard } from "@/components/ActionPlanCard"
import { Nav } from "@/components/Nav"

export default function PipelinePage() {
  const { data: opportunities, isLoading, error } = usePipeline()

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav pipelineCount={opportunities?.length} />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-slate-900">Pipeline</h2>
          <p className="text-sm text-slate-500 mt-0.5">Opportunities you are actively pursuing.</p>
        </div>

        {isLoading && (
          <div className="text-center py-24 text-slate-400">
            <div className="animate-pulse text-lg">Loading pipeline...</div>
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
            <p className="text-slate-500 font-medium">Nothing in the pipeline yet.</p>
            <p className="text-slate-400 text-sm mt-1">Click "Get Started" on any inbox opportunity to create an action plan.</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {opportunities?.map((opp) => (
            <ActionPlanCard key={opp.id} opp={opp} />
          ))}
        </div>
      </main>
    </div>
  )
}

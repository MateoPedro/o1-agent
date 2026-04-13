"use client"

import { ExternalLink, Download } from "lucide-react"
import { useEvidence, usePipeline } from "@/lib/queries"
import { Nav } from "@/components/Nav"
import type { Evidence } from "@/lib/api"

const STRENGTH_STYLES: Record<string, string> = {
  strong: "bg-emerald-50 text-emerald-700 border-emerald-200",
  moderate: "bg-amber-50 text-amber-700 border-amber-200",
  weak: "bg-slate-50 text-slate-500 border-slate-200",
}

const STRENGTH_DOT: Record<string, string> = {
  strong: "bg-emerald-500",
  moderate: "bg-amber-400",
  weak: "bg-slate-300",
}

function EvidenceCard({ entry }: { entry: Evidence }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-900 text-base leading-snug">{entry.host_name}</h3>
          <p className="text-xs text-slate-400 mt-0.5">{entry.host_description}</p>
        </div>
        <a href={entry.public_url} target="_blank" rel="noopener noreferrer" className="text-slate-400 hover:text-slate-600 flex-shrink-0">
          <ExternalLink size={14} />
        </a>
      </div>

      <div className="flex gap-2 flex-wrap items-center">
        <span className="text-xs bg-slate-50 text-slate-600 border border-slate-200 px-2 py-0.5 rounded-full capitalize">{entry.activity_type}</span>
        {entry.source === "profile" && (
          <span className="text-xs bg-violet-50 text-violet-600 border border-violet-100 px-2 py-0.5 rounded-full font-medium">Pre-existing work</span>
        )}
        <span className="text-xs text-slate-500">🗓 {entry.date}</span>
      </div>

      <div className="flex flex-col gap-1.5">
        {entry.uscis_criteria.map((c, i) => (
          <div key={i} className={`rounded-xl border px-3 py-2 ${STRENGTH_STYLES[c.strength] ?? STRENGTH_STYLES.weak}`}>
            <div className="flex items-center gap-2 mb-1">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${STRENGTH_DOT[c.strength] ?? STRENGTH_DOT.weak}`} />
              <span className="text-xs font-semibold">{c.criterion}</span>
              <span className="text-xs opacity-60 ml-auto uppercase tracking-wide">{c.strength}</span>
            </div>
            <p className="text-xs opacity-80 leading-relaxed">{c.rationale}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function EvidencePage() {
  const { data: evidence, isLoading, error } = useEvidence()
  const { data: pipeline } = usePipeline()

  const pipelineCount = pipeline?.filter(o => o.status === "in_progress" || o.status === "submitted").length

  // Group by criterion
  const byCriterion: Record<string, Evidence[]> = {}
  for (const entry of evidence ?? []) {
    for (const c of entry.uscis_criteria) {
      const key = c.criterion
      if (!byCriterion[key]) byCriterion[key] = []
      if (!byCriterion[key].find(e => e.id === entry.id)) {
        byCriterion[key].push(entry)
      }
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav pipelineCount={pipelineCount} evidenceCount={evidence?.length} />

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Evidence</h2>
            <p className="text-sm text-slate-500 mt-0.5">Completed activities mapped to O-1A USCIS criteria.</p>
          </div>
          {evidence && evidence.length > 0 && (
            <a
              href="/api/backend/evidence/export"
              download="o1a-evidence.md"
              className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 border border-slate-200 hover:bg-slate-50 px-3 py-1.5 rounded-lg transition-colors"
            >
              <Download size={14} />
              Export Markdown
            </a>
          )}
        </div>

        {isLoading && (
          <div className="text-center py-24 text-slate-400 animate-pulse">Loading evidence...</div>
        )}

        {error && (
          <div className="text-center py-24">
            <p className="text-red-500 font-medium">Could not reach the API.</p>
          </div>
        )}

        {!isLoading && evidence?.length === 0 && (
          <div className="text-center py-24">
            <p className="text-slate-500 font-medium">No evidence logged yet.</p>
            <p className="text-slate-400 text-sm mt-1">Mark an opportunity as accepted in the Pipeline, then click "Log Evidence".</p>
          </div>
        )}

        {Object.keys(byCriterion).length > 0 && (
          <div className="flex flex-col gap-10">
            {Object.entries(byCriterion).map(([criterion, entries]) => (
              <div key={criterion}>
                <div className="flex items-center gap-3 mb-4">
                  <h3 className="text-sm font-semibold text-slate-700">{criterion}</h3>
                  <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">
                    {entries.length} {entries.length === 1 ? "entry" : "entries"}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
                  {entries.map((e) => <EvidenceCard key={e.id} entry={e} />)}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}

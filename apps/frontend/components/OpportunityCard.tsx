"use client"

import { ExternalLink, CheckCircle } from "lucide-react"
import { useApproveOpportunity } from "@/lib/queries"
import type { Opportunity } from "@/lib/api"

const TYPE_STYLES: Record<string, string> = {
  talk: "bg-indigo-50 text-indigo-700 border-indigo-100",
  judge: "bg-purple-50 text-purple-700 border-purple-100",
  member: "bg-blue-50 text-blue-700 border-blue-100",
  blog: "bg-orange-50 text-orange-700 border-orange-100",
  article: "bg-pink-50 text-pink-700 border-pink-100",
}

const EFFORT_STYLES: Record<string, string> = {
  low: "bg-green-50 text-green-700 border-green-100",
  medium: "bg-amber-50 text-amber-700 border-amber-100",
  high: "bg-red-50 text-red-700 border-red-100",
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100)
  const color = score >= 0.7 ? "bg-emerald-500" : score >= 0.5 ? "bg-amber-500" : "bg-red-400"
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className={`text-xs font-semibold tabular-nums ${score >= 0.7 ? "text-emerald-600" : score >= 0.5 ? "text-amber-600" : "text-red-500"}`}>
        {pct}
      </span>
    </div>
  )
}

function Badge({ label, style }: { label: string; style: string }) {
  return (
    <span className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border ${style}`}>
      {label}
    </span>
  )
}

export function OpportunityCard({ opp }: { opp: Opportunity }) {
  const approve = useApproveOpportunity()
  const isApproved = opp.status === "drafted"

  return (
    <div className={`bg-white rounded-2xl border shadow-sm hover:shadow-md transition-all duration-200 flex flex-col overflow-hidden ${isApproved ? "border-emerald-200 bg-emerald-50/30" : "border-slate-200"}`}>
      {/* Card header */}
      <div className="px-5 pt-5 pb-4 border-b border-slate-100">
        <div className="flex items-start justify-between gap-3 mb-3">
          <Badge
            label={opp.type.toUpperCase()}
            style={TYPE_STYLES[opp.type] ?? "bg-slate-50 text-slate-600 border-slate-200"}
          />
          {isApproved && (
            <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
              <CheckCircle size={12} /> Approved
            </span>
          )}
        </div>
        <h3 className="font-semibold text-slate-900 text-base leading-snug">{opp.host}</h3>
        {opp.host_domain && (
          <p className="text-xs text-slate-400 mt-0.5">{opp.host_domain}</p>
        )}
      </div>

      {/* Body */}
      <div className="px-5 py-4 flex flex-col gap-3 flex-1">
        {/* Score */}
        {opp.priority_score !== null && (
          <div>
            <p className="text-xs text-slate-400 mb-1 font-medium uppercase tracking-wide">Priority Score</p>
            <ScoreBar score={opp.priority_score} />
          </div>
        )}

        {/* Meta pills */}
        <div className="flex flex-wrap gap-1.5">
          {opp.location && (
            <span className="text-xs text-slate-500 flex items-center gap-1">
              📍 {opp.location}
            </span>
          )}
          {opp.deadline && (
            <span className="text-xs text-slate-500 flex items-center gap-1 ml-2">
              📅 {opp.deadline}
            </span>
          )}
          {opp.effort && (
            <Badge
              label={`${opp.effort} effort`}
              style={EFFORT_STYLES[opp.effort] ?? "bg-slate-50 text-slate-600 border-slate-200"}
            />
          )}
        </div>

        {/* USCIS criteria */}
        {opp.uscis_criteria && opp.uscis_criteria.length > 0 && (
          <div>
            <p className="text-xs text-slate-400 mb-1.5 font-medium uppercase tracking-wide">USCIS Criteria</p>
            <div className="flex flex-wrap gap-1.5">
              {opp.uscis_criteria.map((c) => (
                <span key={c} className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded-full">
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Topic tags */}
        {opp.topic_tags && opp.topic_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {opp.topic_tags.map((t) => (
              <span key={t} className="text-xs bg-slate-50 text-slate-500 border border-slate-200 px-2 py-0.5 rounded-full">
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Rationale */}
        {opp.score_rationale && (
          <p className="text-xs text-slate-500 bg-slate-50 rounded-xl p-3 leading-relaxed border border-slate-100">
            {opp.score_rationale}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="px-5 pb-5 pt-3 border-t border-slate-100 flex gap-2">
        <a
          href={opp.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 flex items-center justify-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 border border-slate-200 hover:bg-slate-50 rounded-xl px-3 py-2 transition-colors"
        >
          <ExternalLink size={13} /> View
        </a>
        {!isApproved && (
          <button
            onClick={() => approve.mutate(opp.id)}
            disabled={approve.isPending}
            className="flex-1 flex items-center justify-center gap-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white rounded-xl px-3 py-2 font-medium transition-colors disabled:opacity-50"
          >
            <CheckCircle size={13} />
            {approve.isPending ? "Approving…" : "Approve"}
          </button>
        )}
      </div>
    </div>
  )
}

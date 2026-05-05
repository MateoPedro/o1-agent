"use client"

import { useState } from "react"
import { ExternalLink, CheckSquare, Square, ChevronDown, ChevronUp, Copy, Check, Mail, Send, Trophy, CheckCircle } from "lucide-react"
import { useToggleTodo, useSendEmail, useAcceptOpportunity, useLogEvidence } from "@/lib/queries"
import type { Opportunity, TodoItem, EmailDraft, ContentOutline, MembershipStatement, Pitch } from "@/lib/api"

const STATUS_STYLES: Record<string, string> = {
  in_progress: "bg-indigo-50 text-indigo-700 border-indigo-100",
  submitted: "bg-blue-50 text-blue-700 border-blue-100",
  accepted: "bg-emerald-50 text-emerald-700 border-emerald-100",
  rejected: "bg-red-50 text-red-500 border-red-100",
  completed: "bg-slate-100 text-slate-600 border-slate-200",
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 transition-colors"
    >
      {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
      {copied ? "Copied" : "Copy"}
    </button>
  )
}

function TodoList({ todos, draftId }: { todos: TodoItem[]; draftId: number }) {
  const toggle = useToggleTodo()
  const done = todos.filter(t => t.completed).length

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Next Steps</p>
        <span className="text-xs text-slate-400">{done}/{todos.length} done</span>
      </div>
      <div className="flex flex-col gap-1.5">
        {todos.map((todo) => (
          <div
            key={todo.id}
            className={`rounded-xl border p-3 transition-colors ${todo.completed ? "bg-slate-50 border-slate-100" : "bg-white border-slate-200"}`}
          >
            <div className="flex items-start gap-2.5">
              <button
                onClick={() => toggle.mutate({ draftId, todoId: todo.id })}
                disabled={toggle.isPending}
                className="mt-0.5 flex-shrink-0 text-slate-400 hover:text-indigo-600 transition-colors"
              >
                {todo.completed
                  ? <CheckSquare size={15} className="text-emerald-500" />
                  : <Square size={15} />
                }
              </button>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium leading-snug ${todo.completed ? "line-through text-slate-400" : "text-slate-800"}`}>
                  {todo.task}
                </p>
                {!todo.completed && (
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{todo.detail}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function EmailDraftSection({ drafts, draftId }: { drafts: EmailDraft[]; draftId: number }) {
  const [open, setOpen] = useState<string | null>(null)
  const sendMutation = useSendEmail()

  if (drafts.length === 0) return null

  return (
    <div>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Email Drafts</p>
      <div className="flex flex-col gap-1.5">
        {drafts.map((draft) => (
          <div key={draft.id} className={`rounded-xl border overflow-hidden ${draft.sent ? "border-emerald-100 bg-emerald-50/40" : "border-slate-200"}`}>
            <button
              className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
              onClick={() => setOpen(open === draft.id ? null : draft.id)}
            >
              <Mail size={13} className={draft.sent ? "text-emerald-500" : "text-slate-400"} />
              <span className="text-sm font-medium text-slate-700 flex-1 truncate">{draft.subject}</span>
              {draft.sent
                ? <span className="text-xs text-emerald-600 font-medium flex-shrink-0">Sent</span>
                : open === draft.id ? <ChevronUp size={13} className="text-slate-400" /> : <ChevronDown size={13} className="text-slate-400" />
              }
            </button>
            {open === draft.id && (
              <div className="px-3 pb-3 border-t border-slate-100">
                {draft.to && (
                  <p className="text-xs text-slate-400 mt-2">To: {draft.to}</p>
                )}
                <pre className="text-xs text-slate-600 whitespace-pre-wrap leading-relaxed font-sans mt-2 bg-slate-50 rounded-lg p-3">
                  {draft.body}
                </pre>
                <div className="flex items-center justify-between mt-2">
                  <CopyButton text={draft.body} />
                  {!draft.sent && (
                    <button
                      onClick={() => sendMutation.mutate({ draftId, emailId: draft.id })}
                      disabled={sendMutation.isPending}
                      className="flex items-center gap-1.5 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
                    >
                      <Send size={11} />
                      {sendMutation.isPending ? "Sending…" : "Send"}
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function ContentOutlineSection({ outline }: { outline: ContentOutline }) {
  const [open, setOpen] = useState(false)

  if (!outline) return null

  return (
    <div>
      <button
        className="w-full flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2"
        onClick={() => setOpen(!open)}
      >
        Content Outline
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      {open && (
        <div className="flex flex-col gap-3 bg-slate-50 rounded-xl p-3 border border-slate-100">
          <div>
            <p className="text-xs font-medium text-slate-500 mb-1">Suggested angle</p>
            <p className="text-xs text-slate-700 leading-relaxed">{outline.suggested_angle}</p>
          </div>

          {outline.title_ideas?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Title ideas</p>
              <ul className="flex flex-col gap-1">
                {outline.title_ideas.map((t, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-slate-300 text-xs mt-0.5">—</span>
                    <span className="text-xs text-slate-700">{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {outline.key_points?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Key points to cover</p>
              <ul className="flex flex-col gap-1">
                {outline.key_points.map((p, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-slate-300 text-xs mt-0.5">·</span>
                    <span className="text-xs text-slate-700">{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {outline.story_modules?.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1">Story modules</p>
              <div className="flex flex-wrap gap-1">
                {outline.story_modules.map((m) => (
                  <span key={m} className="text-xs bg-indigo-50 text-indigo-600 border border-indigo-100 px-2 py-0.5 rounded-full">
                    {m.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function PitchSection({ pitch }: { pitch: Pitch }) {
  const [open, setOpen] = useState<string | null>(null)
  const toggle = (s: string) => setOpen(open === s ? null : s)

  return (
    <div>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Pitch Strategy</p>
      <div className="flex flex-col gap-1.5">

        {/* Suggested angle */}
        <div className="bg-rose-50 border border-rose-100 rounded-xl px-3 py-2.5">
          <p className="text-xs font-medium text-rose-700 mb-1">Suggested angle</p>
          <p className="text-xs text-rose-800 leading-relaxed">{pitch.suggested_angle}</p>
        </div>

        {/* Talking points */}
        {pitch.talking_points?.length > 0 && (
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
              onClick={() => toggle("points")}
            >
              <span className="text-sm font-medium text-slate-700">Talking Points</span>
              {open === "points" ? <ChevronUp size={13} className="text-slate-400" /> : <ChevronDown size={13} className="text-slate-400" />}
            </button>
            {open === "points" && (
              <div className="px-3 pb-3 border-t border-slate-100">
                <ul className="flex flex-col gap-1.5 mt-2">
                  {pitch.talking_points.map((p, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-slate-300 text-xs mt-0.5 flex-shrink-0">·</span>
                      <span className="text-xs text-slate-700 leading-relaxed">{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Follow-up note */}
        {pitch.follow_up_note && (
          <p className="text-xs text-slate-500 bg-slate-50 border border-slate-100 rounded-xl px-3 py-2 leading-relaxed italic">
            Follow-up: {pitch.follow_up_note}
          </p>
        )}

      </div>
    </div>
  )
}

function MembershipStatementSection({ statement }: { statement: MembershipStatement }) {
  const [openSection, setOpenSection] = useState<string | null>(null)
  const toggle = (s: string) => setOpenSection(openSection === s ? null : s)

  return (
    <div>
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Membership Application</p>
      <div className="flex flex-col gap-1.5">

        {/* Personal statement */}
        <div className="rounded-xl border border-slate-200 overflow-hidden">
          <button
            className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
            onClick={() => toggle("statement")}
          >
            <span className="text-sm font-medium text-slate-700">Personal Statement Draft</span>
            {openSection === "statement" ? <ChevronUp size={13} className="text-slate-400" /> : <ChevronDown size={13} className="text-slate-400" />}
          </button>
          {openSection === "statement" && (
            <div className="px-3 pb-3 border-t border-slate-100">
              <pre className="text-xs text-slate-600 whitespace-pre-wrap leading-relaxed font-sans mt-2 bg-slate-50 rounded-lg p-3">
                {statement.personal_statement_draft}
              </pre>
              <div className="mt-2">
                <CopyButton text={statement.personal_statement_draft} />
              </div>
            </div>
          )}
        </div>

        {/* Talking points */}
        {statement.talking_points?.length > 0 && (
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
              onClick={() => toggle("points")}
            >
              <span className="text-sm font-medium text-slate-700">Talking Points</span>
              {openSection === "points" ? <ChevronUp size={13} className="text-slate-400" /> : <ChevronDown size={13} className="text-slate-400" />}
            </button>
            {openSection === "points" && (
              <div className="px-3 pb-3 border-t border-slate-100">
                <ul className="flex flex-col gap-1.5 mt-2">
                  {statement.talking_points.map((p, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-slate-300 text-xs mt-0.5 flex-shrink-0">·</span>
                      <span className="text-xs text-slate-700 leading-relaxed">{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Nominator suggestions */}
        {statement.nominator_suggestions?.length > 0 && (
          <div className="rounded-xl border border-slate-200 overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
              onClick={() => toggle("nominators")}
            >
              <span className="text-sm font-medium text-slate-700">Nominator Suggestions</span>
              <div className="flex items-center gap-2">
                <span className="text-xs bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded-full">
                  {statement.nominator_suggestions.length}
                </span>
                {openSection === "nominators" ? <ChevronUp size={13} className="text-slate-400" /> : <ChevronDown size={13} className="text-slate-400" />}
              </div>
            </button>
            {openSection === "nominators" && (
              <div className="px-3 pb-3 border-t border-slate-100 flex flex-col gap-2 mt-2">
                {statement.nominator_suggestions.map((n, i) => (
                  <div key={i} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                    <p className="text-xs font-semibold text-slate-700">{n.role}</p>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{n.why}</p>
                    <p className="text-xs text-indigo-600 mt-1 italic">{n.outreach_note}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Application window note */}
        {statement.application_window_note && (
          <p className="text-xs text-slate-500 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2 leading-relaxed">
            🗓 {statement.application_window_note}
          </p>
        )}

      </div>
    </div>
  )
}

const REPLY_STYLES = {
  accepted: { banner: "bg-emerald-50 border-emerald-200", text: "text-emerald-700", label: "Accepted" },
  rejected: { banner: "bg-red-50 border-red-200", text: "text-red-600", label: "Rejected" },
  more_info_needed: { banner: "bg-amber-50 border-amber-200", text: "text-amber-700", label: "Reply received" },
}

export function ActionPlanCard({ opp }: { opp: Opportunity }) {
  const plan = opp.draft?.action_plan
  const draftId = opp.draft?.id
  const reply = opp.draft?.reply_classification
  const replyStyle = reply ? REPLY_STYLES[reply] : null
  const accept = useAcceptOpportunity()
  const logEvidence = useLogEvidence()
  const isActive = opp.status === "in_progress" || opp.status === "submitted"
  const isAccepted = opp.status === "accepted"
  const isCompleted = opp.status === "completed"

  return (
    <div className={`bg-white rounded-2xl border shadow-sm flex flex-col overflow-hidden ${replyStyle ? replyStyle.banner : "border-slate-200"}`}>
      {/* Header */}
      <div className="px-5 pt-5 pb-4 border-b border-slate-100">
        <div className="flex items-start justify-between gap-3 mb-2">
          <span className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border ${STATUS_STYLES[opp.status] ?? "bg-slate-50 text-slate-600 border-slate-200"}`}>
            {opp.status.replace("_", " ")}
          </span>
          <a
            href={opp.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <ExternalLink size={14} />
          </a>
        </div>
        <h3 className="font-semibold text-slate-900 text-base leading-snug">{opp.host}</h3>
        {opp.host_domain && <p className="text-xs text-slate-400 mt-0.5">{opp.host_domain}</p>}

        {/* Reply banner */}
        {replyStyle && (
          <div className={`mt-3 rounded-xl px-3 py-2 border ${replyStyle.banner}`}>
            <p className={`text-xs font-semibold ${replyStyle.text}`}>{replyStyle.label}</p>
            {opp.draft?.reply_summary && (
              <p className={`text-xs mt-0.5 ${replyStyle.text} opacity-80`}>{opp.draft.reply_summary}</p>
            )}
          </div>
        )}

        <div className="flex flex-wrap gap-2 mt-3">
          {opp.event_date && (
            <span className="text-xs text-slate-500">🗓 Event {opp.event_date}</span>
          )}
          {opp.deadline_status === "specific" && opp.deadline && (
            <span className="text-xs text-slate-500">📅 Apply by {opp.deadline}</span>
          )}
          {opp.deadline_status === "rolling" && (
            <span className="inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full border bg-blue-50 text-blue-600 border-blue-100">Rolling deadline</span>
          )}
        </div>
      </div>

      {/* Plan body */}
      {plan && (
        <div className="px-5 py-4 flex flex-col gap-4 flex-1">
          {plan.todos?.length > 0 && draftId && (
            <TodoList todos={plan.todos} draftId={draftId} />
          )}
          {draftId && <EmailDraftSection drafts={plan.email_drafts ?? []} draftId={draftId} />}
          {plan.pitch && (
            <PitchSection pitch={plan.pitch} />
          )}
          {plan.membership_statement && (
            <MembershipStatementSection statement={plan.membership_statement} />
          )}
          {plan.content_outline && (
            <ContentOutlineSection outline={plan.content_outline} />
          )}
        </div>
      )}

      {!plan && (
        <div className="px-5 py-8 text-center text-slate-400 text-sm">
          No action plan yet.
        </div>
      )}

      {/* Footer actions */}
      {(isActive || isAccepted) && (
        <div className="px-5 pb-5 pt-3 border-t border-slate-100 flex gap-2">
          {isActive && (
            <button
              onClick={() => accept.mutate(opp.id)}
              disabled={accept.isPending}
              className="flex-1 flex items-center justify-center gap-1.5 text-sm bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl px-3 py-2 font-medium transition-colors disabled:opacity-50"
            >
              <CheckCircle size={13} />
              {accept.isPending ? "Marking…" : "Mark Accepted"}
            </button>
          )}
          {isAccepted && (
            <button
              onClick={() => logEvidence.mutate(opp.id)}
              disabled={logEvidence.isPending}
              className="flex-1 flex items-center justify-center gap-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl px-3 py-2 font-medium transition-colors disabled:opacity-50"
            >
              <Trophy size={13} />
              {logEvidence.isPending ? "Logging…" : "Log Evidence"}
            </button>
          )}
        </div>
      )}

      {isCompleted && (
        <div className="px-5 pb-4 pt-3 border-t border-slate-100">
          <p className="text-xs text-emerald-600 font-medium flex items-center gap-1.5">
            <Trophy size={12} /> Evidence logged
          </p>
        </div>
      )}
    </div>
  )
}

const API_BASE = "/api/backend"

export interface UsciscriterionEntry {
  criterion: string
  strength: "strong" | "moderate" | "weak"
  rationale: string
}

export interface TodoItem {
  id: string
  task: string
  detail: string
  completed: boolean
}

export interface EmailDraft {
  id: string
  to: string
  subject: string
  body: string
  sent: boolean
}

export interface ContentOutline {
  suggested_angle: string
  story_modules: string[]
  title_ideas: string[]
  key_points: string[]
}

export interface NominatorSuggestion {
  role: string
  why: string
  outreach_note: string
}

export interface MembershipStatement {
  personal_statement_draft: string
  nominator_suggestions: NominatorSuggestion[]
  talking_points: string[]
  application_window_note: string
}

export interface Pitch {
  suggested_angle: string
  talking_points: string[]
  follow_up_note: string
}

export interface JudgingApplication {
  why_qualified: string
  domain_expertise: string[]
  evaluation_approach: string
  availability_note: string
}

export interface ArticleOutlineSection {
  section: string
  description: string
}

export interface ArticleOutline {
  suggested_angle: string
  title_options: string[]
  outline: ArticleOutlineSection[]
  key_data_points: string[]
  target_word_count?: string | null
}

export interface ActionPlan {
  todos: TodoItem[]
  email_drafts: EmailDraft[]
  content_outline?: ContentOutline
  membership_statement?: MembershipStatement
  pitch?: Pitch
  judging_application?: JudgingApplication
  article_outline?: ArticleOutline
}

export interface Draft {
  id: number
  opportunity_id: number
  action_plan: ActionPlan | null
  message_id: string | null
  thread_id: string | null
  reply_classification: "accepted" | "rejected" | "more_info_needed" | null
  reply_summary: string | null
  created_at: string
  approved_at: string | null
}

export interface Opportunity {
  id: number
  type: string
  host: string
  host_domain: string
  topic_tags: string[]
  deadline: string | null
  deadline_status: "specific" | "rolling" | "unknown"
  event_date: string | null
  effort: string
  effort_rationale: string | null
  location: string | null
  source_url: string
  priority_score: number | null
  score_rationale: string | null
  uscis_criteria: UsciscriterionEntry[] | null
  status: string
  created_at: string
  draft?: Draft | null
}

export async function fetchInbox(limit = 20, types?: string[]): Promise<Opportunity[]> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (types && types.length > 0) params.set("type", types.join(","))
  const res = await fetch(`${API_BASE}/inbox?${params}`)
  if (!res.ok) throw new Error("Failed to fetch inbox")
  return res.json()
}

export async function createPlan(id: number): Promise<Opportunity> {
  const res = await fetch(`${API_BASE}/opportunities/${id}/plan`, {
    method: "POST",
  })
  if (!res.ok) throw new Error("Failed to create plan")
  return res.json()
}

export async function toggleTodo(draftId: number, todoId: string): Promise<Draft> {
  const res = await fetch(`${API_BASE}/drafts/${draftId}/todos/${todoId}/toggle`, {
    method: "PATCH",
  })
  if (!res.ok) throw new Error("Failed to toggle todo")
  return res.json()
}

export interface Evidence {
  id: number
  opportunity_id: number
  activity_type: string
  host_name: string
  host_description: string
  date: string
  public_url: string
  uscis_criteria: Array<{ criterion: string; strength: string; rationale: string }>
  supporting_details: Record<string, unknown>
  source: "profile" | "opportunity"
  created_at: string
}

export async function acceptOpportunity(id: number): Promise<Opportunity> {
  const res = await fetch(`${API_BASE}/opportunities/${id}/accept`, { method: "POST" })
  if (!res.ok) throw new Error("Failed to accept opportunity")
  return res.json()
}

export async function logEvidence(id: number): Promise<Evidence> {
  const res = await fetch(`${API_BASE}/opportunities/${id}/log-evidence`, { method: "POST" })
  if (!res.ok) throw new Error("Failed to log evidence")
  return res.json()
}

export async function fetchEvidence(): Promise<Evidence[]> {
  const res = await fetch(`${API_BASE}/evidence`)
  if (!res.ok) throw new Error("Failed to fetch evidence")
  return res.json()
}

export async function sendEmail(draftId: number, emailId: string): Promise<Draft> {
  const res = await fetch(`${API_BASE}/drafts/${draftId}/emails/${emailId}/send`, {
    method: "POST",
  })
  if (!res.ok) throw new Error("Failed to send email")
  return res.json()
}

export async function fetchPipeline(): Promise<Opportunity[]> {
  const res = await fetch(`${API_BASE}/pipeline`)
  if (!res.ok) throw new Error("Failed to fetch pipeline")
  return res.json()
}

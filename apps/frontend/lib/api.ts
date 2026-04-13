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

export interface ActionPlan {
  todos: TodoItem[]
  email_drafts: EmailDraft[]
  content_outline: ContentOutline
}

export interface Draft {
  id: number
  opportunity_id: number
  action_plan: ActionPlan | null
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

export async function fetchInbox(limit = 10): Promise<Opportunity[]> {
  const res = await fetch(`${API_BASE}/inbox?limit=${limit}`)
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

const API_BASE = "/api/backend"

export interface UsciscriterionEntry {
  criterion: string
  strength: "strong" | "moderate" | "weak"
  rationale: string
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
  location: string | null
  source_url: string
  priority_score: number | null
  score_rationale: string | null
  uscis_criteria: UsciscriterionEntry[] | null
  status: string
  created_at: string
}

export async function fetchInbox(limit = 10): Promise<Opportunity[]> {
  const res = await fetch(`${API_BASE}/inbox?limit=${limit}`)
  if (!res.ok) throw new Error("Failed to fetch inbox")
  return res.json()
}

export async function approveOpportunity(id: number): Promise<Opportunity> {
  const res = await fetch(`${API_BASE}/opportunities/${id}/approve`, {
    method: "POST",
  })
  if (!res.ok) throw new Error("Failed to approve opportunity")
  return res.json()
}

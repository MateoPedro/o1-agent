# Frontend

Streamlit-based opportunity inbox UI for o1-agent. Shows ranked opportunities, draft previews, and approval controls.

Planned to migrate to Next.js once the core loop is stable.

## Getting Started

```bash
pip install -r requirements.txt
streamlit run app.py
```

## What it shows

- **Inbox** — top-ranked opportunities for the week (type, host, deadline, effort, priority score, USCIS criteria, rationale)
- **Draft view** — generated title options, abstract, bio with inline editing
- **Approval controls** — approve / reject / request revision; no submission possible without explicit approval
- **Outcome status** — submitted / accepted / rejected / pending per opportunity

import streamlit as st
import httpx
from datetime import date

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="o1-agent inbox", layout="wide")
st.title("O-1A Opportunity Inbox")

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    limit = st.slider("Max opportunities to show", 1, 20, 10)
    if st.button("Refresh"):
        st.rerun()

# Fetch from API
try:
    response = httpx.get(f"{API_URL}/inbox", params={"limit": limit}, timeout=10)
    response.raise_for_status()
    opportunities = response.json()
except Exception as e:
    st.error(f"Could not reach API: {e}")
    st.stop()

if not opportunities:
    st.info("No scored opportunities in inbox yet. Run the discovery task to populate.")
    st.stop()

st.caption(f"Showing {len(opportunities)} opportunities ranked by priority score")

for opp in opportunities:
    score = opp.get("priority_score") or 0
    deadline = opp.get("deadline")
    location = opp.get("location") or "Unknown"
    criteria = opp.get("uscis_criteria") or []
    tags = opp.get("topic_tags") or []

    # Colour the score badge
    if score >= 0.7:
        score_color = "🟢"
    elif score >= 0.5:
        score_color = "🟡"
    else:
        score_color = "🔴"

    with st.expander(f"{score_color} **{opp['host']}** — {opp['type'].upper()} — Score: {score:.2f}"):
        col1, col2, col3 = st.columns(3)
        col1.metric("Location", location)
        col2.metric("Effort", opp.get("effort", "—").capitalize())
        col3.metric("Deadline", deadline or "Not listed")

        if tags:
            st.write("**Topics:** " + " · ".join(f"`{t}`" for t in tags))

        if criteria:
            st.write("**USCIS criteria:**")
            for c in criteria:
                st.write(f"  • {c}")

        if opp.get("score_rationale"):
            st.info(opp["score_rationale"])

        col_a, col_b, col_c = st.columns([1, 1, 4])
        col_a.link_button("View opportunity", opp.get("source_url", "#"))
        if col_b.button("Approve for drafting", key=f"approve_{opp['id']}"):
            try:
                httpx.post(f"{API_URL}/opportunities/{opp['id']}/approve", timeout=5)
                st.success("Approved — will appear in drafting queue.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to approve: {e}")

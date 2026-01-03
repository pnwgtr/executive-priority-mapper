import streamlit as st
import pandas as pd

st.set_page_config(page_title="Executive Priority Mapper", layout="centered")

ROLES = [
    "Process & Governance Manager",
    "Director of Infrastructure",
    "Enterprise Architect",
    "Director of Information Security",
]

SCORES_2 = {"A": 2, "B": 0}
SCORES_3 = {"A": 2, "B": 1, "C": 0}

QUESTIONS = [
    (1,  "When technology issues occur, which is more acceptable?",
     {"A": "Small, recurring issues", "B": "Rare but high-impact failures"},
     SCORES_2,
     {"Director of Infrastructure": 2, "Process & Governance Manager": 1}),
    (2,  "How much surprise is acceptable at the executive level?",
     {"A": "None, early warning and visibility are expected",
      "B": "Limited, if impact is low",
      "C": "Some, if cost avoidance is achieved"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Infrastructure": 1, "Director of Information Security": 1}),
    (3,  "Which best reflects leadership’s risk posture?",
     {"A": "Proactively manage and reduce risk",
      "B": "Accept known risk to reduce cost",
      "C": "Address risk when it becomes material"},
     SCORES_3,
     {"Process & Governance Manager": 1, "Director of Information Security": 2}),
    (4,  "When cost and stability conflict, which should generally win?",
     {"A": "Stability and reliability",
      "B": "Lowest reasonable cost",
      "C": "Case-by-case"},
     SCORES_3,
     {"Director of Infrastructure": 2}),
    (5,  "Which is more important?",
     {"A": "Predictable, planned spend",
      "B": "Flexibility to adjust spend year to year"},
     SCORES_2,
     {"Process & Governance Manager": 2, "Enterprise Architect": 1}),
    (6,  "How should emergency fixes and reactive spend be viewed?",
     {"A": "Avoid whenever possible",
      "B": "Acceptable if infrequent",
      "C": "An expected cost of doing business"},
     SCORES_3,
     {"Director of Infrastructure": 2, "Process & Governance Manager": 1}),
    (7,  "For decisions that affect multiple departments, ownership should:",
     {"A": "Be clearly assigned to one role",
      "B": "Be shared across teams",
      "C": "Be decided case-by-case"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Enterprise Architect": 1, "Director of Information Security": 1}),
    (8,  "When something fails, leadership prefers:",
     {"A": "A clearly accountable owner",
      "B": "Shared responsibility",
      "C": "Focus on resolution, not ownership"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Infrastructure": 1}),
    (9,  "How should technology exceptions be handled?",
     {"A": "Tracked, reviewed, and revisited",
      "B": "Approved when needed",
      "C": "Left to operational judgment"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Information Security": 1}),
    (10, "Is the organization primarily optimizing for:",
     {"A": "Today’s operational needs",
      "B": "A defined 3–5 year future state",
      "C": "Both equally"},
     SCORES_3,
     {"Enterprise Architect": 2, "Director of Infrastructure": 1}),
    (11, "When adopting new systems, what matters most?",
     {"A": "Fit with long-term direction",
      "B": "Speed of implementation",
      "C": "Lowest cost"},
     SCORES_3,
     {"Enterprise Architect": 2}),
    (12, "How important is clean integration across the enterprise?",
     {"A": "Very important",
      "B": "Somewhat important",
      "C": "Not a priority"},
     SCORES_3,
     {"Enterprise Architect": 2, "Director of Information Security": 1}),
    (13, "How should regulators and auditors view our environment?",
     {"A": "Well-controlled and mature",
      "B": "Compliant but lean",
      "C": "Minimum required standard"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Information Security": 1}),
    (14, "Which concern weighs heavier?",
     {"A": "Reputational impact",
      "B": "Financial impact",
      "C": "Both equally"},
     SCORES_3,
     {"Director of Information Security": 2, "Director of Infrastructure": 1}),
    (15, "After an incident, how should the organization be perceived?",
     {"A": "Prepared and well-governed",
      "B": "Unlucky but responsive",
      "C": "Cost-conscious and pragmatic"},
     SCORES_3,
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),
    (16, "Which operating style best reflects leadership preference?",
     {"A": "Consistent and repeatable",
      "B": "Flexible and adaptive"},
     SCORES_2,
     {"Process & Governance Manager": 2, "Director of Infrastructure": 1}),
    (17, "How acceptable is reliance on key individuals?",
     {"A": "Not acceptable",
      "B": "Acceptable with backups",
      "C": "Acceptable if it works"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Infrastructure": 1}),
    (18, "Which matters more?",
     {"A": "Institutional knowledge and process",
      "B": "Individual expertise and autonomy"},
     SCORES_2,
     {"Process & Governance Manager": 2, "Enterprise Architect": 1}),
    (19, "Who should own enterprise-level cyber risk, beyond individual systems?",
     {"A": "Individual system owners",
      "B": "IT leadership collectively",
      "C": "A single accountable executive"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 3}),
    (20, "When cyber risk spans infrastructure, applications, vendors, and users, who should coordinate decisions?",
     {"A": "Each team independently",
      "B": "Ad hoc leadership discussion",
      "C": "A centralized risk owner"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 3, "Enterprise Architect": 1}),
    (21, "When leadership accepts cyber risk, how should that decision be made?",
     {"A": "Informally as issues arise",
      "B": "Documented and reviewed",
      "C": "Escalated based on impact"},
     {"A": 0, "B": 2, "C": 2},
     {"Director of Information Security": 2, "Process & Governance Manager": 2}),
    (22, "How should executives be informed of cyber risk?",
     {"A": "Only after incidents",
      "B": "Periodic summaries",
      "C": "Ongoing, risk-based reporting"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),
    (23, "What matters most in cyber risk reporting?",
     {"A": "Technical detail",
      "B": "Business impact",
      "C": "Regulatory exposure"},
     {"A": 0, "B": 2, "C": 2},
     {"Director of Information Security": 2}),
    (24, "Who should translate technical cyber risk into business terms?",
     {"A": "Engineering teams",
      "B": "IT leadership",
      "C": "A dedicated risk leader"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),
    (25, "Should cyber risk tolerance vary by department?",
     {"A": "Yes, based on business need",
      "B": "No, it should be consistent",
      "C": "Only with executive approval"},
     {"A": 0, "B": 2, "C": 2},
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),
    (26, "How should security exceptions be handled?",
     {"A": "Approved locally",
      "B": "Approved with oversight",
      "C": "Approved, tracked, and reviewed centrally"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2, "Process & Governance Manager": 2}),
    (27, "Who ensures security standards are applied consistently across the enterprise?",
     {"A": "Individual managers",
      "B": "IT leadership collectively",
      "C": "A centralized authority"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),
    (28, "After a cyber incident, who owns enterprise-level lessons learned?",
     {"A": "The impacted team",
      "B": "IT leadership",
      "C": "A designated risk owner"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),
    (29, "Who ensures corrective actions actually reduce future risk?",
     {"A": "Individual teams",
      "B": "Project management",
      "C": "A centralized risk authority"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),
    (30, "Who briefs executives on residual risk after remediation?",
     {"A": "Engineering teams",
      "B": "IT leadership",
      "C": "A cyber risk executive"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),
]

def role_max_points():
    max_points = {r: 0 for r in ROLES}
    for _, _, _, score_map, weights in QUESTIONS:
        max_choice = max(score_map.values())
        for role, w in weights.items():
            max_points[role] += max_choice * w
    return max_points

MAX_POINTS = role_max_points()

def compute_role_scores(responses: dict) -> dict:
    totals = {r: 0 for r in ROLES}
    for qid, _, _, score_map, weights in QUESTIONS:
        choice = responses.get(qid)
        if not choice:
            continue
        base = score_map[choice]
        for role, w in weights.items():
            totals[role] += base * w
    return totals

def classify(pct: float) -> str:
    if pct >= 0.70:
        return "Strongly implied"
    if pct >= 0.45:
        return "Moderately implied"
    return "Weakly implied"

if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "respondent" not in st.session_state:
    st.session_state.respondent = ""

st.title("Executive Priority Mapper")

st.session_state.respondent = st.text_input("Respondent (Name / Title)", value=st.session_state.respondent)

total = len(QUESTIONS)
step = st.session_state.step

st.progress(min(step / total, 1.0))
st.caption(f"{min(step, total)}/{total} answered")

if step >= total:
    scores = compute_role_scores(st.session_state.responses)
    rows = []
    for role in ROLES:
        maxp = MAX_POINTS[role]
        pct = (scores[role] / maxp) if maxp else 0
        rows.append({"Role": role, "Percent": round(pct * 100, 1), "Implication": classify(pct)})

    df = pd.DataFrame(rows).sort_values("Percent", ascending=False)

    st.subheader("Results")
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("Role")["Percent"])

    st.subheader("Export")
    export_df = df.copy()
    export_df.insert(0, "Respondent", st.session_state.respondent or "Anonymous")
    csv = export_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv, file_name="executive_priority_mapper_results.csv", mime="text/csv")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Restart"):
            st.session_state.step = 0
            st.session_state.responses = {}
            st.rerun()
    with c2:
        if st.button("Back to last question"):
            st.session_state.step = total - 1
            st.rerun()

else:
    qid, qtext, options, _, _ = QUESTIONS[step]

    st.markdown("---")
    st.subheader(f"Question {qid}")
    st.write(qtext)

    prev = st.session_state.responses.get(qid)
    keys = list(options.keys())
    default_index = keys.index(prev) if prev in keys else 0

    choice = st.radio(
        "Select one:",
        options=keys,
        index=default_index,
        format_func=lambda k: options[k],
        key=f"q_{qid}",
    )

    st.session_state.responses[qid] = choice

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Back", disabled=(step == 0)):
            st.session_state.step = max(step - 1, 0)
            st.rerun()
    with c2:
        label = "Finish" if step == total - 1 else "Next"
        if st.button(label):
            st.session_state.step = min(step + 1, total)
            st.rerun()

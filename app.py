import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Executive Priority Mapper", layout="wide")

DATA_DIR = "data"
RESPONSES_JSONL = os.path.join(DATA_DIR, "responses.jsonl")  # full answers per respondent
ROLE_SCORES_CSV = os.path.join(DATA_DIR, "role_scores.csv")  # computed scores per respondent

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


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

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
        choice = responses.get(str(qid)) or responses.get(qid)
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

def load_jsonl(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def append_jsonl(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")

def upsert_role_scores(row: dict):
    # Keep role_scores.csv as an append-only log too (simple). Aggregate reads all rows.
    df_row = pd.DataFrame([row])
    if os.path.exists(ROLE_SCORES_CSV):
        df_existing = pd.read_csv(ROLE_SCORES_CSV)
        df_all = pd.concat([df_existing, df_row], ignore_index=True)
        df_all.to_csv(ROLE_SCORES_CSV, index=False)
    else:
        df_row.to_csv(ROLE_SCORES_CSV, index=False)

def calc_alignment(respondent_answers: list[dict]) -> pd.DataFrame:
    """
    respondent_answers: list of {qid(str): "A"/"B"/"C"} dicts
    Returns dataframe with per-question: distribution, agreement %, entropy-like split
    """
    # Build table respondents x questions
    qids = [str(q[0]) for q in QUESTIONS]
    rows = []
    for ans in respondent_answers:
        rows.append({qid: ans.get(qid) for qid in qids})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()

    out_rows = []
    for qid in qids:
        counts = df[qid].value_counts(dropna=True).to_dict()
        total = int(sum(counts.values())) if counts else 0
        top = max(counts.values()) if counts else 0
        agreement = (top / total) if total else 0

        # Simple "disagreement score" = 1 - agreement
        disagreement = 1 - agreement

        out_rows.append({
            "Question": int(qid),
            "Agreement %": round(agreement * 100, 1),
            "Disagreement %": round(disagreement * 100, 1),
            "A": int(counts.get("A", 0)),
            "B": int(counts.get("B", 0)),
            "C": int(counts.get("C", 0)),
        })

    out = pd.DataFrame(out_rows).sort_values("Disagreement %", ascending=False)
    return out


# ---------- Session state ----------
if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}  # qid(str)->choice
if "respondent" not in st.session_state:
    st.session_state.respondent = ""

ensure_data_dir()

tab_survey, tab_agg = st.tabs(["Survey", "Aggregate View"])

# ---------- Survey Tab ----------
with tab_survey:
    st.title("Executive Priority Mapper")

    st.session_state.respondent = st.text_input(
        "Respondent (Name / Title)",
        value=st.session_state.respondent,
        placeholder="e.g., Interim CEO, CFO, CIO"
    )

    total = len(QUESTIONS)
    step = st.session_state.step

    st.progress(min(step / total, 1.0))
    st.caption(f"Question {min(step + 1, total)} of {total}")

    if step >= total:
        st.subheader("Results (This respondent)")

        scores = compute_role_scores(st.session_state.responses)
        rows = []
        for role in ROLES:
            maxp = MAX_POINTS[role]
            pct = (scores[role] / maxp) if maxp else 0
            rows.append({
                "Role": role,
                "Percent": round(pct * 100, 1),
                "Implication": classify(pct),
            })
        df = pd.DataFrame(rows).sort_values("Percent", ascending=False)

        c1, c2 = st.columns([1, 1])
        with c1:
            st.dataframe(df, use_container_width=True)
        with c2:
            st.bar_chart(df.set_index("Role")["Percent"])

        st.divider()
        st.subheader("Save respondent (for aggregate view)")

        save_name = st.session_state.respondent.strip()
        can_save = bool(save_name)

        if not can_save:
            st.warning("Enter a respondent name/title above before saving.")

        if st.button("Save respondent", disabled=not can_save):
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "respondent": save_name,
                "answers": st.session_state.responses,
            }
            append_jsonl(RESPONSES_JSONL, payload)

            score_row = {"timestamp": payload["timestamp"], "respondent": save_name}
            for r in ROLES:
                score_row[r] = float(df.loc[df["Role"] == r, "Percent"].values[0])
                score_row[f"{r} Implication"] = df.loc[df["Role"] == r, "Implication"].values[0]
            upsert_role_scores(score_row)

            st.success("Saved. Go to the Aggregate View tab.")

        st.subheader("Export (this respondent)")
        export_df = df.copy()
        export_df.insert(0, "Respondent", st.session_state.respondent or "Anonymous")
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download respondent results as CSV",
            data=csv,
            file_name="executive_priority_mapper_results.csv",
            mime="text/csv",
        )

        c3, c4 = st.columns(2)
        with c3:
            if st.button("Restart survey"):
                st.session_state.step = 0
                st.session_state.responses = {}
                st.rerun()
        with c4:
            if st.button("Back to last question"):
                st.session_state.step = total - 1
                st.rerun()

    else:
        qid, qtext, options, _, _ = QUESTIONS[step]
        qid_str = str(qid)

        st.subheader(f"Question {qid}")
        st.write(qtext)

        prev = st.session_state.responses.get(qid_str)
        keys = list(options.keys())
        default_index = keys.index(prev) if prev in keys else 0

        choice = st.radio(
            "Select one:",
            options=keys,
            index=default_index,
            format_func=lambda k: options[k],
            key=f"q_{qid}",
        )

        st.session_state.responses[qid_str] = choice

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Back", disabled=(step == 0)):
                st.session_state.step = max(step - 1, 0)
                st.rerun()
        with b2:
            label = "Finish" if step == total - 1 else "Next"
            if st.button(label):
                st.session_state.step = min(step + 1, total)
                st.rerun()


# ---------- Aggregate View Tab ----------
with tab_agg:
    st.title("Aggregate View (Executive Team)")

    all_payloads = load_jsonl(RESPONSES_JSONL)
    if not all_payloads:
        st.info("No saved respondents yet. Complete the survey and click 'Save respondent' on the results page.")
        st.stop()

    # Extract respondent list + answers
    respondents = [p["respondent"] for p in all_payloads]
    answers_list = [p["answers"] for p in all_payloads]

    st.caption(f"Saved respondents: {', '.join(respondents)}")

    # Compute role percents for each respondent on the fly (source of truth = answers)
    role_rows = []
    for p in all_payloads:
        scores = compute_role_scores(p["answers"])
        row = {"Respondent": p["respondent"]}
        for role in ROLES:
            maxp = MAX_POINTS[role]
            pct = (scores[role] / maxp) if maxp else 0
            row[role] = round(pct * 100, 1)
        role_rows.append(row)

    role_df = pd.DataFrame(role_rows).set_index("Respondent")

    st.subheader("Role implication across leadership")
    st.dataframe(role_df, use_container_width=True)

    avg_series = role_df.mean(axis=0).sort_values(ascending=False)
    st.subheader("Average implication (executive team)")
    st.bar_chart(avg_series)

    st.divider()

    st.subheader("Alignment vs disagreement (by question)")
    align_df = calc_alignment(answers_list)
    if align_df.empty:
        st.info("Not enough data to compute alignment.")
        st.stop()

    # Add question text for readability
    q_text_map = {int(q[0]): q[1] for q in QUESTIONS}
    align_df["Question text"] = align_df["Question"].map(q_text_map)

    # Show most divisive questions at top
    st.caption("Most divisive questions appear first. These indicate areas that require governance and clarity.")
    st.dataframe(
        align_df[["Question", "Question text", "Agreement %", "Disagreement %", "A", "B", "C"]],
        use_container_width=True
    )

    st.divider()

    st.subheader("Most divisive questions (talk track)")
    top_n = min(5, len(align_df))
    top = align_df.head(top_n)

    for _, r in top.iterrows():
        st.markdown(f"**Q{int(r['Question'])}: {r['Question text']}**")
        st.write(f"Agreement: {r['Agreement %']}% | Disagreement: {r['Disagreement %']}%")
        st.write(f"Response counts: A={int(r['A'])}, B={int(r['B'])}, C={int(r['C'])}")
        st.write("Why it matters: disagreement here means leadership priorities are not yet translated into a consistent operating model.")
        st.markdown("---")

    st.subheader("Admin")
    if st.button("Clear all saved data (local)"):
        # Dangerous but sometimes needed for testing
        try:
            if os.path.exists(RESPONSES_JSONL):
                os.remove(RESPONSES_JSONL)
            if os.path.exists(ROLE_SCORES_CSV):
                os.remove(ROLE_SCORES_CSV)
            st.success("Cleared. Refresh the page.")
        except Exception as e:
            st.error(f"Failed to clear: {e}")

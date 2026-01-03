import json
import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

st.set_page_config(page_title="Executive Priority Mapper", layout="wide")

DATA_DIR = "data"
RESPONSES_JSONL = os.path.join(DATA_DIR, "responses.jsonl")

ROLES = [
    "Process & Governance Manager",
    "Director of Infrastructure",
    "Enterprise Architect",
    "Director of Information Security",
]

SCORES_2 = {"A": 2, "B": 0}
SCORES_3 = {"A": 2, "B": 1, "C": 0}

# Questions: (qid, text, options, score_map, role_weights)
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

def append_jsonl(path: str, obj: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")

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

def role_max_points():
    max_points = {r: 0 for r in ROLES}
    for _, _, _, score_map, weights in QUESTIONS:
        max_choice = max(score_map.values())
        for role, w in weights.items():
            max_points[role] += max_choice * w
    return max_points

MAX_POINTS = role_max_points()

def compute_role_scores(answers: dict) -> dict:
    totals = {r: 0 for r in ROLES}
    for qid, _, _, score_map, weights in QUESTIONS:
        choice = answers.get(str(qid))
        if not choice:
            continue
        base = score_map[choice]
        for role, w in weights.items():
            totals[role] += base * w
    return totals

def role_percentages(answers: dict) -> dict:
    scores = compute_role_scores(answers)
    out = {}
    for role in ROLES:
        maxp = MAX_POINTS[role]
        pct = (scores[role] / maxp) if maxp else 0
        out[role] = round(pct * 100, 1)
    return out

def classify(pct: float) -> str:
    if pct >= 70:
        return "Strongly implied"
    if pct >= 45:
        return "Moderately implied"
    return "Weakly implied"

def traffic_light(pct: float) -> str:
    if pct >= 70:
        return "Green"
    if pct >= 45:
        return "Yellow"
    return "Red"

def calc_alignment(answer_dicts: list[dict]) -> pd.DataFrame:
    qids = [str(q[0]) for q in QUESTIONS]
    df = pd.DataFrame([{qid: a.get(qid) for qid in qids} for a in answer_dicts])
    if df.empty:
        return pd.DataFrame()

    rows = []
    for qid in qids:
        counts = df[qid].value_counts(dropna=True).to_dict()
        total = int(sum(counts.values())) if counts else 0
        top = max(counts.values()) if counts else 0
        agreement = (top / total) if total else 0
        rows.append({
            "Question": int(qid),
            "Agreement %": round(agreement * 100, 1),
            "Disagreement %": round((1 - agreement) * 100, 1),
            "A": int(counts.get("A", 0)),
            "B": int(counts.get("B", 0)),
            "C": int(counts.get("C", 0)),
        })
    return pd.DataFrame(rows).sort_values("Disagreement %", ascending=False)

def executive_summary(role_avg: pd.Series, align_df: pd.DataFrame) -> str:
    top_roles = role_avg.sort_values(ascending=False).head(2).index.tolist()
    bottom_roles = role_avg.sort_values(ascending=True).head(1).index.tolist()
    most_divisive = align_df.sort_values("Disagreement %", ascending=False).head(2)["Question"].tolist()

    parts = []
    parts.append(
        f"Team averages indicate strongest implied ownership in: {top_roles[0]} and {top_roles[1]}."
        if len(top_roles) >= 2 else
        f"Team averages indicate strongest implied ownership in: {top_roles[0]}."
    )
    parts.append(f"Lowest implied ownership is: {bottom_roles[0]}." if bottom_roles else "")
    if most_divisive:
        parts.append(f"Leadership is most split on questions: {most_divisive[0]}" + (f" and {most_divisive[1]}." if len(most_divisive) > 1 else "."))
    parts.append("This disagreement is a governance signal: priorities are not yet translated into consistent ownership and decision-making.")
    return " ".join([p for p in parts if p]).strip()

def make_network_graph(role_df: pd.DataFrame):
    """
    role_df index: Respondent
    columns: ROLES with percent values
    Draw exec-role graph with spring layout.
    """
    G = nx.Graph()

    exec_nodes = list(role_df.index)
    role_nodes = list(role_df.columns)

    for e in exec_nodes:
        G.add_node(e, kind="exec")
    for r in role_nodes:
        G.add_node(r, kind="role")

    # Edges weighted by percent / 100
    for e in exec_nodes:
        for r in role_nodes:
            w = float(role_df.loc[e, r]) / 100.0
            if w <= 0:
                continue
            G.add_edge(e, r, weight=w)

    # Spring layout (web-like). Fixed seed for stable layout.
    pos = nx.spring_layout(G, seed=42, k=0.9)

    fig = plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.axis("off")

    # Edge widths by weight
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    widths = [1 + 8 * w for w in weights]

    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.35, ax=ax)

    # Nodes
    exec_list = [n for n, d in G.nodes(data=True) if d.get("kind") == "exec"]
    role_list = [n for n, d in G.nodes(data=True) if d.get("kind") == "role"]

    nx.draw_networkx_nodes(G, pos, nodelist=exec_list, node_size=900, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=role_list, node_size=1300, ax=ax)

    # Labels
    nx.draw_networkx_labels(G, pos, font_size=9, ax=ax)

    return fig

def stable_question_order(respondent: str, randomize: bool) -> list[int]:
    """
    Returns a list of indices into QUESTIONS in the order to present.
    Deterministic per respondent so it does not feel random in a bad way.
    """
    idxs = list(range(len(QUESTIONS)))
    if not randomize:
        return idxs

    seed_source = (respondent or "anonymous").strip().lower()
    # Simple stable seed from text
    seed = sum(ord(c) for c in seed_source) % 10_000
    rng = random.Random(seed)
    rng.shuffle(idxs)
    return idxs


# Session state
if "step" not in st.session_state:
    st.session_state.step = 0
if "responses" not in st.session_state:
    st.session_state.responses = {}  # qid(str) -> choice
if "respondent" not in st.session_state:
    st.session_state.respondent = ""
if "randomize" not in st.session_state:
    st.session_state.randomize = True
if "order" not in st.session_state:
    st.session_state.order = None

ensure_data_dir()

tab_survey, tab_agg = st.tabs(["Survey", "Aggregate View"])

with tab_survey:
    st.title("Executive Priority Mapper")

    st.session_state.respondent = st.text_input(
        "Respondent (Name / Title)",
        value=st.session_state.respondent,
        placeholder="e.g., Interim CEO, CFO, CIO"
    )

    st.session_state.randomize = st.checkbox(
        "Randomize question order",
        value=st.session_state.randomize
    )

    # Set or refresh order when respondent changes or when order not set
    if st.session_state.order is None:
        st.session_state.order = stable_question_order(st.session_state.respondent, st.session_state.randomize)

    # If respondent changes, refresh order and restart only if no answers yet
    # (Keeps it simple: if you already started answering, finish before changing respondent name.)
    total = len(QUESTIONS)
    step = st.session_state.step

    st.progress(min(step / total, 1.0))
    st.caption(f"Question {min(step + 1, total)} of {total}")

    if step >= total:
        st.subheader("Results (This respondent)")
        perc = role_percentages(st.session_state.responses)

        df = pd.DataFrame([{
            "Role": role,
            "Percent": perc[role],
            "Implication": classify(perc[role]),
        } for role in ROLES]).sort_values("Percent", ascending=False)

        c1, c2 = st.columns([1, 1])
        with c1:
            st.dataframe(df, use_container_width=True)
        with c2:
            st.bar_chart(df.set_index("Role")["Percent"])

        st.divider()
        st.subheader("Save respondent (for aggregate view)")

        save_name = st.session_state.respondent.strip()
        if not save_name:
            st.warning("Enter a respondent name/title above before saving.")

        if st.button("Save respondent", disabled=not bool(save_name)):
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "respondent": save_name,
                "answers": st.session_state.responses,
            }
            append_jsonl(RESPONSES_JSONL, payload)
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
                st.session_state.order = stable_question_order(st.session_state.respondent, st.session_state.randomize)
                st.rerun()
        with c4:
            if st.button("Back to last question"):
                st.session_state.step = total - 1
                st.rerun()

    else:
        order = st.session_state.order or list(range(total))
        q_index = order[step]
        qid, qtext, options, _, _ = QUESTIONS[q_index]
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


with tab_agg:
    st.title("Aggregate View (Executive Team)")

    all_payloads = load_jsonl(RESPONSES_JSONL)
    if not all_payloads:
        st.info("No saved respondents yet. Complete the survey and click 'Save respondent' on the results page.")
        st.stop()

    respondents = [p["respondent"] for p in all_payloads]
    answers_list = [p["answers"] for p in all_payloads]

    st.caption("Point-in-time assessment. Responses reflect executive perspectives at the time collected.")
    st.caption(f"Last updated (UTC): {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")

    # Role implication per respondent
    role_rows = []
    for p in all_payloads:
        perc = role_percentages(p["answers"])
        row = {"Respondent": p["respondent"]}
        row.update(perc)
        role_rows.append(row)

    role_df = pd.DataFrame(role_rows).set_index("Respondent")
    role_avg = role_df.mean(axis=0).sort_values(ascending=False)

    align_df = calc_alignment(answers_list)
    q_text_map = {int(q[0]): q[1] for q in QUESTIONS}
    if not align_df.empty:
        align_df["Question text"] = align_df["Question"].map(q_text_map)

    # Executive alignment summary (text-first)
    st.subheader("Executive alignment summary")
    if not align_df.empty:
        st.write(executive_summary(role_avg, align_df))
    else:
        st.write("Not enough responses to compute alignment and disagreement yet.")

    st.divider()

    # Traffic light indicators (team average only)
    st.subheader("Role implication at a glance (team average)")
    light_rows = []
    for role in ROLES:
        pct = float(role_avg.get(role, 0))
        light_rows.append({
            "Role": role,
            "Team average %": round(pct, 1),
            "Indicator": traffic_light(pct),
            "Implication": classify(pct),
        })
    lights_df = pd.DataFrame(light_rows).sort_values("Team average %", ascending=False)
    st.dataframe(lights_df, use_container_width=True)

    st.bar_chart(role_avg)

    st.divider()

    # Network graph (exec heads at a glance)
    st.subheader("Executive map (network view)")
    st.caption("Exec nodes connect to role nodes. Thicker lines indicate stronger implied need for ownership in that domain.")
    fig = make_network_graph(role_df[ROLES])
    st.pyplot(fig, clear_figure=True)

    st.divider()

    # Top 3 governance pressure points
    st.subheader("Top governance pressure points")
    if not align_df.empty:
        top3 = align_df.sort_values("Disagreement %", ascending=False).head(3)
        for _, r in top3.iterrows():
            st.markdown(f"**Q{int(r['Question'])}: {r['Question text']}**")
            st.write(f"Agreement: {r['Agreement %']}% | Disagreement: {r['Disagreement %']}%")
            st.write(f"Response counts: A={int(r['A'])}, B={int(r['B'])}, C={int(r['C'])}")
            st.markdown("---")
    else:
        st.write("Not enough responses to calculate disagreement.")

    st.subheader("Alignment vs disagreement (by question)")
    if not align_df.empty:
        st.dataframe(
            align_df[["Question", "Question text", "Agreement %", "Disagreement %", "A", "B", "C"]],
            use_container_width=True
        )
    else:
        st.write("Not enough responses to calculate alignment.")

    st.divider()
    st.subheader("Admin")
    if st.button("Clear all saved data (local)"):
        try:
            if os.path.exists(RESPONSES_JSONL):
                os.remove(RESPONSES_JSONL)
            st.success("Cleared. Refresh the page.")
        except Exception as e:
            st.error(f"Failed to clear: {e}")

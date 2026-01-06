
import json
import os
from datetime import datetime
import textwrap

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx

st.set_page_config(page_title="Executive Alignment Mapper", layout="wide")

DATA_DIR = "data"
RESPONSES_JSONL = os.path.join(DATA_DIR, "responses.jsonl")

ROLES = [
    "Process & Governance Manager",
    "Director of Infrastructure",
    "Director of Operations",
    "Enterprise Architect",
    "Director of Information Security",
]

SCORES_2 = {"A": 2, "B": 0}
SCORES_3 = {"A": 2, "B": 1, "C": 0}

# Questions: (qid, text, options, score_map, role_weights)
QUESTIONS = [
    (1, "When user-facing technology issues occur, which is more acceptable?",
     {"A": "Small, recurring issues", "B": "Rare but high-impact failures"},
     SCORES_2,
     {"Director of Operations": 2, "Director of Infrastructure": 1}),

    (2, "How much unexpected operational or cyber risk impact is acceptable at the executive level?",
     {"A": "None, early warning and visibility are expected",
      "B": "Limited, if impact is low",
      "C": "Some, if cost avoidance is achieved"},
     SCORES_3,
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),

    (3, "Which best reflects leadership’s cyber risk posture?",
     {"A": "Proactively manage and reduce risk",
      "B": "Accept known risk to reduce cost",
      "C": "Address risk when it becomes material"},
     SCORES_3,
     {"Director of Information Security": 3}),

    (4, "When user-facing stability and cost conflict, which should generally win?",
     {"A": "Stability and reliability",
      "B": "Lowest reasonable cost",
      "C": "Case-by-case"},
     SCORES_3,
     {"Director of Operations": 2}),

    (5, "Which is more important for technology and cyber investments?",
     {"A": "Predictable, planned spend",
      "B": "Flexibility to adjust spend year to year"},
     SCORES_2,
     {"Process & Governance Manager": 2, "Enterprise Architect": 1}),

    (6, "How should emergency fixes required to restore service or reduce cyber risk be viewed?",
     {"A": "Avoid whenever possible",
      "B": "Acceptable if infrequent",
      "C": "An expected cost of doing business"},
     SCORES_3,
     {"Director of Operations": 1, "Director of Information Security": 1}),

    (7, "For cross-department technology or cyber risk decisions, ownership should:",
     {"A": "Be clearly assigned to one role",
      "B": "Be shared across teams",
      "C": "Be decided case-by-case"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Information Security": 1}),

    (8, "When user-facing services or critical systems fail, leadership prefers:",
     {"A": "A clearly accountable owner",
      "B": "Shared responsibility",
      "C": "Focus on resolution, not ownership"},
     SCORES_3,
     {"Director of Operations": 2}),

    (9, "How should cyber and technology control exceptions be handled?",
     {"A": "Tracked, reviewed, and revisited",
      "B": "Approved when needed",
      "C": "Left to operational judgment"},
     SCORES_3,
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),

    (10, "Is the organization primarily optimizing its technology environment for:",
     {"A": "Today’s operational needs",
      "B": "A defined 3–5 year future state",
      "C": "Both equally"},
     SCORES_3,
     {"Enterprise Architect": 2}),

    (11, "When adopting new systems, what matters most from an enterprise perspective?",
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
     {"Enterprise Architect": 2}),

    (13, "How should regulators and auditors view our cybersecurity and control environment?",
     {"A": "Well-controlled and mature",
      "B": "Compliant but lean",
      "C": "Minimum required standard"},
     SCORES_3,
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),

    (14, "Which concern weighs heavier when cyber incidents occur?",
     {"A": "Reputational impact",
      "B": "Financial impact",
      "C": "Both equally"},
     SCORES_3,
     {"Director of Information Security": 2}),

    (15, "After a cyber or operational incident, how should the organization be perceived?",
     {"A": "Prepared and well-governed",
      "B": "Unlucky but responsive",
      "C": "Cost-conscious and pragmatic"},
     SCORES_3,
     {"Director of Information Security": 2}),

    (16, "Which technology operating style best reflects leadership preference?",
     {"A": "Consistent and repeatable",
      "B": "Flexible and adaptive"},
     SCORES_2,
     {"Process & Governance Manager": 2}),

    (17, "How acceptable is reliance on key technical or operational individuals?",
     {"A": "Not acceptable",
      "B": "Acceptable with backups",
      "C": "Acceptable if it works"},
     SCORES_3,
     {"Process & Governance Manager": 2}),

    (18, "Which matters more for long-term operational resilience?",
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
     {"Director of Information Security": 2, "Process & Governance Manager": 1}),

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
      "C": "A dedicated cyber risk leader"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (25, "Should cyber risk tolerance vary by department?",
     {"A": "Yes, based on business need",
      "B": "No, it should be consistent",
      "C": "Only with executive approval"},
     {"A": 0, "B": 2, "C": 2},
     {"Director of Information Security": 2}),

    (26, "How should security exceptions be handled?",
     {"A": "Approved locally",
      "B": "Approved with oversight",
      "C": "Approved, tracked, and reviewed centrally"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (27, "Who ensures security standards are applied consistently across the enterprise?",
     {"A": "Individual managers",
      "B": "IT leadership collectively",
      "C": "A centralized authority"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (28, "After a cyber incident, who owns enterprise-level lessons learned?",
     {"A": "The impacted team",
      "B": "IT leadership",
      "C": "A designated cyber risk owner"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (29, "Who ensures corrective actions actually reduce future risk?",
     {"A": "Individual teams",
      "B": "Project management",
      "C": "A centralized cyber risk authority"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (30, "Who briefs executives on residual risk after remediation?",
     {"A": "Engineering teams",
      "B": "IT leadership",
      "C": "A cyber risk executive"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (31, "When cybersecurity leadership advises against a business decision due to risk, executives should:",
     {"A": "Defer unless the business impact is extreme",
      "B": "Weigh the advice alongside cost and operational impact",
      "C": "Treat the guidance as authoritative unless explicitly overridden"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 3}),

    (32, "How should disagreements between cybersecurity leadership and business leaders be resolved?",
     {"A": "Business leaders decide based on urgency",
      "B": "Through collaborative discussion and documented risk acceptance",
      "C": "By deferring to cybersecurity leadership on risk matters"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 3}),

    (33, "When multiple technology tools provide overlapping capabilities, leadership prefers to:",
     {"A": "Consolidate, even if transition is difficult",
      "B": "Keep multiple tools if they meet local needs",
      "C": "Decide case-by-case based on cost"},
     SCORES_3,
     {"Enterprise Architect": 2, "Director of Operations": 2, "Director of Information Security": 1}),

    (34, "When cybersecurity tooling creates operational friction for end users, leadership expects:",
     {"A": "Adjustments to improve usability where risk allows",
      "B": "Strict adherence regardless of user impact",
      "C": "Local workarounds managed by support teams"},
     SCORES_3,
     {"Director of Operations": 3, "Director of Information Security": 1}),

    (35, "Who is accountable for ensuring infrastructure resilience aligns with business uptime expectations?",
     {"A": "Infrastructure leadership",
      "B": "Shared across IT leadership",
      "C": "Executive leadership"},
     SCORES_3,
     {"Director of Infrastructure": 3}),

    (36, "When standard change processes slow urgent business needs, leadership prefers:",
     {"A": "Controlled flexibility with documented risk",
      "B": "Strict adherence to process",
      "C": "Informal bypass to keep work moving"},
     SCORES_3,
     {"Process & Governance Manager": 2, "Director of Information Security": 1}),

    (37, "When vendors introduce material cyber risk, who should determine acceptability?",
     {"A": "The business owner using the vendor",
      "B": "IT leadership collectively",
      "C": "Cybersecurity leadership"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 3}),

    (38, "How should accumulated technical debt be treated?",
     {"A": "Actively reduced as part of normal operations",
      "B": "Tolerated if systems remain functional",
      "C": "Addressed only during major transformations"},
     SCORES_3,
     {"Enterprise Architect": 3, "Director of Infrastructure": 1}),

    (39, "When Operations, Infrastructure, and Security priorities conflict, who should arbitrate?",
     {"A": "The impacted operational leader",
      "B": "The CIO or executive leadership",
      "C": "Cybersecurity leadership based on risk"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 2}),

    (40, "How much autonomy should directors have to accept risk within their domains?",
     {"A": "Minimal, risk decisions should be centralized",
      "B": "Moderate, within defined guardrails",
      "C": "High, autonomy enables speed"},
     {"A": 0, "B": 1, "C": 2},
     {"Director of Information Security": 1, "Process & Governance Manager": 1}),
]


# -----------------------------
# Storage helpers
# -----------------------------
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


# -----------------------------
# Scoring helpers
# -----------------------------
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
        out[role] = int(round(pct * 100, 0))
    return out


def classify(pct: float) -> str:
    if pct >= 70:
        return "Strongly implied"
    if pct >= 45:
        return "Moderately implied"
    return "Weakly implied"


def calc_alignment(answer_dicts: list[dict]) -> pd.DataFrame:
    qids = [str(q[0]) for q in QUESTIONS]
    df = pd.DataFrame([{qid: a.get(qid) for qid in qids} for a in answer_dicts])
    if df.empty:
        return pd.DataFrame(columns=["Question", "Agreement %", "Disagreement %", "A", "B", "C"])

    rows = []
    for qid in qids:
        counts = df[qid].value_counts(dropna=True).to_dict()
        total = int(sum(counts.values())) if counts else 0
        top = max(counts.values()) if counts else 0
        agreement = (top / total) if total else 0
        rows.append({
            "Question": int(qid),
            "Agreement %": round(agreement * 100, 0),
            "Disagreement %": round((1 - agreement) * 100, 0),
            "A": int(counts.get("A", 0)),
            "B": int(counts.get("B", 0)),
            "C": int(counts.get("C", 0)),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["Question", "Agreement %", "Disagreement %", "A", "B", "C"])
    return out.sort_values("Disagreement %", ascending=False)


def executive_summary(role_avg: pd.Series, align_df: pd.DataFrame) -> str:
    top_roles = role_avg.sort_values(ascending=False).head(2).index.tolist()
    bottom_roles = role_avg.sort_values(ascending=True).head(1).index.tolist()

    most_divisive = []
    if (
        align_df is not None
        and not align_df.empty
        and "Disagreement %" in align_df.columns
        and "Question" in align_df.columns
    ):
        most_divisive = align_df.sort_values("Disagreement %", ascending=False).head(2)["Question"].tolist()

    parts = []
    if len(top_roles) >= 2:
        parts.append(f"Team averages indicate strongest implied ownership in: {top_roles[0]} and {top_roles[1]}.")
    elif len(top_roles) == 1:
        parts.append(f"Team averages indicate strongest implied ownership in: {top_roles[0]}.")

    if bottom_roles:
        parts.append(f"Lowest implied ownership is: {bottom_roles[0]}.")

    if most_divisive:
        if len(most_divisive) > 1:
            parts.append(f"Leadership is most split on questions: {most_divisive[0]} and {most_divisive[1]}.")
        else:
            parts.append(f"Leadership is most split on questions: {most_divisive[0]}.")

    parts.append(
        "This disagreement is a governance signal: priorities are not yet translated into consistent ownership and decision-making."
    )
    return " ".join([p for p in parts if p]).strip()


# -----------------------------
# Table styling helpers
# -----------------------------
def style_table(
    df: pd.DataFrame,
    percent_cols: list[str] | None = None,
    center_cols: list[str] | None = None,
    heatmap_cols: list[str] | None = None,
) -> "pd.io.formats.style.Styler":
    percent_cols = percent_cols or []
    center_cols = center_cols or []
    heatmap_cols = heatmap_cols or []

    fmt = {c: "{:.0f}%" for c in percent_cols if c in df.columns}

    styler = df.style

    # Only apply format if there are columns to format
    if fmt:
        for col, format_str in fmt.items():
            styler = styler.format({col: format_str})

    styler = styler.format(na_rep="")

    styler = (
        styler
        .set_properties(subset=None, **{"text-align": "center", "vertical-align": "middle"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("text-align", "center"), ("font-weight", "600")]},
                {"selector": "td", "props": [("text-align", "center")]},
                {"selector": "table", "props": [("width", "100%")]},
            ]
        )
    )

    # Optional heatmap shading for numeric columns
    if heatmap_cols:
        existing_cols = [c for c in heatmap_cols if c in df.columns]
        if existing_cols:
            styler = styler.background_gradient(cmap="RdYlGn", subset=existing_cols)

    for col in center_cols:
        if col in df.columns:
            idx = df.columns.get_loc(col)
            styler = styler.set_table_styles(
                [
                    {"selector": f"th.col_heading.level0.col{idx}", "props": [("text-align", "center")]},
                    {"selector": f"td.col{idx}", "props": [("text-align", "center")]},
                ],
                overwrite=False,
            )

    return styler


# -----------------------------
# Network graph
# -----------------------------
def make_network_graph(
    role_df: pd.DataFrame,
    highlight_strongest: bool = False,
    top_n: int = 2,
    pad_x: float = 2.2,
    pad_y: float = 1.6,
):
    """
    role_df index: Respondent
    columns: ROLES with percent values (0-100)

    Visual updates:
      - Unique color per respondent (node + edges)
      - Respondent titles wrapped and sized to fit inside circles, with % appended
      - Role nodes neutral, wrapped labels, with avg % appended
      - Optional strongest-edge mode (top_n per respondent) for clarity
    """
    # Order roles and execs by strength to visually prioritize higher signals
    role_nodes = list(
        role_df.mean(axis=0)
        .sort_values(ascending=False)
        .index
    )
    exec_nodes = list(
        role_df.max(axis=1)
        .sort_values(ascending=False)
        .index
    )

    G = nx.Graph()

    # Distinct palette first, then gentle variants (lighter/darker) if we run out
    base_palette = [
        "#1f77b4",  # blue
        "#ff7f0e",  # orange
        "#2ca02c",  # green
        "#d62728",  # red
        "#9467bd",  # purple
        "#8c564b",  # brown
        "#e377c2",  # pink
        "#7f7f7f",  # gray
        "#bcbd22",  # olive
        "#17becf",  # teal
    ]
    variant_factors = [1.0, 1.25, 0.8, 1.5, 0.65]

    def adjust_color(hex_color: str, factor: float) -> tuple[float, float, float, float]:
        """Lighten (>1) or darken (<1) a hex color; returns RGBA tuple."""
        rgb = list(mcolors.to_rgb(hex_color))
        out = []
        for c in rgb:
            if factor >= 1.0:
                c_adj = c + (1 - c) * (factor - 1)
            else:
                c_adj = c * factor
            out.append(min(1.0, max(0.0, c_adj)))
        return (*out, 1.0)

    def wrap_label(s: str, width: int = 12, max_lines: int = 3) -> str:
        s = (s or "").strip()
        if not s:
            return "Anonymous"
        lines = textwrap.wrap(s, width=width)
        if len(lines) <= max_lines:
            return "\n".join(lines)
        kept = lines[:max_lines]
        kept[-1] = kept[-1][: max(0, width - 1)] + "…"
        return "\n".join(kept)

    role_label_map = {
        "Process & Governance Manager": "Process\n&\nGovernance",
        "Director of Infrastructure": "Director of\nInfrastructure",
        "Director of Operations": "Director of\nOperations",
        "Enterprise Architect": "Enterprise\nArchitect",
        "Director of Information Security": "Director of\nInformation\nSecurity",
    }

    for e in exec_nodes:
        G.add_node(e, kind="exec")
    for r in role_nodes:
        G.add_node(r, kind="role")

    # Determine which edges to draw
    def pct_value(exec_name: str, role_name: str) -> float:
        raw = role_df.loc[exec_name, role_name]
        try:
            num = pd.to_numeric(raw, errors="coerce")
            return float(num) if not pd.isna(num) else 0.0
        except Exception:
            return 0.0

    if highlight_strongest:
        for e in exec_nodes:
            series = pd.Series({r: pct_value(e, r) for r in role_nodes})
            top_roles_local = series.nlargest(top_n)
            for r, pct in top_roles_local.items():
                if pct <= 0:
                    continue
                w = pct / 100.0
                G.add_edge(e, r, weight=w, pct=pct)
    else:
        for e in exec_nodes:
            for r in role_nodes:
                pct = pct_value(e, r)
                w = pct / 100.0
                if w <= 0:
                    continue
                G.add_edge(e, r, weight=w, pct=pct)

    pos = {}
    y_step_exec = 17.6 / max(len(exec_nodes), 1)
    for i, e in enumerate(exec_nodes):
        pos[e] = (-36.8, 20.0 - i * y_step_exec)

    y_step_role = 17.6 / max(len(role_nodes), 1)
    for i, r in enumerate(role_nodes):
        pos[r] = (36.8, 20.0 - i * y_step_role)

    bg = "#dfe3eb"
    fig = plt.figure(figsize=(13.5, 7.2), facecolor=bg)
    fig.patch.set_facecolor(bg)
    ax = plt.gca()
    ax.axis("off")
    ax.set_facecolor(bg)

    def color_for_exec(idx: int) -> tuple[float, float, float, float]:
        base = base_palette[idx % len(base_palette)]
        factor = variant_factors[idx // len(base_palette) % len(variant_factors)]
        return adjust_color(base, factor)

    exec_color_map = {e: color_for_exec(i) for i, e in enumerate(exec_nodes)}
    exec_labels = {e: wrap_label(e, width=12, max_lines=3) for e in exec_nodes}

    def exec_node_size(label: str) -> float:
        n = len(label.replace("\n", ""))
        return 4000 + 100 * n  # larger circles to fit wrapped text

    exec_sizes = [exec_node_size(exec_labels[e]) for e in exec_nodes]

    role_strengths = role_df[role_nodes].mean(axis=0).fillna(0.0)
    top_roles = set(role_strengths.sort_values(ascending=False).head(2).index)

    role_sizes: list[float] = []
    role_colors: list[str] = []
    role_edgecolors: list[str] = []
    role_linewidths: list[float] = []
    for r in role_nodes:
        avg = float(role_strengths.get(r, 0.0)) / 100.0
        role_sizes.append(4500 + 3200 * avg)  # larger role circles for labels
        if r in top_roles:
            role_colors.append("#d0e8ff")  # subtle tint for most-implicated roles
            role_edgecolors.append("#4a90e2")
            role_linewidths.append(2.4)
        else:
            role_colors.append("lightgray")
            role_edgecolors.append("white")
            role_linewidths.append(1.0)

    for u, v in G.edges():
        exec_node = u if G.nodes[u]["kind"] == "exec" else v
        w = G[u][v]["weight"]
        lw = 0.8 + 8.5 * w
        a = 0.12 + 0.65 * w
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=[(u, v)],
            width=lw,
            alpha=a,
            edge_color=[exec_color_map[exec_node]],
            ax=ax,
        )

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=exec_nodes,
        node_size=exec_sizes,
        node_color=[exec_color_map[e] for e in exec_nodes],
        linewidths=1.0,
        edgecolors="white",
        ax=ax,
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=role_nodes,
        node_size=role_sizes,
        node_color=role_colors,
        linewidths=role_linewidths,
        edgecolors=role_edgecolors,
        ax=ax,
    )

    def font_size_for(label: str, node_size: float) -> int:
        n = max(1, len(label.replace("\n", "")))
        base = 11 if node_size >= 2600 else 10
        adj = int(round(n / 14.0))
        fs = base - adj
        return max(8, min(12, fs))

    for e in exec_nodes:
        avg_pct = float(role_df.loc[e, role_nodes].mean()) if not role_df.empty else 0.0
        label = f"{exec_labels[e]}\n{avg_pct:.0f}%"
        fs = font_size_for(label, exec_node_size(label))
        x, y = pos[e]
        ax.text(x, y, label, ha="center", va="center", fontsize=fs, color="black", fontweight="bold")

    for r in role_nodes:
        avg_pct = float(role_df[r].mean()) if not role_df.empty else 0.0
        label = f"{role_label_map.get(r, r)}\n{avg_pct:.0f}%"
        x, y = pos[r]
        ax.text(x, y, label, ha="center", va="center", fontsize=9, color="black", fontweight="bold")

    edge_labels = {}
    for u, v in G.edges():
        pct = G[u][v]["pct"]
        if pct >= 65:
            edge_labels[(u, v)] = f"{int(round(pct))}%"
    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=edge_labels,
        font_size=9,
        rotate=False,
        ax=ax,
        bbox=dict(boxstyle="round,pad=0.2", fc="black", ec="none", alpha=0.65),
    )

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    # Fix padding to reduce overlap while keeping circles in view
    ax.set_xlim(min(xs) - 6.0, max(xs) + 6.0)
    ax.set_ylim(min(ys) - 5.0, max(ys) + 5.0)

    ax.text(
        0.0,
        -0.12,
        "How to read: Respondents (left) connect to domains (right). Line thickness indicates stronger implication. Colors represent different respondents. Highlighted role nodes = most implied ownership.",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
    )

    fig.tight_layout()
    return fig


# -----------------------------
# App
# -----------------------------
def main():
    ensure_data_dir()

    # Session state
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "responses" not in st.session_state:
        st.session_state.responses = {}
    if "respondent" not in st.session_state:
        st.session_state.respondent = ""
    if "order" not in st.session_state:
        st.session_state.order = None
    if "_order_prev_respondent" not in st.session_state:
        st.session_state._order_prev_respondent = ""
    question_order = list(range(len(QUESTIONS)))

    tab_survey, tab_agg = st.tabs(["Survey", "Aggregate View"])

    # -----------------------------
    # Survey tab
    # -----------------------------
    with tab_survey:
        st.title("Executive Alignment Mapper")

        c_left, c_right = st.columns([2, 6])
        with c_left:
            st.text_input(
                "Respondent (Name / Title)",
                value=st.session_state.get("respondent", ""),
                placeholder="e.g., Interim CEO, CFO, CIO",
                key="respondent",
            )
        with c_right:
            st.caption("Enter the executive name or title, then proceed through the questions.")

        # Build or refresh the order when respondent changes and no answers exist yet
        if (
            st.session_state.order is None
            or (
                (st.session_state.respondent != st.session_state._order_prev_respondent)
                and not st.session_state.responses
            )
        ):
            st.session_state.order = question_order
            st.session_state.step = 0
            st.session_state._order_prev_respondent = st.session_state.respondent

        order = st.session_state.order or list(range(len(QUESTIONS)))
        total = len(order)
        step = st.session_state.step

        st.progress(min(step / total, 1.0))
        st.caption(f"Question {min(step + 1, total)} of {total}")

        if step >= total:
            st.subheader("Results (This respondent)")
            perc = role_percentages(st.session_state.responses)

            df = (
                pd.DataFrame(
                    [
                        {
                            "Role": role,
                            "Percent": perc[role],
                            "Implication": classify(perc[role]),
                        }
                        for role in ROLES
                    ]
                )
                .sort_values("Percent", ascending=False)
            )

            c1, c2 = st.columns([1, 1])
            with c1:
                df_display = df.copy()
                df_display["Percent"] = df_display["Percent"].round(0)
                st.dataframe(
                    style_table(df_display, percent_cols=["Percent"]),
                    use_container_width=True,
                    hide_index=True,
                )
            with c2:
                st.bar_chart(df.set_index("Role")["Percent"])

            st.divider()
            st.subheader("Save respondent (for aggregate view)")

            save_name = (st.session_state.get("respondent") or "").strip()
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
            export_df.insert(0, "Respondent", save_name or "Anonymous")
            csv_bytes = export_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download respondent results as CSV",
                data=csv_bytes,
                file_name="executive_alignment_mapper_results.csv",
                mime="text/csv",
            )

            c3, c4 = st.columns(2)
            with c3:
                if st.button("Restart survey"):
                    st.session_state.step = 0
                    st.session_state.responses = {}
                    st.session_state.order = question_order
                    st.rerun()
            with c4:
                if st.button("Back to last question"):
                    st.session_state.step = total - 1
                    st.rerun()

        else:
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

            b1, b2, _ = st.columns([1, 1, 6])
            with b1:
                if st.button("Back", disabled=(step == 0)):
                    st.session_state.step = max(step - 1, 0)
                    st.rerun()
            with b2:
                label = "Finish" if step == total - 1 else "Next"
                if st.button(label):
                    st.session_state.step = min(step + 1, total)
                    st.rerun()

    # -----------------------------
    # Aggregate tab
    # -----------------------------
    with tab_agg:
        st.title("Aggregate View (Executive Team)")

        all_payloads = load_jsonl(RESPONSES_JSONL)
        if not all_payloads:
            st.info("No saved respondents yet. Complete the survey and click 'Save respondent' on the results page.")
            return

        cleaned = []
        for p in all_payloads:
            respondent = (p.get("respondent") or "").strip()
            answers = p.get("answers") or {}
            if respondent and isinstance(answers, dict) and answers:
                cleaned.append({"respondent": respondent, "answers": answers, "timestamp": p.get("timestamp")})

        if not cleaned:
            st.warning("Saved data exists, but no valid respondent entries were found (missing respondent name or answers).")
            return

        role_rows = []
        for item in cleaned:
            respondent = item["respondent"]
            perc = role_percentages(item["answers"])
            row = {"Respondent": respondent, **perc}
            role_rows.append(row)

        role_df = (
            pd.DataFrame(role_rows)
            .drop_duplicates(subset=["Respondent"], keep="last")
            .set_index("Respondent")
        )

        # -----------------------------
        # Why this matters (credibility)
        # -----------------------------
        st.subheader("Why this matters")
        st.info(
            "Most real-world incidents do not require advanced attacks. Two consistent drivers are credential abuse "
            "and preventable control gaps. Industry data backs this up:\n\n"
            "- IBM (2025): global average data breach cost is about $4.4M.\n"
            "- Verizon DBIR (2025): Basic Web Application Attacks frequently involve stolen credentials (around 88%).\n\n"
            "This screen is meant to reduce ambiguity: where leadership is split, the organization defaults to inconsistent decisions."
        )

        # -----------------------------
        # Team Summary
        # -----------------------------
        st.subheader("Team Summary")

        role_avg = role_df.mean(axis=0).reindex(ROLES).fillna(0.0).round(0).astype(int)
        top_role = role_avg.sort_values(ascending=False).index[0] if len(role_avg) else None

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Respondents saved", int(role_df.shape[0]))
        with c2:
            st.metric("Top role (avg)", top_role or "N/A")
        with c3:
            st.metric("Top role average %", f"{float(role_avg.max()):.0f}%")

        # -----------------------------
        # Strong / Weak signals
        # -----------------------------
        st.subheader("Signal Highlights")
        strong_roles = [r for r, v in role_avg.items() if v >= 70]
        weak_roles = [r for r, v in role_avg.items() if v <= 40]

        strong_text = ", ".join(strong_roles) if strong_roles else "None"
        weak_text = ", ".join(weak_roles) if weak_roles else "None"

        st.write(f"- Strong signals (≥70%): {strong_text}")
        st.write(f"- Weak signals (≤40%): {weak_text}")

        # -----------------------------
        # Contextual plain-English readout
        # -----------------------------
        implications = role_implications_plain_english(role_avg)
        st.subheader(implications["headline"])
        for b in implications["bullets"]:
            st.write(f"- {b}")
        if implications.get("note"):
            st.caption(implications["note"])

        # -----------------------------
        # Alignment / hotspots prep
        # -----------------------------
        answer_dicts = [item["answers"] for item in cleaned]
        align_df = calc_alignment(answer_dicts)

        # -----------------------------
        # Respondent Results
        # -----------------------------
        st.subheader("Respondent Results (Role Implication %)")

        display_df = role_df.copy().reindex(columns=ROLES).fillna(0.0).round(0)
        st.dataframe(
            style_table(display_df.reset_index(), percent_cols=ROLES, heatmap_cols=ROLES),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Interpretation: Higher % means that respondent's answers imply stronger need for that role to own or coordinate decisions."
        )

        # -----------------------------
        # Team Averages
        # -----------------------------
        st.subheader("Team Averages (by Role)")

        avg_df = pd.DataFrame(
            [
                {"Role": r, "Average %": int(role_avg.get(r, 0)), "Implication": classify(float(role_avg.get(r, 0)))}
                for r in ROLES
            ]
        ).sort_values("Average %", ascending=False)

        avg_df_display = avg_df.copy()

        c4, c5 = st.columns([1, 1])
        with c4:
            st.dataframe(
                style_table(avg_df_display, percent_cols=["Average %"]),
                use_container_width=True,
                hide_index=True,
            )
        with c5:
            st.bar_chart(avg_df_display.set_index("Role")["Average %"])

        # -----------------------------
        # Executive Decision Hotspots (plus briefing)
        # -----------------------------
        st.subheader("Executive Decision Hotspots")

        exec_df_display = pd.DataFrame()

        if align_df.empty:
            st.info("Not enough data yet to identify decision hotspots.")
        else:
            q_lookup = {int(qid): {"text": qtext, "options": options} for (qid, qtext, options, _, _) in QUESTIONS}

            top_n = 6
            hotspots = align_df.sort_values("Disagreement %", ascending=False).head(top_n).copy()

            def top_choice_row(row: pd.Series) -> str:
                counts = {"A": int(row.get("A", 0)), "B": int(row.get("B", 0)), "C": int(row.get("C", 0))}
                return max(counts, key=lambda k: counts[k])

            hotspots["Top Choice"] = hotspots.apply(top_choice_row, axis=1)

            exec_rows = []
            for _, r in hotspots.iterrows():
                qnum = int(r["Question"])
                meta = q_lookup.get(qnum, {})
                qtext = meta.get("text", f"Question {qnum}")
                opts = meta.get("options", {})
                top_letter = r["Top Choice"]
                top_label = opts.get(top_letter, top_letter)
                disagreement_pct = int(round(float(r["Disagreement %"]), 0))

                exec_rows.append({
                    "Question": qnum,
                    "Decision topic": qtext,
                    "Most common answer": f"{top_letter}: {top_label}",
                    "Split": f"A={int(r.get('A', 0))}, B={int(r.get('B', 0))}, C={int(r.get('C', 0))}",
                    "Disagreement %": disagreement_pct,
                })

            exec_df = pd.DataFrame(exec_rows).sort_values("Disagreement %", ascending=False)
            exec_df_display = exec_df.copy()
            exec_df_display["Disagreement %"] = exec_df_display["Disagreement %"].round(0)

            # Briefing for the top hotspot
            briefing = hotspot_briefing_row(exec_df)
            if briefing:
                st.subheader("Hotspot briefing")
                lines = [
                    f"**Question {briefing['qnum']} ({briefing['theme']}) — {briefing.get('disagreement_pct', 0)}% disagreement**",
                    f"**Topic:** {briefing['topic']}",
                ]
                if briefing.get("most_common"):
                    lines.append(f"**Most common answer:** {briefing['most_common']}")
                lines.append(f"**Why it matters:** {briefing['cause']}")
                lines.append(f"**Decision to make:** {briefing['decision']}")
                st.info("\n\n".join(lines))

            st.caption(
                "These are the topics where leadership answers diverge most. Treat these as decision points: clarify ownership, guardrails, or escalation paths."
            )
            st.dataframe(
                style_table(exec_df_display, percent_cols=["Disagreement %"], center_cols=["Question"]),
                use_container_width=True,
                hide_index=True,
            )

            # Top consensus (lowest disagreement)
            consensus_df = align_df.sort_values("Disagreement %", ascending=True).head(3)
            if not consensus_df.empty:
                st.subheader("Top Consensus Topics")
                q_text_map = {int(q[0]): q[1] for q in QUESTIONS}
                consensus_df_display = consensus_df[["Question", "Agreement %", "Disagreement %", "A", "B", "C"]].copy()
                consensus_df_display["Question text"] = consensus_df_display["Question"].map(q_text_map)
                consensus_df_display["Agreement %"] = consensus_df_display["Agreement %"].round(0).astype(int)
                consensus_df_display["Disagreement %"] = consensus_df_display["Disagreement %"].round(0).astype(int)
                # Map option letters to text for readability
                def most_chosen_with_label(row: pd.Series) -> str:
                    counts = [("A", row.get("A", 0)), ("B", row.get("B", 0)), ("C", row.get("C", 0))]
                    letter, _ = max(counts, key=lambda kv: kv[1])
                    opts = {}
                    qid = int(row["Question"])
                    # Build lookup for options
                    for q in QUESTIONS:
                        if int(q[0]) == qid:
                            opts = q[2]
                            break
                    return f"{letter}: {opts.get(letter, '')}"

                consensus_df_display["Most chosen"] = consensus_df_display.apply(most_chosen_with_label, axis=1)
                st.dataframe(
                    style_table(
                        consensus_df_display[["Question", "Question text", "Agreement %", "Disagreement %", "A", "B", "C", "Most chosen"]],
                        percent_cols=["Agreement %", "Disagreement %"],
                        center_cols=["Question"],
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

        # -----------------------------
        # Recommended actions (contextual)
        # -----------------------------
        st.subheader("What to decide next")
        actions = recommended_actions(role_avg, exec_df_display if not exec_df_display.empty else None)
        for a in actions:
            st.write(f"- {a}")

        # -----------------------------
        # Network View
        # -----------------------------
        st.subheader("Exec-to-Role Network View")
        highlight_mode = st.checkbox("Highlight strongest edges (top 2 per respondent)", value=False)
        try:
            fig = make_network_graph(display_df, highlight_strongest=highlight_mode, top_n=2)
            st.pyplot(fig, clear_figure=True)
        except Exception as e:
            st.warning(f"Network graph could not be rendered: {e}")

        # -----------------------------
        # Export / Data management
        # -----------------------------
        st.subheader("Export (Aggregate)")
        export_role_df = display_df.reset_index()
        export_role_df.insert(0, "Timestamp (UTC)", datetime.utcnow().strftime("%Y-%m-%d %H:%M"))
        export_role_df.insert(1, "Respondent count", int(role_df.shape[0]))
        csv_bytes = export_role_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download aggregate results as CSV",
            data=csv_bytes,
            file_name="executive_alignment_mapper_aggregate.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Data Management")
        st.caption("This clears the saved respondents file on disk. Use with caution.")
        if st.button("Clear saved respondents"):
            try:
                if os.path.exists(RESPONSES_JSONL):
                    os.remove(RESPONSES_JSONL)
                st.success("Cleared. Reload the page.")
            except Exception as e:
                st.error(f"Failed to clear saved respondents: {e}")


def _top_roles(role_avg: pd.Series, n: int = 2) -> list[str]:
    if role_avg is None or role_avg.empty:
        return []
    return role_avg.sort_values(ascending=False).head(n).index.tolist()


def role_implications_plain_english(role_avg: pd.Series) -> dict:
    """
    Returns a few short, executive-friendly paragraphs based on which roles score highest,
    plus a warning when the signal is ambiguous (roles cluster too closely).
    """
    if role_avg is None or role_avg.empty:
        return {"headline": "No aggregate results yet.", "bullets": [], "note": ""}

    ordered = role_avg.sort_values(ascending=False)
    top2 = _top_roles(role_avg, 2)
    spread = float(ordered.max() - ordered.min()) if len(ordered) else 0.0

    headline = "What your answers imply"
    bullets: list[str] = []

    # If roles are clustered, call out ambiguity
    if spread < 8:
        bullets.append(
            "Your answers cluster across roles. That signals shared ownership, which often becomes unclear ownership unless you explicitly define decision rights."
        )

    # Role-specific implications (kept neutral, no “leading” language)
    role_msgs = {
        "Director of Operations": [
            "Leadership is prioritizing predictable end-user outcomes: service continuity, fast restoration, and reduced friction.",
            "If ownership is unclear here, recurring support pain and inconsistent service expectations tend to persist.",
        ],
        "Director of Infrastructure": [
            "Leadership is signaling that uptime, resilience, and stability tradeoffs need a clear owner and consistent standards.",
            "If ownership is unclear here, reliability issues often show up as repeated incidents and emergency fixes.",
        ],
        "Enterprise Architect": [
            "Leadership is signaling that long-term direction and clean integration matter, not just short-term delivery.",
            "If ownership is unclear here, tool sprawl and integration costs usually rise over time.",
        ],
        "Process & Governance Manager": [
            "Leadership is signaling a need for repeatable decisions: clear guardrails, consistent exceptions, and documented escalation paths.",
            "If ownership is unclear here, exceptions and one-off decisions become permanent and hard to unwind.",
        ],
        "Director of Information Security": [
            "Leadership is signaling that cyber risk tradeoffs should be evaluated consistently, with clear guardrails and escalation thresholds.",
            "If ownership is unclear here, risk acceptance happens unevenly and visibility tends to come only after something breaks.",
        ],
    }

    for r in top2:
        for line in role_msgs.get(r, []):
            bullets.append(line)

    note = (
        "This is not an org chart recommendation. It’s a readout of what your combined answers imply about where consistent ownership and decision coordination are most needed."
    )
    return {"headline": headline, "bullets": bullets, "note": note}


def hotspot_theme(qnum: int) -> str:
    """
    Light theme mapping for executive narration.
    Adjust these buckets any time without touching scoring.
    """
    ops = {1, 4, 8, 34}
    infra = {35, 6}
    arch = {10, 11, 12, 33, 38}
    governance = {5, 7, 9, 16, 17, 18, 36, 40}
    security = {2, 3, 13, 14, 15, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 37, 39}

    if qnum in ops:
        return "Operations"
    if qnum in infra:
        return "Infrastructure"
    if qnum in arch:
        return "Architecture"
    if qnum in governance:
        return "Governance"
    if qnum in security:
        return "Cyber Risk"
    return "General"


def hotspot_briefing_row(exec_df: pd.DataFrame) -> dict:
    """
    Returns an executive-friendly narrative for the single most divisive hotspot.
    """
    if exec_df is None or exec_df.empty:
        return {}

    row = exec_df.sort_values("Disagreement %", ascending=False).iloc[0]
    qnum = int(row["Question"])
    theme = hotspot_theme(qnum)
    try:
        disagreement_pct = int(round(float(row.get("Disagreement %", 0)), 0))
    except Exception:
        disagreement_pct = 0

    cause_map = {
        "Operations": "This kind of split usually shows up as inconsistent support expectations and uneven user experience.",
        "Infrastructure": "This kind of split usually shows up as unclear reliability targets and repeated ‘emergency’ work.",
        "Architecture": "This kind of split usually shows up as tool sprawl and integration work that becomes unavoidable later.",
        "Governance": "This kind of split usually shows up as inconsistent exceptions, unclear decision rights, and uneven enforcement.",
        "Cyber Risk": "This kind of split usually shows up as inconsistent risk acceptance and surprise escalation when something goes wrong.",
        "General": "This kind of split usually shows up as inconsistent decisions across teams.",
    }

    decision_map = {
        "Operations": "Decision to make: define service expectations and who owns the final call when usability and control requirements conflict.",
        "Infrastructure": "Decision to make: define uptime/reliability targets and who owns the final call when cost and resilience conflict.",
        "Architecture": "Decision to make: define the consolidation principle (standardize vs local autonomy) and who arbitrates exceptions.",
        "Governance": "Decision to make: define decision rights (who can approve what), documentation requirements, and escalation thresholds.",
        "Cyber Risk": "Decision to make: define risk acceptance authority, required documentation, and when executive escalation is mandatory.",
        "General": "Decision to make: clarify ownership and escalation paths for this topic.",
    }

    return {
        "qnum": qnum,
        "theme": theme,
        "topic": str(row.get("Decision topic", f"Question {qnum}")),
        "most_common": str(row.get("Most common answer", "")),
        "disagreement_pct": disagreement_pct,
        "cause": cause_map.get(theme, cause_map["General"]),
        "decision": decision_map.get(theme, decision_map["General"]),
    }


def recommended_actions(role_avg: pd.Series, exec_df: pd.DataFrame) -> list[str]:
    """
    Generates 3-5 concrete actions based on the strongest role signals and #1 hotspot theme.
    """
    actions: list[str] = []

    top2 = _top_roles(role_avg, 2)
    briefing = hotspot_briefing_row(exec_df)
    theme = briefing.get("theme", "")

    # Always useful action
    actions.append("Document decision rights: who can approve, who must be consulted, and when executive escalation is required.")

    # Role-driven actions (neutral framing)
    if "Director of Operations" in top2:
        actions.append("Set service expectations (response/restore targets) for user-impacting issues and define what tradeoffs are acceptable.")
    if "Director of Infrastructure" in top2:
        actions.append("Define reliability and resilience targets (uptime, recovery, change discipline) and align funding to meet them.")
    if "Enterprise Architect" in top2:
        actions.append("Adopt an enterprise standardization principle (platform consolidation vs local autonomy) and enforce it consistently.")
    if "Process & Governance Manager" in top2:
        actions.append("Establish an exceptions process: what qualifies, how it is documented, how often it is reviewed, and who can approve.")
    if "Director of Information Security" in top2:
        actions.append("Define risk acceptance guardrails: what can be accepted at the director level vs what must go to the executive level.")

    # Theme-driven action
    if theme:
        actions.append(f"Resolve the top decision hotspot (theme: {theme}) by defining a clear owner and default rule for making the tradeoff.")

    # Keep it tight
    return actions[:5]


if __name__ == "__main__":
    main()

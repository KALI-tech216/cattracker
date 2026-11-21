from datetime import date
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

CSV_PATH = Path("cat_question_logs.csv")

COLUMNS = [
    "date",
    "section",
    "topic",
    "level",
    "solved",
    "correct",
    "wrong",
    "unattempted",
    "accuracy_pct",
    "net_score",
    "time_mins",
    "notes",
]

SECTION_TOPICS = {
    "Quant": [
        "Time, Speed & Distance",
        "Profit, Loss & Discount",
        "Time & Work",
        "Averages",
        "Percentages",
        "Ratio, Proportion & Variation",
        "Simple & Compound Interest",
        "Alligations & Mixtures",
        "Number System",
        "Algebra & Functions",
        "Geometry & Mensuration",
    ],
    "DILR": [
        "Arrangements & Grids",
        "Games & Tournaments",
        "Charts, Tables & Caselets",
        "Routes, Networks & Venn",
        "Quant-Based DILR",
    ],
    "VARC": [
        "RC Passages",
        "Para Summary",
        "Para Jumbles",
        "Odd One Out",
    ],
}

st.set_page_config(page_title="CAT Daily Question Tracker", layout="wide")


def load_logs(path: Path) -> pd.DataFrame:
    if not path.exists():
        df = pd.DataFrame(columns=COLUMNS)
        df.to_csv(path, index=False)
        return df

    df = pd.read_csv(path)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS]
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        for num_col in ["solved", "correct", "wrong", "unattempted", "time_mins"]:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0).astype(int)
        df["accuracy_pct"] = pd.to_numeric(df["accuracy_pct"], errors="coerce").fillna(0.0)
        df["net_score"] = pd.to_numeric(df["net_score"], errors="coerce").fillna(0).astype(int)
    return df


def save_logs(df: pd.DataFrame, path: Path) -> None:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out[COLUMNS].to_csv(path, index=False)


def compute_metrics(solved: int, correct: int, wrong: int) -> tuple[int, float, int]:
    unattempted = max(0, solved - correct - wrong)
    attempted = correct + wrong
    accuracy_pct = round((correct / attempted) * 100, 1) if attempted > 0 else 0.0
    net_score = (correct * 3) - wrong
    return unattempted, accuracy_pct, net_score


st.title("CAT Question & Accuracy Tracker")
st.caption("Logs sessions locally to `cat_question_logs.csv` with accuracy and `+3 / -1` net score tracking.")

df = load_logs(CSV_PATH)

with st.sidebar:
    st.header("Targets & File")
    weekly_target = st.number_input("Weekly Question Target", min_value=10, max_value=1000, value=150, step=10)
    st.info(f"Storage file: `{CSV_PATH.resolve()}`")

    if not df.empty:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV Backup",
            data=csv_bytes,
            file_name="cat_question_logs_backup.csv",
            mime="text/csv",
        )

st.subheader("Log Practice Session")

col_s1, col_s2, col_s3 = st.columns([1.2, 1.5, 1.3])
with col_s1:
    session_date = st.date_input("Date", value=date.today())
with col_s2:
    section = st.selectbox("Section", options=list(SECTION_TOPICS.keys()))
with col_s3:
    topic = st.selectbox("Topic", options=SECTION_TOPICS[section])

with st.form("log_session_form", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        level = st.selectbox("Difficulty / LOD", options=["LOD 1", "LOD 2", "LOD 3", "Mixed / Sectional"])
    with c2:
        solved = st.number_input("Questions Solved / Attempted", min_value=1, max_value=300, value=15, step=1)
    with c3:
        correct = st.number_input("Correct Answers", min_value=0, max_value=300, value=11, step=1)
    with c4:
        wrong = st.number_input("Wrong Answers", min_value=0, max_value=300, value=3, step=1)

    c5, c6 = st.columns([1, 3])
    with c5:
        time_mins = st.number_input("Time Spent (mins)", min_value=1, max_value=600, value=45, step=5)
    with c6:
        notes = st.text_input("Notes (optional)", placeholder="e.g., Boat & stream tricky cases, rushed last 2 questions")

    submitted = st.form_submit_button("Save Session to CSV", type="primary")

if submitted:
    if correct + wrong > solved:
        st.error("Correct + Wrong cannot exceed total Questions Solved/Attempted.")
    else:
        unattempted, accuracy_pct, net_score = compute_metrics(int(solved), int(correct), int(wrong))
        new_row = pd.DataFrame(
            [
                {
                    "date": session_date,
                    "section": section,
                    "topic": topic,
                    "level": level,
                    "solved": int(solved),
                    "correct": int(correct),
                    "wrong": int(wrong),
                    "unattempted": unattempted,
                    "accuracy_pct": accuracy_pct,
                    "net_score": net_score,
                    "time_mins": int(time_mins),
                    "notes": notes.strip(),
                }
            ]
        )
        df = pd.concat([df, new_row], ignore_index=True)
        save_logs(df, CSV_PATH)
        st.success(f"Saved {solved} questions ({accuracy_pct}% accuracy, Net: {net_score:+d}) for {topic}.")
        st.rerun()

st.divider()

if df.empty:
    st.info("No sessions logged yet. Fill out the form above to create your first entry in `cat_question_logs.csv`.")
else:
    total_solved = int(df["solved"].sum())
    total_correct = int(df["correct"].sum())
    total_wrong = int(df["wrong"].sum())
    total_attempted = total_correct + total_wrong
    overall_acc = round((total_correct / total_attempted) * 100, 1) if total_attempted > 0 else 0.0
    total_net = int(df["net_score"].sum())

    # Last 7 days total
    seven_days_ago = date.today() - pd.Timedelta(days=6)
    last_7d_solved = int(df[df["date"] >= seven_days_ago]["solved"].sum())
    weekly_pct = min(100.0, round((last_7d_solved / weekly_target) * 100, 1)) if weekly_target > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Questions Logged", f"{total_solved}")
    m2.metric("Overall Attempt Accuracy", f"{overall_acc}%")
    m3.metric("Cumulative Net Score (+3/-1)", f"{total_net:+d}")
    m4.metric("Last 7 Days vs Target", f"{last_7d_solved} / {weekly_target}", delta=f"{weekly_pct}%")

    st.progress(weekly_pct / 100.0, text=f"Rolling 7-Day Target Progress: {weekly_pct}%")

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.subheader("Accuracy (%) by Section")
        sec_grp = (
            df.groupby("section", as_index=False)
            .agg(correct=("correct", "sum"), wrong=("wrong", "sum"), solved=("solved", "sum"))
        )
        sec_grp["attempted"] = sec_grp["correct"] + sec_grp["wrong"]
        sec_grp["accuracy"] = sec_grp.apply(
            lambda r: (r["correct"] / r["attempted"] * 100) if r["attempted"] > 0 else 0.0, axis=1
        )

        fig, ax = plt.subplots(figsize=(6, 3.8))
        bars = ax.bar(sec_grp["section"], sec_grp["accuracy"])
        ax.set_ylim(0, 105)
        ax.set_ylabel("Accuracy (%)")
        ax.set_title("Attempt Accuracy by Section")
        for bar, (_, row) in zip(bars, sec_grp.iterrows()):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2,
                f"{row['accuracy']:.1f}%\n({int(row['solved'])} Qs)",
                ha="center",
                va="bottom",
                fontsize=9,
            )
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    with chart_right:
        st.subheader("Daily Trend: Questions Solved & Accuracy")
        daily_grp = (
            df.groupby("date", as_index=False)
            .agg(solved=("solved", "sum"), correct=("correct", "sum"), wrong=("wrong", "sum"))
            .sort_values("date")
        )
        daily_grp["attempted"] = daily_grp["correct"] + daily_grp["wrong"]
        daily_grp["accuracy"] = daily_grp.apply(
            lambda r: (r["correct"] / r["attempted"] * 100) if r["attempted"] > 0 else 0.0, axis=1
        )

        fig2, ax2 = plt.subplots(figsize=(6, 3.8))
        ax2.plot(pd.to_datetime(daily_grp["date"]), daily_grp["accuracy"], marker="o", label="Accuracy (%)")
        ax2.set_ylim(0, 105)
        ax2.set_ylabel("Accuracy (%)")
        ax2.set_title("Daily Accuracy Trajectory")
        ax2.tick_params(axis="x", rotation=30)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    st.subheader("Topic-Wise Breakdown")
    topic_grp = (
        df.groupby(["section", "topic"], as_index=False)
        .agg(
            sessions=("topic", "count"),
            solved=("solved", "sum"),
            correct=("correct", "sum"),
            wrong=("wrong", "sum"),
            net_score=("net_score", "sum"),
            mins=("time_mins", "sum"),
        )
    )
    topic_grp["attempted"] = topic_grp["correct"] + topic_grp["wrong"]
    topic_grp["accuracy_%"] = topic_grp.apply(
        lambda r: round((r["correct"] / r["attempted"]) * 100, 1) if r["attempted"] > 0 else 0.0, axis=1
    )
    topic_grp = topic_grp.sort_values(by=["solved", "accuracy_%"], ascending=[False, True])
    st.dataframe(topic_grp, use_container_width=True, hide_index=True)

    st.subheader("Session History")
    filter_sec = st.multiselect(
        "Filter by Section",
        options=list(SECTION_TOPICS.keys()),
        default=list(SECTION_TOPICS.keys()),
    )
    filtered_df = df[df["section"].isin(filter_sec)].sort_values(by="date", ascending=False)
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
# src/app.py
"""
app.py — Streamlit UI for the Resume App.
Four tabs: Configure, Run & Schedule, Results, Logs.
Talks to FastAPI backend via api_client only.
"""

from pathlib import Path
import streamlit as st
import api_client

st.set_page_config(
    page_title="Resume App",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Resume App")

TRACKS = {
    "generic-saas": "Generic SaaS VP/Director",
    "data-ai": "Data + AI",
    "identity-security": "Identity + Security",
}

tab_configure, tab_run, tab_results, tab_logs = st.tabs([
    "⚙️ Configure", "▶ Run & Schedule", "📊 Results", "🪵 Logs"
])

# ── Tab 1: Configure ──────────────────────────────────────────────────────────
with tab_configure:
    st.header("Job Criteria Configuration")

    selected_track = st.radio(
        "Job Track",
        options=list(TRACKS.keys()),
        format_func=lambda k: TRACKS[k],
        horizontal=True,
    )

    try:
        track_config = api_client.get_track_config(selected_track)
    except Exception:
        st.error("Could not load config — is the API running on port 8000?")
        track_config = {"titles": [], "keywords": {"required": [], "preferred": [], "domain_exclude": []}}

    st.subheader("Job Titles")
    titles = st.text_area(
        "Titles (one per line)",
        value="\n".join(track_config.get("titles", [])),
        height=120,
    )

    st.subheader("Keywords")
    col1, col2 = st.columns(2)
    with col1:
        kw = track_config.get("keywords", {})
        required = st.text_area(
            "Required (one per line)",
            value="\n".join(kw.get("required", [])),
            height=150,
        )
        domain_exclude = st.text_area(
            "Domain Exclude (one per line)",
            value="\n".join(kw.get("domain_exclude", [])),
            height=150,
        )
    with col2:
        preferred = st.text_area(
            "Preferred (one per line)",
            value="\n".join(kw.get("preferred", [])),
            height=150,
        )

    st.subheader("Shared Filters")
    try:
        shared = api_client.get_shared_config()
    except Exception:
        shared = {"location": {"remote": True, "country": "US"},
                  "posting": {"max_days": 14}, "company": {"min_size": 50}}

    col3, col4, col5 = st.columns(3)
    with col3:
        remote = st.checkbox("Remote only", value=shared.get("location", {}).get("remote", True))
        country = st.text_input("Country", value=shared.get("location", {}).get("country", "US"))
    with col4:
        max_days = st.number_input(
            "Posted within (days)", min_value=1, max_value=90,
            value=shared.get("posting", {}).get("max_days", 14)
        )
    with col5:
        min_size = st.number_input(
            "Min company size", min_value=1,
            value=shared.get("company", {}).get("min_size", 50)
        )

    if st.button("💾 Save Config", type="primary"):
        def parse_lines(text):
            return [l.strip() for l in text.strip().splitlines() if l.strip()]

        updated_track = {
            **track_config,
            "titles": parse_lines(titles),
            "keywords": {
                "required": parse_lines(required),
                "preferred": parse_lines(preferred),
                "domain_exclude": parse_lines(domain_exclude),
            },
        }
        ok1 = api_client.save_track_config(selected_track, updated_track)
        updated_shared = {
            "location": {"remote": remote, "country": country},
            "posting": {"max_days": int(max_days)},
            "company": {"min_size": int(min_size)},
            "keywords_file": "config/keywords.yaml",
        }
        ok2 = api_client.save_shared_config(updated_shared)
        if ok1 and ok2:
            st.success("Config saved!")
        else:
            st.error("Save failed — check API connection.")


# ── Tab 2: Run & Schedule ─────────────────────────────────────────────────────
with tab_run:
    st.header("Run & Schedule")

    col_run, col_status = st.columns([1, 2])
    with col_run:
        run_track = st.selectbox(
            "Track to run",
            options=["all"] + list(TRACKS.keys()),
            format_func=lambda k: "All tracks" if k == "all" else TRACKS[k],
        )
        if st.button("▶ Run Now", type="primary"):
            with st.spinner("Running job search..."):
                try:
                    result = api_client.trigger_run(track=run_track, source="ui")
                    st.success(
                        f"Done! Found {result.get('jobs_found', 0)} jobs. "
                        f"Run ID: {result.get('run_id')}"
                    )
                except Exception as e:
                    st.error(f"Run failed: {e}")

    with col_status:
        st.subheader("Last Run Status")
        try:
            status = api_client.get_run_status()
            if status.get("status") == "no_runs":
                st.info("No runs yet.")
            else:
                st.metric("Jobs Found", status.get("jobs_found", 0))
                st.caption(f"Run ID: {status.get('run_id')}")
                st.caption(f"Track: {status.get('track')}")
                st.caption(f"Completed: {status.get('completed_at', 'unknown')}")
        except Exception:
            st.warning("Could not load run status.")

    st.divider()
    st.subheader("Daily Schedule")
    try:
        schedule = api_client.get_schedule()
    except Exception:
        schedule = {"enabled": False, "hour": 8, "minute": 0, "tracks": "all", "next_run": None}

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        enabled = st.checkbox("Enable daily schedule", value=schedule.get("enabled", False))
    with col_s2:
        hour = st.number_input("Hour (24h)", min_value=0, max_value=23, value=schedule.get("hour", 8))
    with col_s3:
        minute = st.number_input("Minute", min_value=0, max_value=59, value=schedule.get("minute", 0))

    if schedule.get("next_run"):
        st.caption(f"Next run: {schedule['next_run']}")

    if st.button("💾 Save Schedule"):
        ok = api_client.save_schedule({
            "enabled": enabled,
            "hour": int(hour),
            "minute": int(minute),
            "tracks": "all",
        })
        st.success("Schedule saved!") if ok else st.error("Save failed.")


# ── Tab 3: Results ────────────────────────────────────────────────────────────
with tab_results:
    st.header("Results")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_track = st.selectbox(
            "Filter by track",
            options=["all"] + list(TRACKS.keys()),
            format_func=lambda k: "All tracks" if k == "all" else TRACKS[k],
        )
    with col_f2:
        result_limit = st.number_input("Max results", min_value=5, max_value=100, value=20)

    st.button("🔄 Refresh")

    track_param = None if filter_track == "all" else filter_track
    try:
        runs = api_client.get_results(track=track_param, limit=int(result_limit))
    except Exception:
        runs = []
        st.warning("Could not load results — is the API running?")

    if not runs:
        st.info("No results yet. Run a job search first.")
    else:
        for run in runs:
            track_label = TRACKS.get(run.get("track", ""), run.get("track", ""))
            st.subheader(f"Run: {run.get('run_id')} — {track_label}")
            st.caption(
                f"Triggered by: {run.get('triggered_by')} · "
                f"Completed: {run.get('completed_at', '')}"
            )
            jobs = run.get("jobs", [])
            skipped = run.get("skipped", [])

            col_kept, col_skipped = st.columns(2)
            with col_kept:
                st.markdown(f"**✅ Kept ({len(jobs)})**")
                if not jobs:
                    st.write("_No matching jobs._")
                for job in jobs:
                    score = job.get("fit_score", "?")
                    with st.expander(f"{job.get('title')} — {job.get('company')} · {score}/100"):
                        st.write(f"📍 {job.get('location')} · Posted: {job.get('posted_date')}")
                        if job.get("gaps"):
                            st.write("**Gaps:**", ", ".join(job["gaps"]))
                        if job.get("url"):
                            st.link_button("View on LinkedIn", job["url"])

            with col_skipped:
                st.markdown(f"**❌ Filtered out ({len(skipped)})**")
                if not skipped:
                    st.write("_Nothing filtered._")
                for s in skipped:
                    with st.expander(f"{s.get('title')} — {s.get('company')}"):
                        st.caption(s.get("reason", "No reason recorded"))
                        if s.get("url"):
                            st.link_button("View on LinkedIn", s["url"])

            st.divider()


# ── Tab 4: Logs ───────────────────────────────────────────────────────────────
with tab_logs:
    st.header("Run Logs")

    try:
        runs = api_client.get_results(limit=20)
        run_ids = [r["run_id"] for r in runs] if runs else []
    except Exception:
        run_ids = []

    log_col1, log_col2 = st.columns([2, 1])
    with log_col1:
        selected_log_run = st.selectbox(
            "Select run",
            options=["latest"] + run_ids,
        )
    with log_col2:
        st.write("")  # spacer
        load_logs = st.button("🔄 Load Logs")

    try:
        logs = api_client.get_logs(selected_log_run)
    except Exception:
        logs = {"events": [], "llm": [], "debug": []}

    col_ev, col_llm, col_dbg = st.columns(3)
    with col_ev:
        st.subheader("📋 Run Events")
        st.text_area(
            "events",
            value="\n".join(logs.get("events", [])) or "(no events yet)",
            height=400,
            label_visibility="collapsed",
        )
    with col_llm:
        st.subheader("🤖 LLM Decisions")
        st.text_area(
            "llm",
            value="\n".join(logs.get("llm", [])) or "(no LLM decisions yet)",
            height=400,
            label_visibility="collapsed",
        )
    with col_dbg:
        st.subheader("🔍 Full Debug")
        st.text_area(
            "debug",
            value="\n".join(logs.get("debug", [])) or "(no debug logs yet)",
            height=400,
            label_visibility="collapsed",
        )

    # Screenshots
    st.divider()
    st.subheader("📸 Screenshots")

    if selected_log_run and selected_log_run != "latest":
        screenshot_dir = Path(__file__).parent.parent / "data" / "screenshots" / selected_log_run
    else:
        # Find most recent screenshot dir
        base = Path(__file__).parent.parent / "data" / "screenshots"
        dirs = sorted(base.glob("*/"), reverse=True) if base.exists() else []
        screenshot_dir = dirs[0] if dirs else Path("/nonexistent")

    if screenshot_dir.exists():
        imgs = sorted(screenshot_dir.glob("*.png"))
        if imgs:
            cols = st.columns(min(len(imgs), 4))
            for i, img_path in enumerate(imgs[:8]):
                with cols[i % min(len(imgs), 4)]:
                    st.image(str(img_path), caption=img_path.stem, use_column_width=True)
        else:
            st.info("No screenshots for this run.")
    else:
        st.info("No screenshots yet — screenshots are captured during live job searches.")

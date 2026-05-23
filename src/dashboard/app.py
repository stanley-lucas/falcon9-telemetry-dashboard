import os

import httpx
import plotly.express as px
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@st.cache_data(ttl=300)
def fetch_launches(limit: int = 200) -> list[dict]:
    response = httpx.get(f"{API_BASE_URL}/launches", params={"limit": limit})
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300)
def fetch_landing_stats() -> dict:
    response = httpx.get(f"{API_BASE_URL}/launches/stats/landing")
    response.raise_for_status()
    return response.json()


def main() -> None:
    st.set_page_config(page_title="Falcon 9 Telemetry", page_icon="🚀", layout="wide")
    st.title("Falcon 9 Launch Telemetry Dashboard")
    st.caption("Historical data from the SpaceX public API · Refreshes every 5 minutes")

    with st.spinner("Loading launch data..."):
        launches = fetch_launches()
        stats = fetch_landing_stats()

    # --- KPI row ---
    col1, col2, col3, col4 = st.columns(4)
    total = len(launches)
    successes = sum(1 for launch in launches if launch["success"] is True)
    col1.metric("Total Launches", total)
    col2.metric("Mission Success Rate", f"{successes / total * 100:.1f}%" if total else "—")
    col3.metric("Landing Attempts", stats["total_attempts"])
    col4.metric("Landing Success Rate", f"{stats['success_rate_pct']:.1f}%")

    st.divider()

    # --- Launch timeline ---
    st.subheader("Launch Timeline")
    import pandas as pd
    df = pd.DataFrame(launches)
    df["date_utc"] = pd.to_datetime(df["date_utc"])
    df["outcome"] = df["success"].map({True: "Success", False: "Failure", None: "Unknown"})

    fig = px.scatter(
        df,
        x="date_utc",
        y="flight_number",
        color="outcome",
        hover_name="name",
        color_discrete_map={"Success": "#00b4d8", "Failure": "#e63946", "Unknown": "#adb5bd"},
        labels={"date_utc": "Date", "flight_number": "Flight Number"},
    )
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # --- Landing breakdown ---
    st.subheader("Landing Statistics")
    lc1, lc2 = st.columns(2)

    with lc1:
        landing_df = pd.DataFrame(
            {
                "Type": ["RTLS", "ASDS"],
                "Attempts": [stats["rtls_attempts"], stats["asds_attempts"]],
                "Successes": [stats["rtls_successes"], stats["asds_successes"]],
            }
        )
        fig2 = px.bar(
            landing_df.melt(id_vars="Type", var_name="Metric", value_name="Count"),
            x="Type", y="Count", color="Metric", barmode="group",
            color_discrete_map={"Attempts": "#adb5bd", "Successes": "#00b4d8"},
        )
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    with lc2:
        st.dataframe(
            df[["flight_number", "name", "date_utc", "outcome"]]
            .sort_values("flight_number", ascending=False)
            .head(20)
            .rename(columns={"flight_number": "Flight", "name": "Mission", "date_utc": "Date", "outcome": "Outcome"}),
            use_container_width=True,
        )


if __name__ == "__main__":
    main()

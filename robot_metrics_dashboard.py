"""
Robot Simulation Metrics Dashboard
----------------------------------
Run:
    pip install -r requirements_visualizer.txt
    streamlit run robot_metrics_dashboard.py

By default, the dashboard reads runs/1.txt (the CSV log created by the
robot simulation). You can also upload another exported CSV file.
"""

from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Robot Simulation Metrics",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Robot Simulation Metrics Dashboard")
st.caption("Explore proximity-sensor distances, detected object types, and light intensity.")

EXPECTED_COLUMNS = [
    "frame_count",
    "total_time",
    "average_sensor_distance",
    "average_robot_distance",
    "average_light_intensity",
    "sensor_type_robot",
    "sensor_type_obstacle",
    "sensor_type_wall",
    "sensor_type_none",
]

DEFAULT_FILE = Path("runs/1.txt")


@st.cache_data
def load_csv(file_bytes: bytes) -> pd.DataFrame:
    """Load and validate a simulation CSV log."""
    from io import BytesIO
    data = pd.read_csv(BytesIO(file_bytes))
    missing = [column for column in EXPECTED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    for column in EXPECTED_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(subset=["total_time"]).sort_values("total_time")
    if data.empty:
        raise ValueError("The CSV contains no usable simulation rows.")
    return data


uploaded_file = st.sidebar.file_uploader(
    "Upload a simulation CSV/TXT log",
    type=["csv", "txt"],
)

if uploaded_file is not None:
    source_name = uploaded_file.name
    raw_bytes = uploaded_file.getvalue()
elif DEFAULT_FILE.exists():
    source_name = str(DEFAULT_FILE)
    raw_bytes = DEFAULT_FILE.read_bytes()
    st.sidebar.success(f"Loaded {DEFAULT_FILE}")
else:
    st.info(
        "No log file found at `runs/1.txt`. Run the robot simulation first, "
        "or upload its exported CSV/TXT log using the sidebar."
    )
    st.stop()

try:
    df = load_csv(raw_bytes)
except Exception as exc:
    st.error(f"Could not read this metrics file: {exc}")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.subheader("Display range")
min_time = float(df["total_time"].min())
max_time = float(df["total_time"].max())
if min_time == max_time:
    start_time, end_time = min_time, max_time
else:
    selected_range = st.sidebar.slider(
        "Simulation time (seconds)",
        min_value=min_time,
        max_value=max_time,
        value=(min_time, max_time),
    )
    start_time, end_time = selected_range

view = df[df["total_time"].between(start_time, end_time)].copy()
if view.empty:
    st.warning("No rows fall inside the selected time range.")
    st.stop()

# Summary values are calculated over the selected time window.
mean_sensor = view["average_sensor_distance"].mean()
mean_robot = view["average_robot_distance"].mean()
mean_light = view["average_light_intensity"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Mean sensor distance", f"{mean_sensor:.2f} px")
k2.metric("Mean robot distance", f"{mean_robot:.2f} px")
k3.metric("Mean light intensity", f"{mean_light:.4f}")
k4.metric("Simulation duration", f"{view['total_time'].max() - view['total_time'].min():.2f} s")

st.markdown(f"**Source:** `{source_name}` · **Frames shown:** {len(view):,}")

st.subheader("1. Distance measurements")
distance_long = view.melt(
    id_vars=["total_time"],
    value_vars=["average_sensor_distance", "average_robot_distance"],
    var_name="Metric",
    value_name="Distance (pixels)",
)
distance_long["Metric"] = distance_long["Metric"].map({
    "average_sensor_distance": "All detected objects",
    "average_robot_distance": "Other robots only",
})
fig_distance = px.line(
    distance_long,
    x="total_time",
    y="Distance (pixels)",
    color="Metric",
    title="Average proximity-sensor distance over time",
    labels={"total_time": "Simulation time (s)"},
)
fig_distance.update_layout(hovermode="x unified")
st.plotly_chart(fig_distance, use_container_width=True)

st.subheader("2. Sensor object-type frequency")
frequency_columns = {
    "sensor_type_robot": "Robot",
    "sensor_type_obstacle": "Obstacle",
    "sensor_type_wall": "Wall",
    "sensor_type_none": "No detection",
}
frequency_total = {
    label: int(view[column].sum())
    for column, label in frequency_columns.items()
}
freq_df = pd.DataFrame({
    "Object type": list(frequency_total.keys()),
    "Sensor readings": list(frequency_total.values()),
})
left, right = st.columns(2)
with left:
    fig_frequency = px.bar(
        freq_df,
        x="Object type",
        y="Sensor readings",
        color="Object type",
        title="Total sensor readings by object type",
        text="Sensor readings",
    )
    st.plotly_chart(fig_frequency, use_container_width=True)
with right:
    fig_pie = px.pie(
        freq_df,
        names="Object type",
        values="Sensor readings",
        title="Share of sensor readings",
        hole=0.35,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("Sensor readings by object type over time")
time_frequency = view[["total_time", *frequency_columns.keys()]].rename(
    columns=frequency_columns
).melt(
    id_vars=["total_time"],
    var_name="Object type",
    value_name="Number of sensors",
)
fig_frequency_time = px.area(
    time_frequency,
    x="total_time",
    y="Number of sensors",
    color="Object type",
    title="Per-frame sensor type counts",
    labels={"total_time": "Simulation time (s)"},
)
fig_frequency_time.update_layout(hovermode="x unified")
st.plotly_chart(fig_frequency_time, use_container_width=True)

st.subheader("3. Average light intensity")
fig_light = px.line(
    view,
    x="total_time",
    y="average_light_intensity",
    title="Average light intensity across robots",
    labels={
        "total_time": "Simulation time (s)",
        "average_light_intensity": "Average light intensity",
    },
)
fig_light.update_layout(hovermode="x unified")
st.plotly_chart(fig_light, use_container_width=True)

with st.expander("View data table"):
    st.dataframe(view, use_container_width=True, hide_index=True)

st.subheader("Export")
summary_df = pd.DataFrame({
    "metric": [
        "mean_average_sensor_distance_px",
        "mean_average_robot_distance_px",
        "mean_average_light_intensity",
        *[f"total_{name.lower().replace(' ', '_')}_readings" for name in frequency_total],
    ],
    "value": [
        mean_sensor,
        mean_robot,
        mean_light,
        *frequency_total.values(),
    ],
})
c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "Download selected raw data (CSV)",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="robot_metrics_selected.csv",
        mime="text/csv",
        use_container_width=True,
    )
with c2:
    st.download_button(
        "Download summary metrics (CSV)",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name="robot_metrics_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

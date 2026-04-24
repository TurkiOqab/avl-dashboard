from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.charts import (
    top_vehicles_chart,
    trend_chart,
    type_breakdown_chart,
)
from src.queries import (
    get_kpis,
    get_raw,
    get_top_vehicles,
    get_trend,
    get_type_breakdown,
)
from src.storage import get_database


st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Dashboard")

db = get_database()

all_types = [r[0] for r in db.conn.execute(
    "SELECT DISTINCT vehicle_type FROM records ORDER BY vehicle_type"
).fetchall()]
all_plates = [r[0] for r in db.conn.execute(
    "SELECT DISTINCT plate_number FROM records ORDER BY plate_number"
).fetchall()]

if not all_types:
    st.info("No data yet. Upload a report on the Upload page first.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
with c1:
    start = st.date_input("From", value=date.today() - timedelta(days=30))
with c2:
    end = st.date_input("To", value=date.today())
with c3:
    types = st.multiselect("Vehicle type", all_types, default=all_types)
with c4:
    plates = st.multiselect("Plate", all_plates, default=[])

if start > end:
    st.error("'From' must be on or before 'To'.")
    st.stop()

filters = {
    "start_date": start,
    "end_date": end,
    "vehicle_types": types or None,
    "plate_numbers": plates or None,
}

kpis = get_kpis(db.conn, filters)
if kpis["total_visits"] == 0:
    st.warning("No records match the current filters. Widen the date range or clear the type/plate filters.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total visits", kpis["total_visits"])
k2.metric("Active vehicles", kpis["active_vehicles"])
k3.metric("Avg per vehicle", f"{kpis['avg_visits_per_vehicle']:.1f}")
k4.metric("Worst day", str(kpis["worst_day"] or "—"))

bucket = "week" if (end - start).days > 60 else "day"
st.plotly_chart(
    trend_chart(get_trend(db.conn, filters, bucket=bucket)),
    use_container_width=True,
)

left, right = st.columns([2, 1])
with left:
    st.plotly_chart(
        top_vehicles_chart(get_top_vehicles(db.conn, filters, limit=10)),
        use_container_width=True,
    )
with right:
    st.plotly_chart(
        type_breakdown_chart(get_type_breakdown(db.conn, filters)),
        use_container_width=True,
    )

st.subheader("Per-vehicle summary")
summary_df = pd.DataFrame(get_top_vehicles(db.conn, filters, limit=1000))
st.dataframe(summary_df, use_container_width=True)

st.subheader("Raw records")
raw_df = pd.DataFrame(get_raw(db.conn, filters))
st.dataframe(raw_df, use_container_width=True)
st.download_button(
    "Export CSV",
    data=raw_df.to_csv(index=False).encode(),
    file_name=f"avl-records-{start}-to-{end}.csv",
    mime="text/csv",
)

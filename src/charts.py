from collections import defaultdict

import plotly.graph_objects as go


def trend_chart(rows: list[dict]) -> go.Figure:
    by_type: dict[str, list[tuple]] = defaultdict(list)
    for r in rows:
        by_type[r["vehicle_type"]].append((r["date"], r["visits"]))

    fig = go.Figure()
    for vtype, points in by_type.items():
        points.sort()
        fig.add_trace(go.Scatter(
            x=[p[0] for p in points],
            y=[p[1] for p in points],
            mode="lines+markers",
            name=vtype,
            stackgroup="one",
        ))
    fig.update_layout(
        title="Off-route visits over time",
        xaxis_title="Date",
        yaxis_title="Visits",
    )
    return fig


def top_vehicles_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure(data=[go.Bar(
        x=[r["plate_number"] for r in rows],
        y=[r["total_visits"] for r in rows],
        text=[r["vehicle_type"] for r in rows],
    )])
    fig.update_layout(
        title="Top vehicles by off-route visits",
        xaxis_title="Plate",
        yaxis_title="Total visits",
    )
    return fig


def type_breakdown_chart(rows: list[dict]) -> go.Figure:
    fig = go.Figure(data=[go.Pie(
        labels=[r["vehicle_type"] for r in rows],
        values=[r["total_visits"] for r in rows],
        hole=0.4,
    )])
    fig.update_layout(title="Share of visits by vehicle type")
    return fig

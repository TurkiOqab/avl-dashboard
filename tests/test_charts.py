from datetime import date

from src.charts import (
    top_vehicles_chart,
    trend_chart,
    type_breakdown_chart,
)


def test_trend_chart_has_one_trace_per_type():
    data = [
        {"date": date(2026, 4, 21), "vehicle_type": "Sedan", "visits": 2},
        {"date": date(2026, 4, 22), "vehicle_type": "Sedan", "visits": 3},
        {"date": date(2026, 4, 21), "vehicle_type": "Van",   "visits": 5},
    ]
    fig = trend_chart(data)
    trace_names = {t.name for t in fig.data}
    assert trace_names == {"Sedan", "Van"}


def test_top_vehicles_chart_orders_bars_as_given():
    data = [
        {"plate_number": "A", "vehicle_type": "Sedan", "total_visits": 10, "last_seen": date(2026, 4, 22)},
        {"plate_number": "B", "vehicle_type": "Van",   "total_visits": 5,  "last_seen": date(2026, 4, 22)},
    ]
    fig = top_vehicles_chart(data)
    assert list(fig.data[0].x) == ["A", "B"]
    assert list(fig.data[0].y) == [10, 5]


def test_type_breakdown_chart_pie_values():
    data = [
        {"vehicle_type": "Sedan", "total_visits": 5},
        {"vehicle_type": "Van",   "total_visits": 6},
    ]
    fig = type_breakdown_chart(data)
    assert list(fig.data[0].labels) == ["Sedan", "Van"]
    assert list(fig.data[0].values) == [5, 6]

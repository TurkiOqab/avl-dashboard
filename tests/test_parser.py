from datetime import date

from src.parser import parse_report


def test_parse_report_extracts_all_rows(make_excel):
    rows = [
        {
            "vehicle_type": "Sedan",
            "plate_number": "ABC-1234",
            "record_date": date(2026, 4, 22),
            "visits_count": 3,
            "location_indices": "12, 13, 14",
        },
        {
            "vehicle_type": "Van",
            "plate_number": "XYZ-9999",
            "record_date": date(2026, 4, 22),
            "visits_count": 1,
            "location_indices": "7",
        },
    ]
    path = make_excel(rows)
    parsed = parse_report(path)

    assert parsed.report_date == date(2026, 4, 22)
    assert len(parsed.records) == 2
    assert parsed.records[0]["plate_number"] == "ABC-1234"
    assert parsed.records[0]["visits_count"] == 3
    assert parsed.records[0]["location_indices"] == "12, 13, 14"
    assert parsed.records[0]["record_date"] == date(2026, 4, 22)

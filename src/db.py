import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    report_date DATE NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,
    row_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    vehicle_type TEXT NOT NULL,
    plate_number TEXT NOT NULL,
    record_date DATE NOT NULL,
    visits_count INTEGER NOT NULL,
    location_indices TEXT,
    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_records_plate ON records(plate_number);
CREATE INDEX IF NOT EXISTS idx_records_date  ON records(record_date);
"""


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def init_schema(self) -> None:
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def import_report(
        self,
        filename: str,
        report_date,
        file_hash: str,
        records: list[dict],
    ) -> int:
        try:
            cur = self.conn.execute(
                """
                INSERT INTO reports (filename, report_date, file_hash, row_count)
                VALUES (?, ?, ?, ?)
                """,
                (filename, report_date.isoformat(), file_hash, len(records)),
            )
            report_id = cur.lastrowid
            self.conn.executemany(
                """
                INSERT INTO records (
                    report_id, vehicle_type, plate_number,
                    record_date, visits_count, location_indices
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        report_id,
                        r["vehicle_type"],
                        r["plate_number"],
                        r["record_date"].isoformat(),
                        r["visits_count"],
                        r.get("location_indices"),
                    )
                    for r in records
                ],
            )
            self.conn.commit()
            return report_id
        except Exception:
            self.conn.rollback()
            raise

    def find_report_by_hash(self, file_hash: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM reports WHERE file_hash = ?", (file_hash,)
        ).fetchone()

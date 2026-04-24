import hashlib
import sqlite3
from io import BytesIO

import pandas as pd
import streamlit as st

from src.parser import parse_report
from src.storage import get_database


st.set_page_config(page_title="Upload", layout="wide")
st.title("Upload a daily report")

uploaded = st.file_uploader(
    "Drop an Excel (.xlsx) report here",
    type=["xlsx"],
    accept_multiple_files=False,
)

if uploaded is not None:
    raw = uploaded.getvalue()
    file_hash = hashlib.sha256(raw).hexdigest()

    db = get_database()
    existing = db.find_report_by_hash(file_hash)
    if existing is not None:
        st.warning(
            f"Already imported on {existing['uploaded_at']} as "
            f"`{existing['filename']}`."
        )
        st.stop()

    try:
        parsed = parse_report(BytesIO(raw))
    except Exception as exc:
        st.error(f"Could not parse this file: {exc}")
        st.stop()

    st.success(
        f"Parsed **{len(parsed.records)}** rows "
        f"(report date: **{parsed.report_date}**)."
    )
    df = pd.DataFrame(parsed.records)
    st.dataframe(df, use_container_width=True)

    if st.button("Save to database", type="primary"):
        try:
            db.import_report(
                filename=uploaded.name,
                report_date=parsed.report_date,
                file_hash=file_hash,
                records=parsed.records,
            )
            st.success("Saved. Go to the Dashboard to view it.")
        except sqlite3.IntegrityError:
            st.error("This file was imported between page loads. Refresh.")

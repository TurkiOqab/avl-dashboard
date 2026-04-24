import hashlib
import sqlite3
from io import BytesIO

import pandas as pd
import streamlit as st

from src.parser import ParsedReport, parse_report
from src.storage import get_database


st.set_page_config(page_title="Upload", layout="wide")
st.title("Upload a daily report")


@st.cache_data(show_spinner=False)
def _hash_and_parse(raw: bytes) -> tuple[str, ParsedReport]:
    """Hash and parse once per unique file. Streamlit reruns the script on
    every widget interaction; without this cache, SHA-256 and openpyxl
    would both run each time the user even looks at the page."""
    file_hash = hashlib.sha256(raw).hexdigest()
    parsed = parse_report(BytesIO(raw))
    return file_hash, parsed


# Files saved during this session, so re-renders after a successful save
# show a clean success state instead of the "already imported" warning.
if "saved_hashes" not in st.session_state:
    st.session_state.saved_hashes = set()

uploaded = st.file_uploader(
    "Drop an Excel (.xlsx) report here",
    type=["xlsx"],
    accept_multiple_files=False,
)

if uploaded is not None:
    raw = uploaded.getvalue()

    try:
        file_hash, parsed = _hash_and_parse(raw)
    except Exception as exc:
        st.error(f"Could not parse this file: {exc}")
        st.stop()

    if file_hash in st.session_state.saved_hashes:
        st.success(
            "Saved. Drop another file, or open the Dashboard from the sidebar."
        )
        st.stop()

    db = get_database()
    existing = db.find_report_by_hash(file_hash)
    if existing is not None:
        st.warning(
            f"Already imported on {existing['uploaded_at']} as "
            f"`{existing['filename']}`."
        )
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
            st.session_state.saved_hashes.add(file_hash)
            st.success("Saved. Go to the Dashboard to view it.")
        except sqlite3.IntegrityError:
            st.error("This file was imported between page loads. Refresh.")

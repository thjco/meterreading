import streamlit as st
from datetime import datetime
from meterreading_tools import *


st.set_page_config(page_title="Meter Reading", initial_sidebar_state="collapsed")
st.title("Zählerstände")

with st.sidebar:
    if st.button("Daten löschen"):
        drop_tables()

    if st.button("Beispieldaten"):
        set_example_data()

conn = create_connection(DB_FILE)
ensure_tables(conn)

entries = select_all_entries(conn)

tab_entry, tab_analysis, tab_data = st.tabs(["Eingabe", "Auswertung", "Daten"])

with tab_entry:
    with st.form("input"):
        now = datetime.today()

        r_date = st.date_input("Datum", value=now.date()) # value="2022/10/02") #
        r_time = st.time_input("Uhrzeit", value=now.time())

        gas = st.number_input("Gas", min_value=0., step=0.001, value=0.0, format="%.3f")

        submitted = st.form_submit_button("Speichern")


with tab_data:
    st.dataframe(entries)

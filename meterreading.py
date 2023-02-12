import streamlit as st
import matplotlib.pyplot as plt
import json
from datetime import datetime
from meterreading_tools import *
from io import StringIO


st.set_page_config(page_title="Meter Reading", initial_sidebar_state="collapsed")
st.title("Zählerstände")

conn = create_connection(DB_FILE)
ensure_tables(conn)

entries = select_all_entries(conn)

with st.sidebar:
    if st.button("Daten löschen"):
        drop_tables()
        entries = []

    if st.button("Beispieldaten verwenden"):
        set_example_data()
        entries = select_all_entries(conn)

    download_json = entries.to_json(orient="records") if len(entries) else "[]"
    download_filename = (
        f"meterreading-{datetime.today().strftime('%Y%m%d-%H%M%S')}.json"
    )
    st.download_button(
        "Daten exportieren", data=download_json, file_name=download_filename
    )

    uploaded_file = st.file_uploader("Daten importieren")
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        string_data = stringio.read()
        #TODO finalize import
        e = json.loads(string_data)
        #e = pd.DataFrame(e)
        st.write(type(entries))

tab_entry, tab_analysis, tab_data = st.tabs(["Eingabe", "Auswertung", "Daten"])

with tab_entry:
    with st.form("input"):
        now = datetime.today()

        r_date = st.date_input("Datum", value=now.date())  # value="2022/10/02") #
        r_time = st.time_input("Uhrzeit", value=now.time())

        gas = st.number_input(
            "Gas", min_value=0.0, step=0.001, value=0.0, format="%.3f"
        )
        water = st.number_input(
            "Water", min_value=0.0, step=0.001, value=0.0, format="%.3f"
        )
        electricity = st.number_input(
            "Electricity", min_value=0.0, step=0.1, value=0.0, format="%.1f"
        )

        submitted = st.form_submit_button("Speichern")

    if submitted:
        # TODO Close connection at this point?
        r_datetime = datetime.combine(r_date, r_time)
        r_datetime = int(r_datetime.timestamp() * 1000)
        data = {
            "rdate": r_datetime,
            "gas": gas,
            "water": water,
            "electricity": electricity,
        }
        df = pd.DataFrame([data])
        create_entry(conn, df.iloc[0])
        entries = select_all_entries(conn)

with tab_analysis:
    years = sorted(set(entries.year.to_list()))
    last_year = years[-1]
    idx = years.index(last_year)
    selected_year = st.selectbox("Jahr", years, index=idx)

    for conf in COUNT_UP_DEVICES_CONFIGURATION:
        device = CountUpDevice(
            conf["name"], conf["column"], conf["unit"], conf["lightColor"], conf["darkColor"]
        )
        device.set_values(entries)
        if device.has_per_day_values():
            fig = device.get_per_day_fig()
            st.pyplot(fig)
            fig = device.get_per_day_of_year_fig(selected_year)
            st.pyplot(fig)
        if device.has_per_year_values():
            fig = device.get_per_year_fig()
            st.pyplot(fig)

with tab_data:
    st.dataframe(entries[::-1])

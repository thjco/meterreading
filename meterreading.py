import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from meterreading_tools import *


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

    download_json = entries.to_json( orient="records") if len(entries) else "[]"
    download_filename = f"meterreading-{datetime.today().strftime('%Y%m%d-%H%M%S')}.json"
    st.download_button("Daten exportieren", data=download_json, file_name=download_filename)

tab_entry, tab_analysis, tab_data = st.tabs(["Eingabe", "Auswertung", "Daten"])

with tab_entry:
    with st.form("input"):
        now = datetime.today()

        r_date = st.date_input("Datum", value=now.date()) # value="2022/10/02") #
        r_time = st.time_input("Uhrzeit", value=now.time())

        gas = st.number_input("Gas", min_value=0., step=0.001, value=0.0, format="%.3f")
        water = st.number_input("Water", min_value=0., step=0.001, value=0.0, format="%.3f")
        electricity = st.number_input("Electricity", min_value=0., step=0.1, value=0.0, format="%.1f")

        submitted = st.form_submit_button("Speichern")

    if submitted:
        # TODO Close connection at this point?
        r_datetime = datetime.combine(r_date, r_time)
        r_datetime = int(r_datetime.timestamp() * 1000)
        data = { "rdate": r_datetime, "gas": gas, "water": water, "electricity": electricity}
        df = pd.DataFrame([data])
        create_entry(conn, df.iloc[0])
        entries = select_all_entries(conn)

with tab_analysis:
    years = sorted(set(entries.year.to_list()))
    last_year = years[-1]
    idx = years.index(last_year)
    selected_year = st.selectbox("Jahr", years, index=idx)

    gas_device = CountUpDevice("Gas", "gas", "m³", "Red")
    gas_device.set_values(entries)
    if gas_device.has_per_day_values():
        fig = gas_device.get_per_day_fig()
        st.pyplot(fig)
        fig = gas_device.get_per_day_of_year_fig(selected_year)
        st.pyplot(fig)
    if gas_device.has_per_year_values():
        fig = gas_device.get_per_year_fig()
        st.pyplot(fig)

    water_device = CountUpDevice("Water", "water", "m³", "Blue")
    water_device.set_values(entries)
    if water_device.has_per_day_values():
        fig = water_device.get_per_day_fig()
        st.pyplot(fig)
        fig = water_device.get_per_day_of_year_fig(selected_year)
        st.pyplot(fig)
    if water_device.has_per_year_values():
        fig = water_device.get_per_year_fig()
        st.pyplot(fig)

    electricity_device = CountUpDevice("Electricity", "electricity", "kWh", "Green")
    electricity_device.set_values(entries)
    if water_device.has_per_day_values():
        fig = electricity_device.get_per_day_fig()
        st.pyplot(fig)
        fig = electricity_device.get_per_day_of_year_fig(selected_year)
        st.pyplot(fig)
    if electricity_device.has_per_year_values():
        fig = electricity_device.get_per_year_fig()
        st.pyplot(fig)


with tab_data:
    st.dataframe(entries[::-1])

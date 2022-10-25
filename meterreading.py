import streamlit as st
import matplotlib.pyplot as plt
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

with tab_analysis:
    gas_per_day = entries.dropna().copy()
    gas_per_day["d_gas"] = (gas_per_day.gas - gas_per_day.gas.shift())
    gas_per_day["gas_per_day"] = gas_per_day.d_gas / gas_per_day.days
    gas_per_day = gas_per_day.query("gas_per_day > 0").copy()

    if gas_per_day.shape[0] > 0:
        fig, ax = plt.subplots()
        #ax.plot(consumption["consumption"], label="Verbrauch", color="b", marker="o", linewidth=2, markersize=6)
        plt.plot_date(gas_per_day["datetime"], gas_per_day["gas_per_day"], fmt="-");
        plt.legend()
        st.pyplot(fig)

        years = sorted(set(gas_per_day.year.to_list()))
        fig, ax = plt.subplots()
        ax.set_xticks(list(range(13)))
        for year in years[:-1]:
            y = gas_per_day.query(f"year == {year}")
            plt.plot(y["m_of_year"], y["gas_per_day"], c="LightGrey")
        y = gas_per_day.query(f"year == {years[-1]}")
        plt.plot(y["m_of_year"], y["gas_per_day"], c="Blue")
        plt.grid()
        st.pyplot(fig)

with tab_data:
    st.dataframe(entries)

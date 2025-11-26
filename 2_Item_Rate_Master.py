# pages/2_Item_Rate_Master.py
import streamlit as st
import pandas as pd
from db import get_conn, get_party_list, init_db

init_db()
st.title("📦 Item & Rate Master")

tab1, tab2 = st.tabs(["Item Master", "Rate Master"])

with tab1:
    st.subheader("Item / Goods Type Master (Optional)")
    with st.form("item_form"):
        item_name = st.text_input("Item Name")
        desc = st.text_input("Description (optional)")
        submitted = st.form_submit_button("💾 Save Item")
        if submitted:
            if not item_name.strip():
                st.error("Item Name required.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR IGNORE INTO item_master (item_name, description)
                    VALUES (?, ?)
                """, (item_name, desc))
                conn.commit()
                conn.close()
                st.success("Item saved ✅")

    conn = get_conn()
    df_items = pd.read_sql_query("SELECT item_name, description FROM item_master ORDER BY item_name", conn)
    conn.close()
    st.dataframe(df_items, use_container_width=True)

with tab2:
    st.subheader("Rate Master (Party + Route Wise)")

    parties = get_party_list()
    party_map = {p[1]: p[0] for p in parties}
    party_name = st.selectbox("Party (optional, blank = general)", [""] + list(party_map.keys()))
    from_city = st.text_input("From City (e.g., DELHI)")
    to_city = st.text_input("To City (e.g., MUMBAI)")
    rate_type = st.selectbox("Rate Type", ["KG", "PARCEL"])
    rate_val = st.number_input("Rate", min_value=0.0, step=1.0)

    if st.button("💾 Save Rate"):
        if not from_city.strip() or not to_city.strip():
            st.error("From और To दोनों ज़रूरी हैं।")
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO rate_master (party_id, from_city, to_city, rate_type, rate)
                VALUES (?, ?, ?, ?, ?)
            """, (
                party_map.get(party_name) if party_name else None,
                from_city.upper().strip(),
                to_city.upper().strip(),
                rate_type,
                rate_val
            ))
            conn.commit()
            conn.close()
            st.success("Rate saved ✅")

    conn = get_conn()
    df_rates = pd.read_sql_query("""
        SELECT
          COALESCE((SELECT party_name FROM party_master p WHERE p.id = r.party_id), 'ALL') AS party,
          from_city, to_city, rate_type, rate
        FROM rate_master r
        ORDER BY party, from_city, to_city
    """, conn)
    conn.close()
    st.dataframe(df_rates, use_container_width=True)

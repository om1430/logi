# pages/1_Party_Master.py
import streamlit as st
import pandas as pd
from db import get_conn, init_db

init_db()
st.title("👥 Party Master (Party Register)")

st.info("यहाँ से Party add/update करें। नीचे simple form है।")

with st.form("party_form"):
    party_name = st.text_input("Party Name *")
    address = st.text_area("Address")
    mobile = st.text_input("Mobile Number")
    gst_no = st.text_input("GST No. (optional)")
    marka = st.text_input("Marka / Sign")
    default_rate_per_kg = st.number_input("Default Rate per Kg (optional)", min_value=0.0, step=1.0)
    default_rate_per_parcel = st.number_input("Default Rate per Parcel (optional)", min_value=0.0, step=1.0)
    submitted = st.form_submit_button("💾 Save Party")

    if submitted:
        if not party_name.strip():
            st.error("Party Name ज़रूरी है।")
        else:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO party_master
                (id, party_name, address, mobile, gst_no, marka,
                 default_rate_per_kg, default_rate_per_parcel)
                VALUES (
                    COALESCE((SELECT id FROM party_master WHERE party_name = ?), NULL),
                    ?,?,?,?,?,?,?
                )
            """, (party_name, party_name, address, mobile, gst_no, marka,
                  default_rate_per_kg, default_rate_per_parcel))
            conn.commit()
            conn.close()
            st.success("Party saved successfully ✅")

st.markdown("---")
st.subheader("📋 Party List")

conn = get_conn()
df = pd.read_sql_query("SELECT party_name, mobile, gst_no, marka, default_rate_per_kg, default_rate_per_parcel FROM party_master ORDER BY party_name", conn)
conn.close()

st.dataframe(df, use_container_width=True)

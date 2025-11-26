# pages/5_Payments.py
import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_conn, get_party_list, compute_party_balance, init_db

init_db()
st.title("💰 Payment Entry (Cash / Bank)")

parties = get_party_list()
if not parties:
    st.warning("पहले Party Master में Party बनाओ।")
    st.stop()

party_map = {p[1]: p[0] for p in parties}
party_name = st.selectbox("Party चुनें", list(party_map.keys()))
party_id = party_map[party_name]

current_bal = compute_party_balance(party_id)
st.info(f"Approx Current Balance (Approx): ₹ {current_bal:.2f}")

with st.form("payment_form"):
    date_str = st.text_input("Date", value=datetime.now().strftime("%d/%m/%Y"))
    amount = st.number_input("Amount", min_value=0.0, step=500.0)
    mode = st.selectbox("Payment Type", ["CASH", "BANK", "UPI", "CHEQUE"])
    remark = st.text_input("Remark (optional)")
    submitted = st.form_submit_button("💾 Save Payment")

    if submitted:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO payments (party_id, date, amount, mode, remark)
            VALUES (?,?,?,?,?)
        """, (party_id, date_str, amount, mode, remark))
        conn.commit()
        conn.close()
        st.success("Payment saved ✅")

st.markdown("---")
st.subheader("Recent Payments")

conn = get_conn()
df = pd.read_sql_query("""
    SELECT date, amount, mode, remark
    FROM payments
    WHERE party_id=?
    ORDER BY id DESC LIMIT 50
""", conn, params=(party_id,))
conn.close()
st.dataframe(df, use_container_width=True)

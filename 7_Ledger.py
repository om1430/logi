# pages/7_Ledger.py

import streamlit as st
import pandas as pd
from datetime import date
from db import get_conn, init_db
from utils.pdf_utils import ledger_pdf
import io

init_db()

st.title("📚 Party Ledger")

conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT id, party_name FROM party_master ORDER BY party_name")
parties = cur.fetchall()
conn.close()

if not parties:
    st.error("❌ Add Party first.")
    st.stop()

party_map = {p[1]: p[0] for p in parties}
party_name = st.selectbox("Select Party", list(party_map.keys()))
party_id = party_map[party_name]

opening_balance = st.number_input("Opening Balance (₹)", value=0.0, step=100.0)

col1, col2 = st.columns(2)
with col1:
    start_dt = st.date_input("From Date", date.today().replace(day=1))
with col2:
    end_dt = st.date_input("To Date", date.today())

if start_dt > end_dt:
    st.error("❌ From Date cannot be after To Date.")
    st.stop()

if st.button("📄 Show Ledger", type="primary"):
    conn = get_conn()

    tokens = pd.read_sql_query("""
        SELECT 
            t.datetime,
            t.id AS token_no,
            t.amount
        FROM tokens t
        WHERE t.party_id = ?
        ORDER BY t.datetime
    """, conn, params=(party_id,))

    payments = pd.read_sql_query("""
        SELECT date, amount, mode, remark
        FROM payments
        WHERE party_id = ?
        ORDER BY date
    """, conn, params=(party_id,))

    conn.close()

    rows = []

    # Token parsing
    if not tokens.empty:
        tokens["dt"] = pd.to_datetime(tokens["datetime"], format="%d-%m-%Y %I:%M %p", errors="coerce")
        tokens = tokens[tokens["dt"].notna()]
        tokens["d"] = tokens["dt"].dt.date
        tokens = tokens[(tokens["d"] >= start_dt) & (tokens["d"] <= end_dt)]
        for _, r in tokens.iterrows():
            rows.append({
                "date": r["d"].strftime("%d-%m-%Y"),
                "type": "TOKEN",
                "details": f"Token #{r['token_no']}",
                "debit": r["amount"],
                "credit": 0,
            })

    # Payment parsing
    if not payments.empty:
        payments["dt"] = pd.to_datetime(payments["date"], errors="coerce", dayfirst=True)
        payments = payments[payments["dt"].notna()]
        payments["d"] = payments["dt"].dt.date
        payments = payments[(payments["d"] >= start_dt) & (payments["d"] <= end_dt)]
        for _, r in payments.iterrows():
            desc = f"Payment ({r['mode']})"
            if r["remark"]:
                desc += f" - {r['remark']}"
            rows.append({
                "date": r["d"].strftime("%d-%m-%Y"),
                "type": "PAYMENT",
                "details": desc,
                "debit": 0,
                "credit": r["amount"],
            })

    if not rows:
        st.warning("No transactions.")
        st.stop()

    ledger_df = pd.DataFrame(rows)
    ledger_df["date_sort"] = pd.to_datetime(ledger_df["date"], dayfirst=True)
    ledger_df.sort_values("date_sort", inplace=True)

    balance = opening_balance
    balances = []
    for _, r in ledger_df.iterrows():
        balance += r["debit"] - r["credit"]
        balances.append(balance)

    ledger_df["balance"] = balances
    ledger_df.drop(columns=["date_sort"], inplace=True)

    st.dataframe(ledger_df, width="stretch")

    # PDF
    header = {
        "party_name": party_name,
        "from_date": start_dt.strftime("%d-%m-%Y"),
        "to_date": end_dt.strftime("%d-%m-%Y"),
        "opening_balance": opening_balance,
        "closing_balance": float(balance)
    }

    pdf_buf = ledger_pdf(header, ledger_df.to_dict(orient="records"))

    st.download_button(
        "⬇️ Download Ledger PDF",
        data=pdf_buf,
        file_name=f"Ledger_{party_name.replace(' ','_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # Excel
    excel_buf = io.BytesIO()
    ledger_df.to_excel(excel_buf, index=False, engine="openpyxl")
    excel_buf.seek(0)

    st.download_button(
        "⬇️ Download Excel",
        data=excel_buf,
        file_name=f"Ledger_{party_name.replace(' ','_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

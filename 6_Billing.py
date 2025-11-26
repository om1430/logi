# pages/6_Billing.py

import streamlit as st
import pandas as pd
from datetime import date
from db import get_conn, init_db
from utils.pdf_utils import bill_pdf
import io

init_db()

st.title("🧾 Billing (Party-wise)")
st.info("किसी party के लिए date range चुनकर Bill बना सकते हैं।")

# -------------------------
#  LOAD PARTIES
# -------------------------
conn = get_conn()
cur = conn.cursor()
cur.execute("SELECT id, party_name FROM party_master ORDER BY party_name")
parties = cur.fetchall()
conn.close()

if not parties:
    st.error("❌ No parties found. Add parties first.")
    st.stop()

party_map = {p[1]: p[0] for p in parties}
party_name = st.selectbox("Select Party", list(party_map.keys()))
party_id = party_map[party_name]

# -------------------------
#   DATE RANGE + OLD BAL
# -------------------------
col1, col2 = st.columns(2)
with col1:
    start_dt = st.date_input("From Date", date.today().replace(day=1))
with col2:
    end_dt = st.date_input("To Date", date.today())

old_balance = st.number_input("Old Balance (₹)", value=0.0, step=100.0)

if start_dt > end_dt:
    st.error("❌ From Date cannot be greater than To Date.")
    st.stop()


# -------------------------
#     SHOW BILL BUTTON
# -------------------------
if st.button("🔍 Show Bill", type="primary"):

    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT 
            t.id AS token_no,
            t.datetime,
            t.weight,
            t.packages,
            t.amount,
            t.from_city,
            t.to_city
        FROM tokens t
        WHERE t.party_id = ?
          AND t.status IN ('PENDING', 'LOADED')
        ORDER BY t.datetime
    """, conn, params=(party_id,))
    conn.close()

    if df.empty:
        st.warning("No records for this party.")
        st.stop()

    # -------------------------
    #  PARSE DATE
    # -------------------------
    df["dt"] = pd.to_datetime(df["datetime"], format="%d-%m-%Y %I:%M %p", errors="coerce")
    df = df[df["dt"].notna()].copy()
    df["d"] = df["dt"].dt.date

    # filter range
    mask = (df["d"] >= start_dt) & (df["d"] <= end_dt)
    df = df[mask]

    if df.empty:
        st.warning("No records in this date range.")
        st.stop()

    # -------------------------
    #  SHOW TABLE ON SCREEN
    # -------------------------
    df_show = df[[
        "token_no", "datetime", "from_city", "to_city",
        "weight", "packages", "amount"
    ]]

    st.dataframe(df_show, width="stretch")

    total_weight = df["weight"].sum()
    total_pack = df["packages"].sum()
    total_amt = df["amount"].sum()

    st.subheader("📌 Totals")
    st.write(f"**Total Weight:** {total_weight}")
    st.write(f"**Total Packages:** {total_pack}")
    st.write(f"**Total Amount:** ₹{total_amt}")

    # -------------------------
    #  PREPARE PDF DATA
    # -------------------------
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "token_no": r["token_no"],
            "datetime": r["datetime"],
            "from_city": r["from_city"],
            "to_city": r["to_city"],
            "weight": r["weight"],
            "packages": r["packages"],
            "amount": r["amount"],
        })

    header = {
        "party_name": party_name,
        "from_date": start_dt.strftime("%d-%m-%Y"),
        "to_date": end_dt.strftime("%d-%m-%Y"),
        "total_weight": total_weight,
        "total_pkgs": total_pack,
        "total_amount": total_amt,
        "old_balance": old_balance,
    }

    # -------------------------
    #   PDF GENERATION
    # -------------------------
    pdf_buf = bill_pdf(header, rows)

    st.download_button(
        "⬇️ Download Bill PDF",
        data=pdf_buf,
        file_name=f"BILL_{party_name.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    # -------------------------
    #   EXCEL EXPORT
    # -------------------------
    excel_buf = io.BytesIO()
    df_show.to_excel(excel_buf, index=False, engine="openpyxl")
    excel_buf.seek(0)

    st.download_button(
        "⬇️ Download Excel",
        data=excel_buf,
        file_name=f"BILL_{party_name.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

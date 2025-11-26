# pages/4_Challan_Loading.py

import streamlit as st
import pandas as pd
from datetime import datetime
from db import get_conn, get_next_challan_no, init_db
from utils.pdf_utils import challan_pdf

# Initialise DB (tables already exist as per your schema)
init_db()

st.title("🚛 Challan / Loading")
st.info("Truck में माल load करते समय यहाँ से Challan बनाओ। Pending tokens select करके एक challan बनता है।")

# --------------------- FETCH PENDING TOKENS --------------------- #

conn = get_conn()

df_pending = pd.read_sql_query("""
    SELECT 
        t.id AS token_no,
        t.datetime,
        p.party_name,
        t.weight,
        t.amount,
        t.from_city,
        t.to_city
    FROM tokens t
    LEFT JOIN party_master p ON p.id = t.party_id
    WHERE t.status = 'PENDING'
    ORDER BY t.datetime
""", conn)

conn.close()

if df_pending.empty:
    st.warning("अभी कोई pending token नहीं है (सब load हो गए हैं या अभी token बनाए नहीं हैं)।")
    st.stop()

# --------------------- TOKEN SELECTION TABLE --------------------- #

st.subheader("Select Tokens for Challan (Loading)")
st.caption("नीचे list में से वही tokens चुनो जो एक ही truck में जा रहे हैं।")

# Add a selection column
df_pending["select"] = False

# Use new Streamlit API: width='stretch' (no use_container_width warning)
selected = st.data_editor(
    df_pending,
    width="stretch",
    num_rows="fixed",
    hide_index=True,
)

# User-selected token_nos
selected_token_nos = selected[selected["select"]]["token_no"].tolist()

if not selected_token_nos:
    st.info("कम से कम 1 token select करो।")
    st.stop()

# Pre-fill from/to using first selected row
first_row = selected[selected["select"]].iloc[0]
from_city_auto = first_row["from_city"]
to_city_auto = first_row["to_city"]

st.markdown("---")

# --------------------- CHALLAN DETAILS FORM --------------------- #

st.subheader("Challan Details")

challan_no = get_next_challan_no()
st.text_input("Challan No (Auto)", value=str(challan_no), disabled=True)

today_str = datetime.now().strftime("%d/%m/%Y")
date_str = st.text_input("Challan Date", value=today_str)

col1, col2 = st.columns(2)
with col1:
    from_city = st.text_input("From City", value=from_city_auto)
    truck_no = st.text_input("Truck No.")
with col2:
    to_city = st.text_input("To City", value=to_city_auto)
    driver_name = st.text_input("Driver Name")

col3, col4 = st.columns(2)
with col3:
    driver_mobile = st.text_input("Driver Mobile")
    hire = st.number_input("Gadi Bhadha (Hire)", min_value=0.0, step=500.0, value=0.0)
with col4:
    loading_hamali = st.number_input("Loading Hamali", min_value=0.0, step=100.0, value=0.0)
    unloading_hamali = st.number_input("Unloading Hamali", min_value=0.0, step=100.0, value=0.0)

other_exp = st.number_input("Other Expenses", min_value=0.0, step=100.0, value=0.0)

# --------------------- CREATE CHALLAN & PDF --------------------- #

if st.button("✅ Create Challan & Download PDF", type="primary"):
    conn = get_conn()
    cur = conn.cursor()

    # Totals from selected tokens
    q_marks = ",".join("?" * len(selected_token_nos))

    cur.execute(
        f"SELECT SUM(amount), SUM(weight) FROM tokens WHERE id IN ({q_marks})",
        selected_token_nos
    )
    tot_amt, tot_wt = cur.fetchone()
    tot_amt = tot_amt or 0.0
    tot_wt = tot_wt or 0.0

    total_hamali = loading_hamali + unloading_hamali
    balance = tot_amt - hire - total_hamali - other_exp

    # Insert challan master
    cur.execute("""
        INSERT INTO challan (
            challan_no, date, from_city, to_city,
            truck_no, driver_name, driver_mobile,
            hire, loading_hamali, unloading_hamali,
            other_exp, balance
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        challan_no, date_str, from_city, to_city,
        truck_no, driver_name, driver_mobile,
        hire, loading_hamali, unloading_hamali,
        other_exp, balance
    ))
    challan_id = cur.lastrowid

    # Link each token -> challan + mark token as LOADED
    for tid in selected_token_nos:
        cur.execute(
            "INSERT INTO challan_tokens (challan_id, token_id) VALUES (?, ?)",
            (challan_id, tid)
        )
        cur.execute(
            "UPDATE tokens SET status='LOADED' WHERE id=?",
            (tid,)
        )

    # Get data for PDF rows (token_no, weight, amount, party_name)
    cur.execute(f"""
        SELECT 
            t.id AS token_no,
            t.weight,
            t.amount,
            p.party_name
        FROM tokens t
        LEFT JOIN party_master p ON p.id = t.party_id
        WHERE t.id IN ({q_marks})
    """, selected_token_nos)

    rows_db = cur.fetchall()
    conn.commit()
    conn.close()

    # Prepare rows in the format challan_pdf expects
    rows = []
    for r in rows_db:
        rows.append(
            {
                "token_no": r[0],
                "weight": r[1] or 0,
                "amount": r[2] or 0,
                "party_name": r[3] or "",
            }
        )

    challan_data = {
        "challan_no": challan_no,
        "date": date_str,
        "from_city": from_city,
        "to_city": to_city,
        "truck_no": truck_no,
        "driver_name": driver_name,
        "driver_mobile": driver_mobile,
        "hire": hire,
        "loading_hamali": loading_hamali,
        "unloading_hamali": unloading_hamali,
        "other_exp": other_exp,
        "balance": balance,
    }

    # Generate PDF with your existing layout function
    pdf_buf = challan_pdf(challan_data, rows)

    st.success(f"✅ Challan {challan_no} तैयार हो गया!")

    st.download_button(
        "⬇️ Download Challan PDF",
        data=pdf_buf,
        file_name=f"CHALLAN_{challan_no}.pdf",
        mime="application/pdf",
        width="stretch",
    )

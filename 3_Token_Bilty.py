import streamlit as st
import sqlite3
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# ============================================================
# DATABASE CONNECTION
# ============================================================
def get_conn():
    return sqlite3.connect("tms.db", check_same_thread=False)

conn = get_conn()
cur = conn.cursor()

# Create Token Table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS tokens(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT,
    party_id INTEGER,
    party_name TEXT,
    marka TEXT,
    from_city TEXT,
    to_city TEXT,
    weight REAL,
    rate REAL,
    amount REAL,
    packages INTEGER,
    driver_mobile TEXT,
    status TEXT DEFAULT 'PENDING'
)
""")
conn.commit()

# ============================================================
# FETCH PARTY LIST
# ============================================================
def get_parties():
    try:
        cur.execute("SELECT id, party_name, marka FROM party_master ORDER BY party_name")
        return cur.fetchall()
    except:
        st.error("❌ party_master table missing or incorrect structure.")
        return []

# ============================================================
# PDF GENERATOR
# ============================================================
def generate_token_pdf(token):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 800, "TOKEN / BILTY")

    c.setFont("Helvetica", 12)
    y = 770

    lines = [
        f"Token No: {token['id']}",
        f"Date/Time: {token['datetime']}",
        f"Party: {token['party_name']}",
        f"Marka: {token['marka']}",
        f"From: {token['from_city']}",
        f"To: {token['to_city']}",
        f"Weight (KG): {token['weight']}",
        f"Rate: {token['rate']}",
        f"Amount: {token['amount']}",
        f"Packages: {token['packages']}",
        f"Driver Mobile: {token['driver_mobile']}"
    ]

    for line in lines:
        c.drawString(50, y, line)
        y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(200, y - 20, "Thank You")

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"TOKEN_{token['id']}.pdf"
    return buffer, filename

# ============================================================
# PAGE UI
# ============================================================
st.title("📄 Token / Bilty Generation")
st.info("यहाँ से आप आसानी से Token (Bilty) बना सकते हैं। सभी चीज़ें auto-fill होंगी।")

# Fetch party list
parties = get_parties()
party_names = [p[1] for p in parties] if parties else []

if not parties:
    st.error("❌ No parties found in Party Master. Please add parties first.")
    st.stop()

# ============================================================
# FORM STARTS
# ============================================================
with st.form("token_form"):

    col1, col2 = st.columns(2)

    with col1:
        party_name = st.selectbox("Party Name", party_names)
        weight = st.number_input("Weight (KG)", 0.0)
        rate = st.number_input("Rate per KG", 0.0)
        packages = st.number_input("Packages", 1, step=1)

    with col2:
        from_city = st.selectbox("From City", ["DELHI", "MUMBAI"])
        to_city = st.selectbox("To City", ["DELHI", "MUMBAI"])
        driver_mobile = st.text_input("Driver Mobile (Optional)")

    # Autofill Marka
    marka = ""
    for p in parties:
        if p[1] == party_name:
            marka = p[2] if p[2] else ""
            break

    st.text_input("Marka / Sign", value=marka, key="marka_input")

    # Button inside form
    submitted = st.form_submit_button("➕ Generate Token")

# ============================================================
# AFTER SUBMIT - OUTSIDE FORM
# ============================================================
if submitted:

    amount = weight * rate
    timestamp = datetime.now().strftime("%d-%m-%Y %I:%M %p")

    # INSERT TOKEN INTO DB
    cur.execute("""
        INSERT INTO tokens(datetime, party_id, party_name, marka, from_city, to_city,
                           weight, rate, amount, packages, driver_mobile)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, (
        timestamp,
        next(p[0] for p in parties if p[1] == party_name),
        party_name, marka, from_city, to_city,
        weight, rate, amount, packages, driver_mobile
    ))
    conn.commit()

    token_id = cur.lastrowid

    token_data = {
        "id": token_id,
        "datetime": timestamp,
        "party_name": party_name,
        "marka": marka,
        "from_city": from_city,
        "to_city": to_city,
        "weight": weight,
        "rate": rate,
        "amount": amount,
        "packages": packages,
        "driver_mobile": driver_mobile
    }

    st.success(f"✅ Token Created Successfully! Token No: {token_id}")

    # Generate PDF
    pdf_buffer, filename = generate_token_pdf(token_data)

    # Download button (OUTSIDE FORM)
    st.download_button(
        label="📥 Download Token PDF",
        data=pdf_buffer,
        file_name=filename,
        mime="application/pdf",
        width="stretch"
    )

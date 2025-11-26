# pages/8_Reports.py

import streamlit as st
import pandas as pd
from datetime import date
from db import get_conn, init_db
import io

init_db()

st.title("📊 Reports")

conn = get_conn()

tokens = pd.read_sql_query("""
    SELECT 
        t.id AS token_no,
        t.datetime,
        t.party_name,
        t.weight,
        t.packages,
        t.amount
    FROM tokens t
""", conn)

payments = pd.read_sql_query("""
    SELECT party_id, date, amount
    FROM payments
""", conn)

parties = pd.read_sql_query("""
    SELECT id, party_name
    FROM party_master
""", conn)

conn.close()

if not tokens.empty:
    tokens["dt"] = pd.to_datetime(tokens["datetime"], format="%d-%m-%Y %I:%M %p", errors="coerce")
    tokens = tokens[tokens["dt"].notna()]
    tokens["d"] = tokens["dt"].dt.date

if not payments.empty:
    payments["dt"] = pd.to_datetime(payments["date"], errors="coerce", dayfirst=True)
    payments = payments[payments["dt"].notna()]

tab1, tab2 = st.tabs(["📅 Daily Booking", "💰 Outstanding"])

# ============ TAB 1 ============
with tab1:
    st.subheader("📅 Daily Booking")

    col1, col2 = st.columns(2)
    with col1:
        start_dt = st.date_input("From Date", date.today().replace(day=1))
    with col2:
        end_dt = st.date_input("To Date", date.today())

    if start_dt > end_dt:
        st.error("Invalid date range.")
    else:
        if tokens.empty:
            st.warning("No booking data.")
        else:
            df = tokens[(tokens["d"] >= start_dt) & (tokens["d"] <= end_dt)]
            if df.empty:
                st.warning("No records in range.")
            else:
                grp = df.groupby("d").agg(
                    tokens=("token_no", "count"),
                    weight=("weight", "sum"),
                    amount=("amount", "sum")
                ).reset_index()

                grp["d"] = grp["d"].apply(lambda x: x.strftime("%d-%m-%Y"))

                st.dataframe(
                    grp.rename(columns={
                        "d": "Date",
                        "tokens": "Tokens",
                        "weight": "Total Weight",
                        "amount": "Total Amount"
                    }),
                    width="stretch"
                )

# ============ TAB 2 ============
with tab2:
    st.subheader("💰 Outstanding by Party")

    if tokens.empty and payments.empty:
        st.warning("Not enough data.")
    else:
        tok_sum = (
            tokens.groupby("party_name")["amount"].sum()
            if not tokens.empty else pd.Series()
        )

        pay_sum = (
            payments.merge(parties, left_on="party_id", right_on="id")
            .groupby("party_name")["amount"].sum()
            if not payments.empty else pd.Series()
        )

        out_df = pd.DataFrame({
            "Total Billing": tok_sum,
            "Payments": pay_sum
        }).fillna(0)

        out_df["Outstanding"] = out_df["Total Billing"] - out_df["Payments"]

        st.dataframe(out_df, width="stretch")

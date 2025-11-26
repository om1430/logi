# app.py
import streamlit as st
from db import init_db, compute_party_balance, get_party_list

st.set_page_config(
    page_title="Transport Management Software",
    page_icon="🚚",
    layout="wide",
)

# Init DB at startup
init_db()

# Simple CSS
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 1.5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 1.5rem;
}
.stats-box {
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 10px;
    border-left: 4px solid #667eea;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🚚 Transport Management Software</h1>
    <p>Simple Token, Challan, Billing & Ledger System (Logistics Friendly)</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 👋 Welcome")

st.write("""
यह software **Transport / Logistics Company** के लिए बनाया गया है।  
यूज़र को बस simple buttons दबाने हैं:

- **Party Master** → Party add / edit  
- **Token / Bilty** → रोज़ का booking entry  
- **Challan** → Truck load करते समय tokens चुनकर challan बनाओ  
- **Billing** → Party & Date Range से Bill बनाओ  
- **Payments** → Cash/Bank entry  
- **Ledger** → Party का हिसाब देखो  
- **Reports** → Daily report, outstanding, आदि  
""")

parties = get_party_list()
if parties:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="stats-box"><b>Parties:</b> ' + str(len(parties)) + '</div>',
                    unsafe_allow_html=True)
else:
    st.info("👉 सबसे पहले बाईं तरफ़ से **Party Master** page में जाकर Parties add करें।")

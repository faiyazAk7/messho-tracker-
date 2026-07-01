import streamlit as st
import pdfplumber
import re
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Meesho Profit Tracker", page_icon="🚀", layout="wide")
st.title("🚀 Meesho Smart Analytics Panel")
st.markdown("---")

if 'orders_list' not in st.session_state:
    st.session_state.orders_list = [
        {"Sub Order ID": "301977326731015552_1", "Account": "flexine", "Selling Price": 186.13, "Cost Price": 50.00, "Tax (2%)": 3.72, "Packaging": 5.00, "Net Profit": 127.41, "Date": "2026-06-28"},
        {"Sub Order ID": "301735111807213056_1", "Account": "at your need", "Selling Price": 78.63, "Cost Price": 50.00, "Tax (2%)": 1.57, "Packaging": 5.00, "Net Profit": 22.06, "Date": "2026-06-28"}
    ]

st.sidebar.header("📦 Upload Meesho Label")
account_selected = st.sidebar.selectbox("Select Account Name", ["flexine", "at your need"])
uploaded_pdf = st.sidebar.file_uploader("Upload Shipping Label (PDF)", type=["pdf"])

if uploaded_pdf is not None:
    with pdfplumber.open(uploaded_pdf) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() or ""
            
    sub_order_match = re.search(r'(?:Sub\s*Order\s*No|Order\s*No)[:\s\-\#]+(\d+)', full_text, re.IGNORECASE)
    price_match = re.search(r'(?:₹|Rs\.?)\s*(\d+(?:\.\d{2})?)', full_text)
    
    sub_id = sub_order_match.group(1) if sub_order_match else f"MANUAL_{datetime.now().strftime('%M%S')}"
    selling_price = float(price_match.group(1)) if price_match else 150.0
    
    exists = any(x["Sub Order ID"] == sub_id for x in st.session_state.orders_list)
    
    if not exists:
        cost_price = 50.00
        tax = round(selling_price * 0.02, 2)
        packaging = 5.00
        net_profit = round(selling_price - cost_price - tax - packaging, 2)
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        new_order = {
            "Sub Order ID": sub_id,
            "Account": account_selected,
            "Selling Price": selling_price,
            "Cost Price": cost_price,
            "Tax (2%)": tax,
            "Packaging": packaging,
            "Net Profit": net_profit,
            "Date": current_date
        }
        st.session_state.orders_list.insert(0, new_order)
        st.sidebar.success(f"Order {sub_id} Processed Successfully!")

df = pd.DataFrame(st.session_state.orders_list)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Orders Tracked", value=len(df))
with col2:
    st.metric(label="Total Gross Sales", value=f"₹{round(df['Selling Price'].sum(), 2)}")
with col3:
    st.metric(label="Total Net Profit (Jeb Ka Paisa)", value=f"₹{round(df['Net Profit'].sum(), 2)}")

st.markdown("### 📊 Performance Analytics")
col_a, col_b = st.columns(2)
with col_a:
    st.write("**Account wise Profit**")
    st.bar_chart(df.groupby("Account")["Net Profit"].sum())
with col_b:
    st.write("**Orders Distribution**")
    st.bar_chart(df.groupby("Account").size())

st.markdown("### 📋 Processed Orders Log")
st.dataframe(df, use_container_width=True)

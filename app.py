import streamlit as st
import pdfplumber
import re
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Meesho Profit Tracker", page_icon="🚀", layout="wide")
st.title("🚀 Meesho Smart Analytics Panel (Permanent Storage)")
st.markdown("---")

# 🔗 Teri Google Sheet ka link
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1eUPB9qd4nWjjvaqWScjn-U5a-9bpo3UKf-9ps110TUM/edit?usp=sharing"

# Google Sheets se connect karne ka naya mast tareeka
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=GOOGLE_SHEET_URL, ttl="0d")
except Exception as e:
    df = pd.DataFrame(columns=["Sub Order ID", "Account", "Selling Price", "Cost Price", "Tax (2%)", "Packaging", "Net Profit", "Date"])

# Session state ko update karna
if 'orders_list' not in st.session_state:
    if not df.empty and "Sub Order ID" in df.columns:
        st.session_state.orders_list = df.to_dict(orient="records")
    else:
        st.session_state.orders_list = []

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
    
    # Check if duplicate
    exists = any(str(x["Sub Order ID"]) == str(sub_id) for x in st.session_state.orders_list)
    
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
        
        # Pehle local list mein daalo
        st.session_state.orders_list.insert(0, new_order)
        
        # Ab Google Sheet mein save karne ke liye update karo
        updated_df = pd.DataFrame(st.session_state.orders_list)
        try:
            conn.update(spreadsheet=GOOGLE_SHEET_URL, data=updated_df)
            st.sidebar.success(f"Order {sub_id} Saved to Google Sheet!")
        except Exception as e:
            st.sidebar.warning("Data added locally, Google Sheet saving failed. Check if Sheet is set to Editor.")

# Data load update for dashboard
df_display = pd.DataFrame(st.session_state.orders_list)

if not df_display.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Orders Tracked", value=len(df_display))
    with col2:
        st.metric(label="Total Gross Sales", value=f"₹{round(df_display['Selling Price'].sum(), 2)}")
    with col3:
        st.metric(label="Total Net Profit (Jeb Ka Paisa)", value=f"₹{round(df_display['Net Profit'].sum(), 2)}")

    st.markdown("### 📊 Performance Analytics")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Account wise Profit**")
        st.bar_chart(df_display.groupby("Account")["Net Profit"].sum())
    with col_b:
        st.write("**Orders Distribution**")
        st.bar_chart(df_display.groupby("Account").size())

    st.markdown("### 📋 Processed Orders Log")
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("No orders tracked yet. Upload a Meesho label PDF from the sidebar to start!")

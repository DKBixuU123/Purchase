import streamlit as st
import pandas as pd

import streamlit as st
import pandas as pd
from datetime import date

# Page Setup
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 1. USER DATABASE & PASSWORDS
user_db = {
    "End User / PPC": "ppc123", "Purchaser": "buy123", "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123", "Finance Head": "fin123", "CEO / MD": "ceo123",
    "PE & Facility": "pe123", "Hr & Admin": "hr123", "Stores": "store123",
    "Engineering": "eng123", "IT": "it123"
}

# --- INITIALIZE DATA STORAGE ---
if 'rfq_list' not in st.session_state:
    st.session_state['rfq_list'] = []
if 'quotations' not in st.session_state:
    st.session_state['quotations'] = []
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- SIDEBAR LOGIN ---
st.sidebar.title("🔐 Secure Login")
if not st.session_state['logged_in']:
    selected_dept = st.sidebar.selectbox("Select Department/Role", list(user_db.keys()))
    pwd_input = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if pwd_input == user_db[selected_dept]:
            st.session_state['logged_in'] = True
            st.session_state['user'] = selected_dept
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Password")
else:
    st.sidebar.success(f"User: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- MAIN SYSTEM ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    st.title(f"🚀 Procurement Portal | {user}")

    # --- SECTION A: RAISE RFQ (For Departments) ---
    if user not in ["CEO / MD", "Sr. GM Commercial", "Finance Head", "Purchaser"]:
        st.header("Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item_name = st.text_input("Item Description")
            with c2: qty = st.number_input("Quantity", min_value=0.1)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
            
            col_a, col_b = st.columns(2)
            with col_a: req_date = st.date_input("Required Date", min_value=date.today())
            with col_b: remarks = st.text_area("Remarks")
            
            if st.form_submit_button("Submit RFQ"):
                st.session_state['rfq_list'].append({
                    "ID": len(st.session_state['rfq_list'])+101,
                    "Item": item_name, "Qty": qty, "UOM": uom, "Target": req_date, "Status": "Open"
                })
                st.success("✅ RFQ Submitted to Purchase!")

    # --- SECTION B: QUOTATION ENTRY (For Purchaser) ---
    if user == "Purchaser":
        st.header("Step 2: Enter Vendor Quotations")
        if not st.session_state['rfq_list']:
            st.info("No pending RFQs to process.")
        else:
            selected_rfq = st.selectbox("Select RFQ ID to add Quote", [r['ID'] for r in st.session_state['rfq_list']])
            
            with st.form("quote_form"):
                v1, v2, v3 = st.columns(3)
                with v1: vendor = st.text_input("Supplier Name")
                with v2: price = st.number_input("Unit Price (Basic)", min_value=0.0)
                with v3: discount = st.number_input("Discount (%)", min_value=0.0)
                
                t1, t2 = st.columns(2)
                with t1: pay_terms = st.text_input("Payment Terms (e.g. 30 Days)")
                with t2: lead_time = st.text_input("Lead Time (e.g. 1 Week)")
                
                if st.form_submit_button("Add Quotation"):
                    net_price = price * (1 - discount/100)
                    st.session_state['quotations'].append({
                        "RFQ_ID": selected_rfq, "Vendor": vendor, "Basic": price,
                        "Disc%": discount, "Net": net_price, "Terms": pay_terms, "Lead": lead_time
                    })
                    st.success(f"Quote from {vendor} added!")

    # --- SECTION C: COMPARISON & L1 INDICATOR (Visible to Purchaser & HOD+) ---
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("Step 3: Auto-Comparison & L1 Selection")
        
        if st.session_state['quotations']:
            df_q = pd.DataFrame(st.session_state['quotations'])
            
            # Find the minimum Net Price for L1
            min_price = df_q['Net'].min()

            def highlight_l1(row):
                return ['background-color: #d1e7dd; font-weight: bold' if row.Net == min_price else '' for _ in row]

            st.subheader("Comparison Table")
            st.table(df_q.style.apply(highlight_l1, axis=1))
            st.success(f"✨ System Recommendation: L1 Vendor selected based on Net Price.")
            
            if user != "Purchaser":
                if st.button("Generate Purchase Requisition (PR) for L1"):
                    st.balloons()
                    st.success("PR Created successfully for the Lowest Quote!")
        else:
            st.info("Waiting for Purchaser to enter quotations...")

    # --- SECTION D: LIVE DASHBOARD ---
    st.divider()
    st.subheader("📊 RFQ Tracking Dashboard")
    if st.session_state['rfq_list']:
        st.write(pd.DataFrame(st.session_state['rfq_list']))

else:
    st.info("👈 Please login to access the Procurement System.")

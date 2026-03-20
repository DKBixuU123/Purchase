import streamlit as st
import pandas as pd

import streamlit as st
import pandas as pd
from datetime import date

# Page Setup
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 1. USER DATABASE & PASSWORDS
# You can change these passwords here anytime
user_db = {
    "End User / PPC": "ppc123",
    "Purchaser": "buy123",
    "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123",
    "Finance Head": "fin123",
    "CEO / MD": "ceo123",
    "PE & Facility": "pe123",
    "Hr & Admin": "hr123",
    "Stores": "store123",
    "Engineering": "eng123",
    "IT": "it123"
}

# --- SESSION MANAGEMENT ---
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
        st.session_state['logged_in'] = False
        st.rerun()

# --- MAIN SYSTEM ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    st.title(f"🚀 Procurement Portal | {user}")

    # 2 & 3 & 4. ENHANCED RFQ FORM
    # Usually, only Departments raise RFQs, while Seniors Approve
    if user not in ["CEO / MD", "Sr. GM Commercial", "Finance Head"]:
        st.header("Step 1: Raise New RFQ")
        
        with st.form("rfq_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                item_name = st.text_input("Item / Service Description")
                qty = st.number_input("Required Quantity", min_value=1)
                # 3. List of Departments
                dept = st.selectbox("Requesting Department", [
                    "PPC", "PE & Facility", "Hr & Admin", "Stores", "Engineering", "IT", "Production"
                ])
                
            with col2:
                # 2. Required Date & Remarks
                req_date = st.date_input("Required Date (Deadline)", min_value=date.today())
                remarks = st.text_area("Detailed Remarks / Specs")
            
            # 4. Image/Document Upload Option
            uploaded_file = st.file_uploader("Upload Drawing, Image, or Specification (PDF/JPG/PNG)", 
                                            type=["pdf", "png", "jpg", "jpeg"])
            
            if st.form_submit_button("Submit RFQ"):
                st.success(f"✅ RFQ for {item_name} has been raised successfully!")
                if uploaded_file:
                    st.write(f"📎 Attached file: {uploaded_file.name}")

    # --- COMPARISON & APPROVAL (For Seniors & Purchaser) ---
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("Step 3: Auto-Comparison Statement (CS)")
        
        # Example Data
        cs_table = pd.DataFrame({
            "Vendor": ["Alpha Tech", "Beta Corp", "Gamma Ind."],
            "Unit Price (INR)": [5500, 4800, 5100],
            "Lead Time": ["15 Days", "7 Days", "10 Days"],
            "Rating": ["⭐⭐⭐", "⭐⭐⭐⭐⭐", "⭐⭐⭐⭐"],
            "Rank": ["L3", "L1", "L2"]
        })
        
        # Highlight L1 in Green
        def highlight_l1(s):
            return ['background-color: #d1e7dd' if s.Rank == 'L1' else '' for _ in s]
        
        st.table(cs_table.style.apply(highlight_l1, axis=1))

        # APPROVAL ACTIONS
        if user != "Purchaser":
            st.subheader("Step 5: Authorization")
            st.info(f"Pending Approval for {user}")
            c1, c2 = st.columns(4)
            with c1: st.button("✅ Approve", key="app")
            with c2: st.button("❌ Reject", key="rej")

else:
    st.info("👈 Please enter your password in the sidebar to begin.")

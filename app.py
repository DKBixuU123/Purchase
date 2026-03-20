import streamlit as st
import pandas as pd

import streamlit as st
import pandas as pd
from datetime import date
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

# --- INITIALIZE DATA STORAGE (The Dashboard List) ---
if 'rfq_list' not in st.session_state:
    st.session_state['rfq_list'] = []

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

    # STEP 1: RFQ FORM
    if user not in ["CEO / MD", "Sr. GM Commercial", "Finance Head"]:
        st.header("Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                item_name = st.text_input("Item / Service Description")
            with col2:
                qty = st.number_input("Quantity", min_value=0.1, step=0.1)
            with col3:
                # NEW UOM FIELD
                uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr", "Box", "Pkt", "Sq.Mtr"])
                
            col_a, col_b = st.columns(2)
            with col_a:
                dept = st.selectbox("Requesting Department", ["PPC", "PE & Facility", "Hr & Admin", "Stores", "Engineering", "IT", "Production"])
                req_date = st.date_input("Required Date (Deadline)", min_value=date.today())
            with col_b:
                remarks = st.text_area("Detailed Remarks / Specs")
            
            uploaded_file = st.file_uploader("Upload Drawing/Specs", type=["pdf", "png", "jpg", "jpeg"])
            
            if st.form_submit_button("Submit RFQ"):
                # Save details including UOM
                new_rfq = {
                    "Date Raised": date.today().strftime("%d-%m-%Y"),
                    "Item": item_name,
                    "Qty": qty,
                    "UOM": uom,
                    "Dept": dept,
                    "Target Date": req_date.strftime("%d-%m-%Y"),
                    "Remarks": remarks,
                    "Attachment": uploaded_file.name if uploaded_file else "No File",
                    "Status": "Pending at Purchase"
                }
                st.session_state['rfq_list'].append(new_rfq)
                st.success(f"✅ RFQ for {item_name} ({qty} {uom}) submitted successfully!")

        # --- LIVE DASHBOARD VIEW ---
        st.divider()
        st.header("📋 Submitted RFQ Status Dashboard")
        if st.session_state['rfq_list']:
            # Showing newest first
            df_display = pd.DataFrame(st.session_state['rfq_list'])
            st.dataframe(df_display.iloc[::-1], use_container_width=True)
        else:
            st.info("No RFQs submitted in this session.")

    # STEP 3: COMPARISON (Visible to Purchaser & Seniors)
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("Step 3: Comparison Statement (CS)")
        cs_table = pd.DataFrame({
            "Vendor": ["Alpha Tech", "Beta Corp", "Gamma Ind."],
            "Price (INR)": [5500, 4800, 5100], 
            "Lead Time": ["15 Days", "7 Days", "10 Days"],
            "Terms": ["30 Days", "Advance", "15 Days"],
            "Rank": ["L3", "L1", "L2"]
        })
        def highlight_l1(s):
            return ['background-color: #d1e7dd' if s.Rank == 'L1' else '' for _ in s]
        st.table(cs_table.style.apply(highlight_l1, axis=1))

        if user != "Purchaser":
            st.subheader("Step 5: Authorization")
            col_app, col_rej = st.columns([1, 5])
            with col_app: st.button("✅ Approve")
            with col_rej: st.button("❌ Reject")

else:
    st.info("👈 Please enter your password in the sidebar to begin.")

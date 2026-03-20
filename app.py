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
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("Item / Service Description")
                qty = st.number_input("Required Quantity", min_value=1)
                dept = st.selectbox("Requesting Department", ["PPC", "PE & Facility", "Hr & Admin", "Stores", "Engineering", "IT", "Production"])
            with col2:
                req_date = st.date_input("Required Date (Deadline)", min_value=date.today())
                remarks = st.text_area("Detailed Remarks / Specs")
            
            uploaded_file = st.file_uploader("Upload Drawing/Specs", type=["pdf", "png", "jpg", "jpeg"])
            
            if st.form_submit_button("Submit RFQ"):
                # Save details to the list
                new_rfq = {
                    "Date Raised": date.today().strftime("%d-%m-%Y"),
                    "Item": item_name,
                    "Qty": qty,
                    "Dept": dept,
                    "Target Date": req_date.strftime("%d-%m-%Y"),
                    "Remarks": remarks,
                    "Attachment": uploaded_file.name if uploaded_file else "No File",
                    "Status": "Pending at Purchase"
                }
                st.session_state['rfq_list'].append(new_rfq)
                st.success("✅ RFQ submitted and added to the dashboard below!")

        # --- NEW DASHBOARD VIEW (Inside the same view) ---
        st.divider()
        st.header("📋 Your Submitted RFQ Dashboard")
        if st.session_state['rfq_list']:
            df_display = pd.DataFrame(st.session_state['rfq_list'])
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No RFQs submitted yet. Fill the form above to see details here.")

    # STEP 3: COMPARISON (Visible to Purchaser & Seniors)
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("Step 3: Comparison Statement (CS)")
        cs_table = pd.DataFrame({
            "Vendor": ["Alpha Tech", "Beta Corp", "Gamma Ind."],
            "Price (INR)": [5500, 4800, 5100], "Lead Time": ["15 Days", "7 Days", "10 Days"],
            "Rating": ["⭐⭐⭐", "⭐⭐⭐⭐⭐", "⭐⭐⭐⭐"], "Rank": ["L3", "L1", "L2"]
        })
        def highlight_l1(s):
            return ['background-color: #d1e7dd' if s.Rank == 'L1' else '' for _ in s]
        st.table(cs_table.style.apply(highlight_l1, axis=1))

        if user != "Purchaser":
            st.subheader("Step 5: Authorization")
            c1, c2 = st.columns(4)
            with c1: st.button("✅ Approve PR")
            with c2: st.button("❌ Reject PR")

else:
    st.info("👈 Please enter your password in the sidebar to begin.")

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

# --- DATA PERSISTENCE (Session State) ---
# This keeps data alive as long as the app tab is open.
if 'rfq_master' not in st.session_state:
    st.session_state['rfq_master'] = []
if 'quotes_master' not in st.session_state:
    st.session_state['quotes_master'] = {}

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 Secure Login")
if not st.session_state['logged_in']:
    selected_role = st.sidebar.selectbox("Select Role", list(user_db.keys()))
    pwd_input = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if pwd_input == user_db[selected_role]:
            st.session_state['logged_in'] = True
            st.session_state['user'] = selected_role
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Password")
else:
    st.sidebar.success(f"User: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- MAIN APP ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    
    # --- DASHBOARD (ALWAYS VISIBLE AT TOP) ---
    st.title(f"🚀 Procurement Dashboard")
    st.subheader("📋 RFQ Status Tracker (Live Data)")
    if st.session_state['rfq_master']:
        df_master = pd.DataFrame(st.session_state['rfq_master'])
        st.dataframe(df_master, use_container_width=True)
    else:
        st.info("No RFQs found in the system.")
    
    st.divider()

    # --- PHASE 1: DEPARTMENT VIEW (Create RFQ) ---
    if user not in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📝 Create New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item = st.text_input("Item Description")
            with c2: qty = st.number_input("Qty", min_value=1.0)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
            
            r1, r2 = st.columns(2)
            with r1: req_date = st.date_input("Required By", min_value=date.today())
            with r2: remarks = st.text_area("Remarks")
            
            if st.form_submit_button("Submit RFQ"):
                rfq_id = f"RFQ-{len(st.session_state['rfq_master']) + 101}"
                new_entry = {
                    "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                    "Required Date": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote"
                }
                st.session_state['rfq_master'].append(new_entry)
                st.success(f"✅ {rfq_id} Saved to Dashboard!")
                st.rerun()

    # --- PHASE 2: PURCHASER VIEW (Add Quotes) ---
    if user == "Purchaser":
        st.header("📥 Purchaser Action: Add Quotes")
        pending_list = [r['RFQ ID'] for r in st.session_state['rfq_master'] if r['Status'] == "Pending Quote"]
        
        if pending_list:
            selected_rfq = st.selectbox("Select RFQ to Process", pending_list)
            
            with st.expander(f"Add Vendor Details for {selected_rfq}", expanded=True):
                with st.form("q_form", clear_on_submit=True):
                    v1, v2, v3 = st.columns(3)
                    with v1: vendor = st.text_input("Vendor Name")
                    with v2: price = st.number_input("Rate", min_value=0.0)
                    with v3: disc = st.number_input("Discount %", min_value=0.0)
                    
                    if st.form_submit_button("Save Quote"):
                        if selected_rfq not in st.session_state['quotes_master']:
                            st.session_state['quotes_master'][selected_rfq] = []
                        
                        net = price * (1 - disc/100)
                        st.session_state['quotes_master'][selected_rfq].append({
                            "Vendor": vendor, "Rate": price, "Disc %": disc, "Net Price": net
                        })
                        st.success(f"Quote for {vendor} saved!")
        else:
            st.write("All RFQs have been processed.")

    # --- PHASE 3: COMPARISON STATEMENT (Purchaser & Approvers) ---
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📊 Comparison Statement (CS)")
        available_cs = list(st.session_state['quotes_master'].keys())
        
        if available_cs:
            cs_rfq = st.selectbox("View CS for RFQ:", available_cs)
            if st.button("Generate L1 Comparison"):
                df_cs = pd.DataFrame(st.session_state['quotes_master'][cs_rfq])
                l1_price = df_cs['Net Price'].min()
                
                def color_l1(row):
                    return ['background-color: #d1e7dd' if row['Net Price'] == l1_price else '' for _ in row]
                
                st.table(df_cs.style.apply(color_l1, axis=1))
                st.success(f"L1 Vendor identified for {cs_rfq}")
        else:
            st.info("No quotations found. Purchaser must enter quotes first.")

else:
    st.info("Please login to see your historical RFQ data.")

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
    st.session_state['quotations'] = {} # Dictionary to link quotes to RFQ ID
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- SIDEBAR LOGIN ---
st.sidebar.title("🔐 Secure Login")
if not st.session_state['logged_in']:
    selected_dept = st.sidebar.selectbox("Select Role", list(user_db.keys()))
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

    # --- PHASE 1: RAISE RFQ (For End Users/Depts) ---
    if user not in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item = st.text_input("Item Description")
            with c2: qty = st.number_input("Quantity", min_value=1.0)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
            
            col_a, col_b = st.columns(2)
            with col_a: req_date = st.date_input("Required Date", min_value=date.today())
            with col_b: remarks = st.text_area("Remarks")
            
            if st.form_submit_button("Submit RFQ"):
                rfq_id = f"RFQ-{len(st.session_state['rfq_list']) + 1001}"
                st.session_state['rfq_list'].append({
                    "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, "Qty": qty, "UOM": uom, "Target": req_date.strftime("%d-%m-%Y"),
                    "Dept": user, "Status": "Pending Quote"
                })
                st.success(f"✅ {rfq_id} submitted to Purchase Team!")

    # --- PHASE 2: PURCHASER WORK AREA (Enter Quotations) ---
    if user == "Purchaser":
        st.header("Step 2: Supplier Quotation Entry")
        pending_rfqs = [r['RFQ ID'] for r in st.session_state['rfq_list'] if r['Status'] == "Pending Quote"]
        
        if not pending_rfqs:
            st.info("No pending RFQs to process.")
        else:
            sel_rfq = st.selectbox("Select Pending RFQ to Add Quotes", pending_rfqs)
            
            with st.expander(f"➕ Add Quote for {sel_rfq}", expanded=True):
                with st.form("quote_form", clear_on_submit=True):
                    v1, v2, v3 = st.columns(3)
                    with v1: vendor = st.text_input("Supplier Name")
                    with v2: price = st.number_input("Basic Price", min_value=0.0)
                    with v3: disc = st.number_input("Discount %", min_value=0.0)
                    
                    t1, t2 = st.columns(2)
                    with t1: p_terms = st.text_input("Payment Terms")
                    with t2: l_time = st.text_input("Lead Time")
                    
                    if st.form_submit_button("Save Quotation"):
                        if sel_rfq not in st.session_state['quotations']:
                            st.session_state['quotations'][sel_rfq] = []
                        
                        net_price = price * (1 - disc/100)
                        st.session_state['quotations'][sel_rfq].append({
                            "Supplier": vendor, "Basic": price, "Disc%": disc, 
                            "Net Price": net_price, "Payment": p_terms, "Lead Time": l_time
                        })
                        st.success(f"Quote from {vendor} saved for {sel_rfq}")

    # --- PHASE 3: COMPARISON STATEMENT (For Purchaser & HOD+) ---
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("Step 3: Comparison Statement (CS)")
        
        # Select from RFQs that have at least one quote
        ready_rfqs = list(st.session_state['quotations'].keys())
        
        if not ready_rfqs:
            st.warning("No quotations entered yet. L1 cannot be calculated.")
        else:
            view_rfq = st.selectbox("Select RFQ to Generate CS", ready_rfqs)
            
            if st.button("📊 Generate Comparison Statement"):
                df_cs = pd.DataFrame(st.session_state['quotations'][view_rfq])
                
                # Logic to find L1
                min_net = df_cs['Net Price'].min()
                
                def highlight_l1(row):
                    return ['background-color: #d1e7dd; font-weight: bold' if row['Net Price'] == min_net else '' for _ in row]
                
                st.subheader(f"Comparison View for {view_rfq}")
                st.table(df_cs.style.apply(highlight_l1, axis=1))
                st.success(f"🏆 L1 Supplier identified based on lowest Net Price.")

    # --- GLOBAL DASHBOARD (Visible to All) ---
    st.divider()
    st.header("📋 RFQ Status Dashboard")
    if st.session_state['rfq_list']:
        df_dash = pd.DataFrame(st.session_state['rfq_list'])
        st.dataframe(df_dash.iloc[::-1], use_container_width=True)
    else:
        st.info("No RFQs found in the system.")

else:
    st.info("👈 Please enter your credentials in the sidebar to begin.")

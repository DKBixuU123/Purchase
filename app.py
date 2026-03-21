import streamlit as st
import pandas as pd
from datetime import date

# 1. PAGE CONFIG
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 2. USER ACCESS CONTROL
user_db = {
    "End User / PPC": "ppc123", "Purchaser": "buy123", "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123", "Finance Head": "fin123", "CEO / MD": "ceo123",
    "PE & Facility": "pe123", "Hr & Admin": "hr123", "Stores": "store123",
    "Engineering": "eng123", "IT": "it123"
}

# 3. DATA STORAGE (Keeps history for the session)
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
        st.session_state.clear()
        st.rerun()

# --- MAIN SYSTEM ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    st.title(f"🚀 Procurement Portal")
    
    # --- DASHBOARD (HISTORY) - ALWAYS SHOWN AT TOP ---
    st.header("📋 RFQ Status Tracker")
    if st.session_state['rfq_master']:
        # This shows ALL RFQs, including the old ones
        df_history = pd.DataFrame(st.session_state['rfq_master'])
        st.dataframe(df_history.iloc[::-1], use_container_width=True) # Newest on top
    else:
        st.info("No RFQs found in history.")
    
    st.divider()

    # PHASE 1: CREATE RFQ (Visible to Depts)
    if user not in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📝 Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item = st.text_input("Item Description")
            with c2: qty = st.number_input("Qty", min_value=0.1)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
            
            r1, r2 = st.columns(2)
            with r1: req_date = st.date_input("Required By", min_value=date.today())
            with r2: remarks = st.text_area("Special Instructions/Remarks")
            
            # ADDED DOCUMENT UPLOAD FOR RFQ
            rfq_doc = st.file_uploader("Upload Drawing/Specs/Reference", type=['pdf', 'jpg', 'png'])
            
            if st.form_submit_button("Submit RFQ"):
                rfq_id = f"RFQ-{len(st.session_state['rfq_master']) + 101}"
                st.session_state['rfq_master'].append({
                    "RFQ ID": rfq_id, 
                    "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, 
                    "Qty": qty, 
                    "UOM": uom, 
                    "Dept": user, 
                    "Required Date": req_date.strftime("%d-%m-%Y"), 
                    "Status": "Pending Quote",
                    "File": rfq_doc.name if rfq_doc else "No File"
                })
                st.success(f"✅ {rfq_id} successfully raised and visible to Purchaser!")
                st.rerun()

    # PHASE 2: QUOTATION ENTRY (Visible to Purchaser)
    if user == "Purchaser":
        st.header("📥 Purchaser: Arrange Supplier Quotations")
        # Only show RFQs that need quotes
        pending_ids = [r['RFQ ID'] for r in st.session_state['rfq_master'] if r['Status'] == "Pending Quote"]
        
        if pending_ids:
            sel_id = st.selectbox("Select RFQ to add Vendor Quotes", pending_ids)
            
            # PULL DATA AUTOMATICALLY
            rfq_data = next(i for i in st.session_state['rfq_master'] if i["RFQ ID"] == sel_id)
            st.info(f"**Item:** {rfq_data['Item']} | **Qty:** {rfq_data['Qty']} {rfq_data['UOM']}")
            
            with st.form("q_entry_form", clear_on_submit=True):
                v1, v2, v3 = st.columns(3)
                with v1: v_name = st.text_input("Supplier Name")
                with v2: v_price = st.number_input("Unit Price", min_value=0.0)
                with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                
                t1, t2, t3 = st.columns(3)
                with t1: v_terms = st.text_input("Payment Terms")
                with t2: v_lead = st.text_input("Lead Time")
                with t3: v_quote_doc = st.file_uploader("Upload Supplier Quote", type=['pdf', 'jpg', 'png'])
                
                if st.form_submit_button("➕ Save Supplier Quote"):
                    if sel_id not in st.session_state['quotes_master']:
                        st.session_state['quotes_master'][sel_id] = []
                    
                    net = v_price * (1 - v_disc/100)
                    st.session_state['quotes_master'][sel_id].append({
                        "Supplier": v_name, "Rate": v_price, "Disc%": v_disc, 
                        "Net Price": net, "Payment": v_terms, "Lead Time": v_lead,
                        "Quote File": v_quote_doc.name if v_quote_doc else "None"
                    })
                    st.success(f"Quote for {v_name} added to {sel_id}!")
                    st.rerun()

            # SHOW CURRENT LIST OF QUOTES FOR THIS RFQ
            if sel_id in st.session_state['quotes_master']:
                st.subheader(f"Quotes received for {sel_id}")
                st.table(pd.DataFrame(st.session_state['quotes_master'][sel_id]))
        else:
            st.info("No new RFQs pending for quotes.")

    # PHASE 3: COMPARISON (All Approvers)
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("📊 Step 3: Generate Comparison Statement")
        ready_ids = list(st.session_state['quotes_master'].keys())
        
        if ready_ids:
            cs_id = st.selectbox("Select RFQ for L1 Analysis", ready_ids)
            if st.button("Generate L1 Report"):
                df_cs = pd.DataFrame(st.session_state['quotes_master'][cs_id])
                l1_val = df_cs['Net Price'].min()
                
                def color_l1(row):
                    return ['background-color: #d1e7dd; font-weight: bold' if row['Net Price'] == l1_val else '' for _ in row]
                
                st.subheader(f"L1 Analysis: {cs_id}")
                st.table(df_cs.style.apply(color_l1, axis=1))
                st.success("The Green row indicates the L1 Supplier.")
        else:
            st.write("Awaiting quotes from Purchaser.")

else:
    st.info("👈 Please enter password to access system.")

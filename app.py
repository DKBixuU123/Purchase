import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. PAGE CONFIG
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 2. DATA INITIALIZATION (Fallback to Session State until you link Google Sheets)
# To make this truly permanent, we would replace this block with Google Sheet connection code.
if 'rfq_master' not in st.session_state:
    st.session_state['rfq_master'] = []
if 'quotes_master' not in st.session_state:
    st.session_state['quotes_master'] = {}

# 3. USER ROLES
user_db = {
    "End User / PPC": "ppc123", "Purchaser": "buy123", "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123", "Finance Head": "fin123", "CEO / MD": "ceo123"
}

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.sidebar.title("🔐 Secure Login")
if not st.session_state['logged_in']:
    role = st.sidebar.selectbox("Select Role", list(user_db.keys()))
    pwd = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if pwd == user_db[role]:
            st.session_state['logged_in'] = True
            st.session_state['user'] = role
            st.rerun()
        else: st.sidebar.error("❌ Invalid Password")
else:
    st.sidebar.info(f"User: {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- MAIN APP ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    
    # DASHBOARD (Always visible, always carries over old data)
    st.header("📋 RFQ Status Tracker")
    if st.session_state['rfq_master']:
        st.table(pd.DataFrame(st.session_state['rfq_master']).iloc[::-1])
    else:
        st.info("No RFQs found in history.")
    
    st.divider()

    # PHASE 1: PPC / END USER (Raise RFQ)
    if user == "End User / PPC":
        st.header("📝 Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item = st.text_input("Item Description")
            with c2: qty = st.number_input("Qty", min_value=0.1)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
            
            r1, r2 = st.columns(2)
            with r1: req_date = st.date_input("Required By")
            with r2: remarks = st.text_area("Remarks")
            
            doc = st.file_uploader("Upload Specs", type=['pdf','jpg','png'])
            
            if st.form_submit_button("Submit RFQ"):
                rfq_id = f"RFQ-{len(st.session_state['rfq_master']) + 101}"
                st.session_state['rfq_master'].append({
                    "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                    "Required": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote",
                    "Attachment": doc.name if doc else "No File"
                })
                st.success(f"✅ {rfq_id} saved!")
                st.rerun()

    # PHASE 2: PURCHASER (Enter Quotes & Clear Form)
    if user == "Purchaser":
        st.header("📥 Purchaser: Arrange Supplier Quotations")
        pending_ids = [r['RFQ ID'] for r in st.session_state['rfq_master']]
        
        if pending_ids:
            sel_id = st.selectbox("Select RFQ to add Quotes", pending_ids)
            rfq_data = next(i for i in st.session_state['rfq_master'] if i["RFQ ID"] == sel_id)
            
            # PULL DATA FROM RFQ
            st.warning(f"📌 Working on: **{rfq_data['Item']}** ({rfq_data['Qty']} {rfq_data['UOM']})")
            
            with st.form("quote_form", clear_on_submit=True):
                v1, v2, v3 = st.columns(3)
                with v1: v_name = st.text_input("Supplier Name")
                with v2: v_price = st.number_input("Unit Price", min_value=0.0)
                with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                
                t1, t2, t3 = st.columns(3)
                with t1: v_terms = st.text_input("Payment Terms")
                with t2: v_lead = st.text_input("Lead Time")
                with t3: v_file = st.file_uploader("Upload Quote", type=['pdf','jpg','png'])
                
                if st.form_submit_button("Save Supplier Quote"):
                    if sel_id not in st.session_state['quotes_master']:
                        st.session_state['quotes_master'][sel_id] = []
                    
                    net = v_price * (1 - v_disc/100)
                    st.session_state['quotes_master'][sel_id].append({
                        "Supplier": v_name, "Rate": v_price, "Disc%": v_disc, 
                        "Net Price": net, "Payment": v_terms, "Lead Time": v_lead,
                        "File": v_file.name if v_file else "None"
                    })
                    st.success(f"Quote for {v_name} saved! Form is now blank for next supplier.")
                    st.rerun()

            if sel_id in st.session_state['quotes_master']:
                st.subheader(f"Saved Quotes for {sel_id}")
                st.table(pd.DataFrame(st.session_state['quotes_master'][sel_id]))

    # PHASE 3: COMPARISON
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("📊 Final Comparison & L1")
        if st.session_state['quotes_master']:
            cs_id = st.selectbox("Select RFQ for Comparison", list(st.session_state['quotes_master'].keys()))
            if st.button("Generate CS"):
                df_cs = pd.DataFrame(st.session_state['quotes_master'][cs_id])
                l1_val = df_cs['Net Price'].min()
                st.table(df_cs.style.apply(lambda x: ['background: #d1e7dd' if x['Net Price'] == l1_val else '' for i in x], axis=1))

else:
    st.info("👈 Please login. Note: To stop data loss on code updates, we must link your Google Sheet.")

import streamlit as st
import pandas as pd
from datetime import date

# 1. PAGE CONFIG
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 2. USER ACCESS CONTROL
user_db = {
    "End User / PPC": "ppc123", "Purchaser": "buy123", "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123", "Finance Head": "fin123", "CEO / MD": "ceo123"
}

# 3. DATA STORAGE (Note: This will reset on code updates until Google Sheets is linked)
if 'rfq_master' not in st.session_state:
    st.session_state['rfq_master'] = []
if 'quotes_master' not in st.session_state:
    st.session_state['quotes_master'] = {}

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
        st.session_state.clear()
        st.rerun()

# --- MAIN APP ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    st.title(f"🚀 Procurement Portal")
    
    # --- DASHBOARD (History) ---
    st.header("📋 RFQ & PR Status Tracker")
    if st.session_state['rfq_master']:
        df_rfq = pd.DataFrame(st.session_state['rfq_master'])
        st.table(df_rfq.iloc[::-1]) 
    else:
        st.info("No records found.")
    
    st.divider()

    # --- PHASE 1: PPC / END USER (RFQ & PR) ---
    if user == "End User / PPC":
        tab1, tab2 = st.tabs(["📝 Raise New RFQ", "📤 Raise Purchase Requisition (PR)"])
        
        with tab1:
            with st.form("rfq_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1: item = st.text_input("Item Description")
                with c2: qty = st.number_input("Qty", min_value=0.1)
                with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
                r1, r2 = st.columns(2)
                with r1: req_date = st.date_input("Required By")
                with r2: remarks = st.text_area("Remarks")
                
                # RE-ADDED DOCUMENT UPLOAD
                rfq_doc = st.file_uploader("Upload Specs/Drawing", type=['pdf','jpg','png'], key="rfq_up")
                
                if st.form_submit_button("Submit RFQ"):
                    rfq_id = f"RFQ-{len(st.session_state['rfq_master']) + 101}"
                    st.session_state['rfq_master'].append({
                        "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                        "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                        "Required": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote",
                        "File": rfq_doc.name if rfq_doc else "No File"
                    })
                    st.success(f"✅ {rfq_id} Raised! You can now raise another without logging out.")
                    st.rerun()

        with tab2:
            cs_ready = [r['RFQ ID'] for r in st.session_state['rfq_master'] if r['Status'] == "CS Generated"]
            if cs_ready:
                sel_rfq = st.selectbox("Select RFQ to Raise PR", cs_ready)
                df_q = pd.DataFrame(st.session_state['quotes_master'][sel_rfq])
                st.write("### Comparison Results (CS)")
                st.table(df_q)
                
                with st.form("pr_form"):
                    chosen_vendor = st.selectbox("Select Recommended Vendor", df_q['Supplier'].unique())
                    justification = st.text_area("Justification for Selection")
                    if st.form_submit_button("Submit PR for Approval"):
                        for r in st.session_state['rfq_master']:
                            if r['RFQ ID'] == sel_rfq:
                                r['Status'] = "PR Pending Approval"
                                r['Vendor'] = chosen_vendor
                        st.success(f"PR for {sel_rfq} submitted to HOD!")
                        st.rerun()
            else:
                st.info("No Comparison Statements ready for PR.")

    # --- PHASE 2: PURCHASER (Quotes & CS) ---
    if user == "Purchaser":
        st.header("📥 Purchaser: Arrange Supplier Quotations")
        pending_rfqs = [r['RFQ ID'] for r in st.session_state['rfq_master'] if r['Status'] == "Pending Quote"]
        
        if pending_rfqs:
            sel_id = st.selectbox("Add Quotes for:", pending_rfqs)
            rfq_info = next(i for i in st.session_state['rfq_master'] if i["RFQ ID"] == sel_id)
            st.warning(f"📌 Item: {rfq_info['Item']} | Qty: {rfq_info['Qty']} {rfq_info['UOM']}")
            
            with st.form("q_form", clear_on_submit=True):
                v1, v2, v3 = st.columns(3)
                with v1: v_name = st.text_input("Supplier Name")
                with v2: v_price = st.number_input("Unit Price", min_value=0.0)
                with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                
                # QUOTATION DOCUMENT UPLOAD
                q_doc = st.file_uploader("Upload Supplier Quote", type=['pdf','jpg','png'], key="q_up")
                
                if st.form_submit_button("Save Quote"):
                    if sel_id not in st.session_state['quotes_master']: st.session_state['quotes_master'][sel_id] = []
                    st.session_state['quotes_master'][sel_id].append({
                        "Supplier": v_name, "Rate": v_price, "Disc%": v_disc, 
                        "Net Price": v_price * (1 - v_disc/100), "File": q_doc.name if q_doc else "None"
                    })
                    st.rerun()
            
            if sel_id in st.session_state['quotes_master']:
                st.table(pd.DataFrame(st.session_state['quotes_master'][sel_id]))
                if st.button("Finalize Comparison (Send to End User)"):
                    for r in st.session_state['rfq_master']:
                        if r['RFQ ID'] == sel_id: r['Status'] = "

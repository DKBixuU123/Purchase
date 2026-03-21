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

# 3. DATA STORAGE (Session State)
if 'rfq_master' not in st.session_state:
    st.session_state['rfq_master'] = []
if 'quotes_master' not in st.session_state:
    st.session_state['quotes_master'] = {}
if 'pr_master' not in st.session_state:
    st.session_state['pr_master'] = []

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
        st.table(df_rfq.iloc[::-1]) # Newest on top
    else:
        st.info("No records found.")
    
    st.divider()

    # --- PHASE 1: PPC / END USER (Raise RFQ & Raise PR) ---
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
                if st.form_submit_button("Submit RFQ"):
                    rfq_id = f"RFQ-{len(st.session_state['rfq_master']) + 101}"
                    st.session_state['rfq_master'].append({
                        "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                        "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                        "Required": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote"
                    })
                    st.success(f"✅ {rfq_id} Raised!")
                    st.rerun()

        with tab2:
            # Show RFQs where CS is already generated
            cs_ready = [r['RFQ ID'] for r in st.session_state['rfq_master'] if r['Status'] == "CS Generated"]
            if cs_ready:
                sel_rfq = st.selectbox("Select RFQ to Raise PR", cs_ready)
                # Show the quotes for this RFQ so user can see L1
                df_q = pd.DataFrame(st.session_state['quotes_master'][sel_rfq])
                st.write("### Comparison Results")
                st.table(df_q)
                
                with st.form("pr_form"):
                    chosen_vendor = st.selectbox("Select Recommended Vendor", df_q['Supplier'].unique())
                    justification = st.text_area("Reason for Selection / Justification")
                    if st.form_submit_button("Submit PR for Approval"):
                        # Update RFQ status
                        for r in st.session_state['rfq_master']:
                            if r['RFQ ID'] == sel_rfq:
                                r['Status'] = "PR Pending Approval"
                                r['Vendor'] = chosen_vendor
                        st.success(f"PR for {sel_rfq} sent for Approval!")
                        st.rerun()
            else:
                st.info("No Comparison Statements ready for PR raising.")

    # --- PHASE 2: PURCHASER (Quotes & CS Generation) ---
    if user == "Purchaser":
        st.header("📥 Purchaser: Arrange Supplier Quotations")
        pending_rfqs = [r['RFQ ID'] for r in st.session_state['rfq_master'] if r['Status'] == "Pending Quote"]
        
        if pending_rfqs:
            sel_id = st.selectbox("Add Quotes for:", pending_rfqs)
            with st.form("q_form", clear_on_submit=True):
                v1, v2, v3 = st.columns(3)
                with v1: v_name = st.text_input("Supplier Name")
                with v2: v_price = st.number_input("Unit Price", min_value=0.0)
                with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                if st.form_submit_button("Save Quote"):
                    if sel_id not in st.session_state['quotes_master']: st.session_state['quotes_master'][sel_id] = []
                    st.session_state['quotes_master'][sel_id].append({
                        "Supplier": v_name, "Rate": v_price, "Disc%": v_disc, "Net Price": v_price * (1 - v_disc/100)
                    })
                    st.rerun()
            
            if sel_id in st.session_state['quotes_master']:
                st.table(pd.DataFrame(st.session_state['quotes_master'][sel_id]))
                if st.button("Finalize Comparison (Generate CS)"):
                    for r in st.session_state['rfq_master']:
                        if r['RFQ ID'] == sel_id: r['Status'] = "CS Generated"
                    st.success("CS Generated! Moving to End User for PR.")
                    st.rerun()
        else:
            st.info("No RFQs pending quotes.")

    # --- PHASE 3: APPROVAL (HOD / GM / Finance / CEO) ---
    if user in ["Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("⚖️ PR Approval Portal")
        to_approve = [r for r in st.session_state['rfq_master'] if r['Status'] == "PR Pending Approval"]
        
        if to_approve:
            for req in to_approve:
                with st.expander(f"Review PR: {req['RFQ ID']} - {req['Item']}", expanded=True):
                    st.write(f"**Vendor:** {req['Vendor']} | **Qty:** {req['Qty']} | **Dept:** {req['Dept']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve {req['RFQ ID']}", key=f"app_{req['RFQ ID']}"):
                            req['Status'] = "Approved (Ready for SAP B1)"
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject {req['RFQ ID']}", key=f"rej_{req['RFQ ID']}"):
                            req['Status'] = "Rejected"
                            st.rerun()
        else:
            st.info("No PRs waiting for your approval.")

else:
    st.info("👈 Please login from the sidebar.")

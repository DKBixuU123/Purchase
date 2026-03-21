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

# 3. PERMANENT-STYLE STORAGE (Session State)
if 'rfq_master' not in st.session_state:
    st.session_state['rfq_master'] = []
if 'quotes_master' not in st.session_state:
    st.session_state['quotes_master'] = {}

# --- LOGIN ---
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
    
    # DASHBOARD - Visible to All (Shows history)
    st.subheader("📋 RFQ Status & History")
    if st.session_state['rfq_master']:
        st.dataframe(pd.DataFrame(st.session_state['rfq_master']), use_container_width=True)
    else:
        st.info("No RFQs found in history.")
    
    st.divider()

    # PHASE 1: CREATE RFQ (Dept View)
    if user not in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📝 Raise New RFQ")
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
                st.session_state['rfq_master'].append({
                    "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                    "Required Date": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote"
                })
                st.success(f"✅ {rfq_id} Saved!")
                st.rerun()

    # PHASE 2: QUOTATION ENTRY (Purchaser View)
    if user == "Purchaser":
        st.header("📥 Quotation Management")
        rfq_ids = [r['RFQ ID'] for r in st.session_state['rfq_master']]
        
        if rfq_ids:
            sel_id = st.selectbox("Select RFQ to add Quotes", rfq_ids)
            # PULL DATA FROM RFQ
            rfq_data = next(i for i in st.session_state['rfq_master'] if i["RFQ ID"] == sel_id)
            
            st.warning(f"📌 **Working on:** {rfq_data['Item']} ({rfq_data['Qty']} {rfq_data['UOM']})")
            
            with st.form("q_form", clear_on_submit=True):
                v1, v2, v3 = st.columns(3)
                with v1: v_name = st.text_input("Supplier Name")
                with v2: v_price = st.number_input("Unit Price (Basic)", min_value=0.0)
                with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                
                t1, t2, t3 = st.columns(3)
                with t1: v_terms = st.text_input("Payment Terms")
                with t2: v_lead = st.text_input("Lead Time")
                with t3: v_file = st.file_uploader("Upload Quote", type=['pdf', 'jpg', 'png'])
                
                if st.form_submit_button("➕ Add Supplier to List"):
                    if sel_id not in st.session_state['quotes_master']:
                        st.session_state['quotes_master'][sel_id] = []
                    
                    net = v_price * (1 - v_disc/100)
                    st.session_state['quotes_master'][sel_id].append({
                        "Supplier": v_name, "Basic Price": v_price, "Disc%": v_disc, 
                        "Net Price": net, "Payment": v_terms, "Lead Time": v_lead,
                        "File": v_file.name if v_file else "None"
                    })
                    st.rerun()

            # SHOW RUNNING LIST OF SUPPLIERS FOR THIS RFQ
            if sel_id in st.session_state['quotes_master']:
                st.subheader(f"Current Supplier Quotes for {sel_id}")
                st.table(pd.DataFrame(st.session_state['quotes_master'][sel_id]))

    # PHASE 3: COMPARISON & L1 (Purchaser & Approvers)
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("📊 Comparison Statement (CS)")
        available_ids = list(st.session_state['quotes_master'].keys())
        
        if available_ids:
            cs_id = st.selectbox("Select RFQ for L1 Analysis:", available_ids)
            if st.button("Generate Comparison Statement"):
                df_cs = pd.DataFrame(st.session_state['quotes_master'][cs_id])
                l1_val = df_cs['Net Price'].min()
                
                def highlight_l1(row):
                    return ['background-color: #d1e7dd; font-weight: bold' if row['Net Price'] == l1_val else '' for _ in row]
                
                st.write(f"### Final Comparison for {cs_id}")
                st.table(df_cs.style.apply(highlight_l1, axis=1))
                st.success("🟢 L1 Vendor highlighted in Green.")
        else:
            st.info("Awaiting supplier quotations from the Purchaser.")
else:
    st.info("👈 Please login to view and manage RFQs.")

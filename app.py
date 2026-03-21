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

# 3. PERSISTENT STORAGE LOGIC
# We use 'st.cache_resource' to prevent data loss during a single session logout
@st.cache_resource
def get_global_data():
    return {"rfq_master": [], "quotes_master": {}}

data_store = get_global_data()

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
    st.sidebar.info(f"Logged in as: **{st.session_state['user']}**")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        # We DO NOT clear the data_store here so it stays for the next login
        st.rerun()

# --- MAIN SYSTEM ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    st.title(f"🚀 Procurement Portal")
    
    # --- DASHBOARD (History) ---
    st.header("📋 RFQ Status Tracker")
    if data_store['rfq_master']:
        df_history = pd.DataFrame(data_store['rfq_master'])
        st.table(df_history.iloc[::-1]) # Newest at top
    else:
        st.info("No RFQs found. Old RFQs will appear here once raised.")
    
    st.divider()

    # PHASE 1: DEPARTMENT VIEW (Raise RFQ)
    if user not in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📝 Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item = st.text_input("Item Description")
            with c2: qty = st.number_input("Qty", min_value=0.1)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr"])
            
            r1, r2 = st.columns(2)
            with r1: req_date = st.date_input("Required By", min_value=date.today())
            with r2: remarks = st.text_area("Remarks")
            
            uploaded_doc = st.file_uploader("Upload Drawing/Reference", type=['pdf','jpg','png'])
            
            if st.form_submit_button("Submit RFQ"):
                rfq_id = f"RFQ-{len(data_store['rfq_master']) + 101}"
                data_store['rfq_master'].append({
                    "RFQ ID": rfq_id, 
                    "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                    "Required": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote",
                    "Attachment": uploaded_doc.name if uploaded_doc else "No File"
                })
                st.success(f"✅ {rfq_id} saved! It will now show in the tracker for the Purchaser.")
                st.rerun()

    # PHASE 2: PURCHASER VIEW (Entering Quotations)
    if user == "Purchaser":
        st.header("📥 Purchaser: Arrange Supplier Quotations")
        pending_ids = [r['RFQ ID'] for r in data_store['rfq_master'] if r['Status'] == "Pending Quote"]
        
        if pending_ids:
            sel_id = st.selectbox("Select Pending RFQ to Enter Quotes", pending_ids)
            rfq_data = next(i for i in data_store['rfq_master'] if i["RFQ ID"] == sel_id)
            st.warning(f"📌 Working on: **{rfq_data['Item']}** ({rfq_data['Qty']} {rfq_data['UOM']})")
            
            with st.form("quote_entry"):
                v1, v2, v3 = st.columns(3)
                with v1: v_name = st.text_input("Supplier Name")
                with v2: v_price = st.number_input("Unit Price", min_value=0.0)
                with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                
                t1, t2 = st.columns(2)
                with t1: v_terms = st.text_input("Payment Terms")
                with t2: v_lead = st.text_input("Lead Time")
                
                if st.form_submit_button("Save Supplier Quote"):
                    if sel_id not in data_store['quotes_master']:
                        data_store['quotes_master'][sel_id] = []
                    
                    net = v_price * (1 - v_disc/100)
                    data_store['quotes_master'][sel_id].append({
                        "Supplier": v_name, "Rate": v_price, "Disc%": v_disc, 
                        "Net Price": net, "Payment": v_terms, "Lead Time": v_lead
                    })
                    st.success(f"Quote for {v_name} saved!")
                    st.rerun()

            if sel_id in data_store['quotes_master']:
                st.subheader(f"Saved Quotes for {sel_id}")
                st.table(pd.DataFrame(data_store['quotes_master'][sel_id]))
        else:
            st.info("No RFQs are currently pending for quotes.")

    # PHASE 3: COMPARISON
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.divider()
        st.header("📊 Final Comparison & L1")
        ready_ids = list(data_store['quotes_master'].keys())
        
        if ready_ids:
            cs_id = st.selectbox("Select RFQ for Comparison", ready_ids)
            if st.button("Generate CS"):
                df_cs = pd.DataFrame(data_store['quotes_master'][cs_id])
                l1_val = df_cs['Net Price'].min()
                st.table(df_cs.style.apply(lambda x: ['background: #d1e7dd' if x['Net Price'] == l1_val else '' for i in x], axis=1))
        else:
            st.write("Awaiting quotes from Purchaser.")
else:
    st.info("👈 Please login. Note: Refreshing the browser will still wipe data until we connect Google Sheets.")

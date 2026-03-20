import streamlit as st
import pandas as pd
from datetime import date

# Page Setup
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 1. USER DATABASE
user_db = {
    "End User / PPC": "ppc123", "Purchaser": "buy123", "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123", "Finance Head": "fin123", "CEO / MD": "ceo123",
    "PE & Facility": "pe123", "Hr & Admin": "hr123", "Stores": "store123",
    "Engineering": "eng123", "IT": "it123"
}

# --- DATA STORAGE ---
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

# --- MAIN APP ---
if st.session_state['logged_in']:
    user = st.session_state['user']
    
    # --- DASHBOARD (History) ---
    st.title(f"🚀 Procurement Dashboard")
    st.subheader("📋 RFQ Status Tracker")
    if st.session_state['rfq_master']:
        df_master = pd.DataFrame(st.session_state['rfq_master'])
        st.dataframe(df_master, use_container_width=True)
    else:
        st.info("No RFQs found.")
    
    st.divider()

    # --- PHASE 1: CREATE RFQ (Dept View) ---
    if user not in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📝 Step 1: Raise New RFQ")
        with st.form("rfq_form", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1: item = st.text_input("Item Description")
            with c2: qty = st.number_input("Qty", min_value=0.1)
            with c3: uom = st.selectbox("UOM", ["Nos", "Kg", "Mtr", "Set", "Ltr", "Box"])
            
            r1, r2 = st.columns(2)
            with r1: req_date = st.date_input("Required By", min_value=date.today())
            with r2: remarks = st.text_area("Special Instructions/Remarks")
            
            if st.form_submit_button("Submit RFQ"):
                rfq_id = f"RFQ-{len(st.session_state['rfq_master']) + 101}"
                st.session_state['rfq_master'].append({
                    "RFQ ID": rfq_id, "Date": date.today().strftime("%d-%m-%Y"),
                    "Item": item, "Qty": qty, "UOM": uom, "Dept": user, 
                    "Required Date": req_date.strftime("%d-%m-%Y"), "Status": "Pending Quote"
                })
                st.success(f"✅ {rfq_id} submitted!")
                st.rerun()

    # --- PHASE 2: PURCHASER ACTION ---
    if user == "Purchaser":
        st.header("📥 Step 2: Arrange Quotations")
        pending_rfqs = [r for r in st.session_state['rfq_master'] if r['Status'] == "Pending Quote"]
        
        if pending_rfqs:
            # Select RFQ
            rfq_options = {r['RFQ ID']: r for r in pending_rfqs}
            selected_id = st.selectbox("Select RFQ to add Quote", list(rfq_options.keys()))
            curr_rfq = rfq_options[selected_id]

            # 1. AUTO-FETCH DATA FROM RFQ
            st.info(f"**Material:** {curr_rfq['Item']} | **Qty:** {curr_rfq['Qty']} | **UOM:** {curr_rfq['UOM']}")

            with st.expander(f"Add Supplier Quote for {selected_id}", expanded=True):
                with st.form("q_form", clear_on_submit=True):
                    v1, v2 = st.columns(2)
                    with v1: supplier = st.text_input("Supplier Name")
                    with v2: rate = st.number_input("Unit Rate (Basic)", min_value=0.0)
                    
                    d1, d2, d3 = st.columns(3)
                    with d1: discount = st.number_input("Discount %", min_value=0.0)
                    with d2: p_terms = st.text_input("Payment Terms")
                    with d3: l_time = st.text_input("Lead Time")
                    
                    q_file = st.file_uploader("Upload Supplier Quote (PDF/JPG)", type=["pdf", "jpg", "png"])
                    
                    if st.form_submit_button("Save Quote Details"):
                        if selected_id not in st.session_state['quotes_master']:
                            st.session_state['quotes_master'][selected_id] = []
                        
                        net = rate * (1 - discount/100)
                        st.session_state['quotes_master'][selected_id].append({
                            "Supplier": supplier, "Basic Rate": rate, "Disc %": discount, 
                            "Net Price": net, "Payment": p_terms, "Lead Time": l_time,
                            "Doc": q_file.name if q_file else "No File"
                        })
                        st.success(f"Quote for {supplier} added!")

            # 2. SHOW ENTERED QUOTES BELOW FORM
            if selected_id in st.session_state['quotes_master']:
                st.subheader(f"Current Quotes for {selected_id}")
                st.table(pd.DataFrame(st.session_state['quotes_master'][selected_id]))
        else:
            st.write("No pending RFQs.")

    # --- PHASE 3: COMPARISON STATEMENT ---
    if user in ["Purchaser", "Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("📊 Step 3: Comparison Statement (CS)")
        available_ids = list(st.session_state['quotes_master'].keys())
        
        if available_ids:
            cs_id = st.selectbox("Select RFQ for Comparison", available_ids)
            if st.button("Generate CS & Indicate L1"):
                df_cs = pd.DataFrame(st.session_state['quotes_master'][cs_id])
                l1_val = df_cs['Net Price'].min()
                
                def highlight_l1(row):
                    return ['background-color: #d1e7dd' if row['Net Price'] == l1_val else '' for _ in row]
                
                st.table(df_cs.style.apply(highlight_l1, axis=1))
                st.success(f"L1 Supplier for {cs_id} highlighted in Green.")
        else:
            st.info("No quotes available to compare yet.")

else:
    st.info("👈 Please login from the sidebar.")

import streamlit as st
import pandas as pd
from datetime import date
import gspread
from google.oauth2.service_account import Credentials

# 1. PAGE CONFIG
st.set_page_config(page_title="Procurement ERP Pro", layout="wide")

# 2. GOOGLE SHEETS CONNECTION
# PASTE YOUR URL HERE
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Zks8dDcskV1EvEslYFDmPhXQodC3VHsL7r_VZBhCCl8/edit?gid=509050112#gid=509050112" 

def get_gsheet():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Ensure your JSON key is in Streamlit Secrets as [gcp_service_account]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(SHEET_URL)
        return sheet
    except Exception as e:
        return None

db = get_gsheet()

# 3. USER ACCESS CONTROL
user_db = {
    "End User / PPC": "ppc123", "Purchaser": "buy123", "Purchase HOD": "hod123",
    "Sr. GM Commercial": "gm123", "Finance Head": "fin123", "CEO / MD": "ceo123"
}

# 4. SESSION STATE INITIALIZATION
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'show_rfq_form' not in st.session_state: st.session_state['show_rfq_form'] = True

# --- LOGIN LOGIC ---
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 Secure Login")
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
if st.session_state['logged_in'] and db:
    user = st.session_state['user']
    st.title(f"🚀 Procurement Portal")
    
    # LOAD MASTER DATA FROM GOOGLE SHEETS
    rfq_sheet = db.worksheet("RFQs")
    all_rfqs = pd.DataFrame(rfq_sheet.get_all_records())
    
    # DASHBOARD
    st.header("📋 RFQ & PR Status Tracker")
    if not all_rfqs.empty:
        st.table(all_rfqs.iloc[::-1])
    else:
        st.info("No records found in Google Sheets.")
    
    st.divider()

    # PHASE 1: PPC / END USER (Raise Multiple RFQs & PR)
    if user == "End User / PPC":
        tab1, tab2 = st.tabs(["📝 Raise New RFQ", "📤 Raise PR"])
        
        with tab1:
            if st.session_state['show_rfq_form']:
                st.header("Step 1: Create RFQ")
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
                        new_id = f"RFQ-{101 + len(all_rfqs)}"
                        new_row = [new_id, date.today().strftime("%d-%m-%Y"), item, qty, uom, user, 
                                   req_date.strftime("%d-%m-%Y"), "Pending Quote", doc.name if doc else "No File"]
                        rfq_sheet.append_row(new_row)
                        st.session_state['show_rfq_form'] = False
                        st.rerun()
            else:
                st.success("✅ RFQ Submitted Successfully to Google Sheets!")
                if st.button("➕ Create Another RFQ"):
                    st.session_state['show_rfq_form'] = True
                    st.rerun()

        with tab2:
            # PR Section: Only show RFQs where CS is Generated
            if not all_rfqs.empty:
                cs_ready = all_rfqs[all_rfqs['Status'] == "CS Generated"]['RFQ ID'].tolist()
                if cs_ready:
                    sel_pr = st.selectbox("Select RFQ to Convert to PR", cs_ready)
                    if st.button("Raise PR for Approval"):
                        cell = rfq_sheet.find(sel_pr)
                        rfq_sheet.update_cell(cell.row, 8, "PR Pending Approval")
                        st.success(f"PR for {sel_pr} sent to HOD!")
                        st.rerun()
                else:
                    st.info("No Comparison Statements ready for PR yet.")

    # PHASE 2: PURCHASER (Add Quotes & Finalize CS)
    if user == "Purchaser":
        st.header("📥 Purchaser: Arrange Supplier Quotations")
        if not all_rfqs.empty:
            pending_ids = all_rfqs[all_rfqs['Status'] == "Pending Quote"]['RFQ ID'].tolist()
            
            if pending_ids:
                sel_id = st.selectbox("Select Pending RFQ to Enter Quotes", pending_ids)
                rfq_data = all_rfqs[all_rfqs['RFQ ID'] == sel_id].iloc[0]
                
                st.warning(f"📌 Working on: **{rfq_data['Item']}** ({rfq_data['Qty']} {rfq_data['UOM']})")
                
                with st.form("quote_form", clear_on_submit=True):
                    v1, v2, v3 = st.columns(3)
                    with v1: v_name = st.text_input("Supplier Name")
                    with v2: v_price = st.number_input("Unit Price", min_value=0.0)
                    with v3: v_disc = st.number_input("Discount %", min_value=0.0)
                    if st.form_submit_button("Save Supplier Quote"):
                        db.worksheet("Quotes").append_row([sel_id, v_name, v_price, v_disc, v_price * (1 - v_disc/100)])
                        st.success(f"Quote for {v_name} saved!")
                        st.rerun()

                if st.button("Finalize Comparison (CS)"):
                    cell = rfq_sheet.find(sel_id)
                    rfq_sheet.update_cell(cell.row, 8, "CS Generated")
                    st.success("Comparison Statement Generated! It is now visible to the End User.")
                    st.rerun()
            else:
                st.info("No pending RFQs found.")

    # PHASE 3: APPROVAL (HOD/Finance/CEO)
    if user in ["Purchase HOD", "Sr. GM Commercial", "Finance Head", "CEO / MD"]:
        st.header("⚖️ PR Approval Portal")
        if not all_rfqs.empty:
            to_approve = all_rfqs[all_rfqs['Status'] == "PR Pending Approval"]
            if not to_approve.empty:
                for index, row in to_approve.iterrows():
                    with st.expander(f"Review PR: {row['RFQ ID']} - {row['Item']}"):
                        if st.button(f"Approve {row['RFQ ID']}", key=f"app_{row['RFQ ID']}"):
                            cell = rfq_sheet.find(row['RFQ ID'])
                            rfq_sheet.update_cell(cell.row, 8, "Approved (Ready for SAP B1)")
                            st.rerun()
            else:
                st.info("No PRs waiting for your approval.")

else:
    st.warning("👈 Please login and check Google Sheet URL connection.")

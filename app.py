import streamlit as st
import pandas as pd

# --- 1. INITIALIZATION (Fixes the AttributeError) ---
if 'role' not in st.session_state:
    st.session_state.role = None

if 'rfq_data' not in st.session_state:
    # Starting with some sample data to test the flow
    st.session_state.rfq_data = [
        {"id": "RFQ-001", "item": "Laptop", "dept": "IT", "status": "CS_GENERATED", "l1_supplier": "Dell Store", "l1_price": 55000},
        {"id": "RFQ-002", "item": "Office Chairs", "dept": "HR & Admin", "status": "OPEN", "l1_supplier": None, "l1_price": None}
    ]

# --- 2. LOGIN SYSTEM ---
if st.session_state.role is None:
    st.title("🏗️ Industrial Procurement Portal")
    st.subheader("Please Login")
    user_role = st.selectbox("Select Your Role:", ["Purchaser", "End User", "HOD", "CEO"])
    
    if st.button("Login"):
        st.session_state.role = user_role
        st.rerun()
    st.stop()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title(f"Logged in as: {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.role = None
    st.rerun()

# --- 4. ROLE-BASED DASHBOARDS ---

# --- PURCHASER VIEW ---
if st.session_state.role == "Purchaser":
    st.header("Purchaser Dashboard")
    
    tab1, tab2 = st.tabs(["Manage RFQs", "Approved PRs for SAP"])
    
    with tab1:
        st.write("### Current RFQs")
        for rfq in st.session_state.rfq_data:
            if rfq['status'] == 'OPEN':
                st.info(f"RFQ {rfq['id']}: {rfq['item']} is awaiting quotes.")
                if st.button(f"Generate CS for {rfq['id']}"):
                    rfq['status'] = 'CS_GENERATED'
                    rfq['l1_supplier'] = "Supplier A" # Example logic
                    rfq['l1_price'] = 1000
                    st.success("CS Generated! Moving to End User for PR.")
                    st.rerun()
    
    with tab2:
        st.write("### PRs Ready for SAP B1 Entry")
        approved = [r for r in st.session_state.rfq_data if r['status'] == 'PR_APPROVED']
        if approved:
            st.table(approved)
        else:
            st.write("No approved PRs yet.")

# --- END USER VIEW ---
elif st.session_state.role == "End User":
    st.header("End User PR Panel")
    st.write("Review the Comparative Statement (CS) and raise a Purchase Requisition.")
    
    pending_cs = [r for r in st.session_state.rfq_data if r['status'] == 'CS_GENERATED']
    
    if not pending_cs:
        st.info("No Comparative Statements are ready for your review.")
    else:
        for rfq in pending_cs:
            with st.expander(f"Review CS for {rfq['item']} ({rfq['id']})"):
                st.write(f"**Best Price Found:** {rfq['l1_price']}")
                st.write(f"**Recommended Supplier:** {rfq['l1_supplier']}")
                
                if st.button(f"Raise PR for {rfq['id']}", key=f"pr_{rfq['id']}"):
                    rfq['status'] = 'PR_PENDING_APPROVAL'
                    st.success("PR Raised! Sent to HOD/CEO for approval.")
                    st.rerun()

# --- APPROVER VIEW (HOD/CEO) ---
elif st.session_state.role in ["HOD", "CEO"]:
    st.header("Approval Dashboard")
    
    pending_approval = [r for r in st.session_state.rfq_data if r['status'] == 'PR_PENDING_APPROVAL']
    
    if not pending_approval:
        st.write("No PRs awaiting approval.")
    else:
        for rfq in pending_approval:
            st.warning(f"PR Request: {rfq['item']} for {rfq['dept']}")
            if st.button(f"Approve {rfq['id']}", key=f"app_{rfq['id']}"):
                rfq['status'] = 'PR_APPROVED'
                st.success(f"PR {rfq['id']} Approved!")
                st.rerun()

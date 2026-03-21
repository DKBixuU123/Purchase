import streamlit as st
import pandas as pd

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Procurement Portal", layout="wide")

# --- 2. INITIALIZATION ---
if 'role' not in st.session_state:
    st.session_state.role = None

if 'rfq_data' not in st.session_state:
    # Sample data to visualize the flow
    st.session_state.rfq_data = [
        {"id": "RFQ-101", "item": "Steel Pipes", "dept": "Engineering", "status": "CS_GENERATED", "l1_price": 45000, "l1_vendor": "Tata Steel"},
        {"id": "RFQ-102", "item": "Laptops", "dept": "IT", "status": "OPEN", "l1_price": None, "l1_vendor": None}
    ]

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("⚙️ System Menu")
    
    if st.session_state.role is None:
        st.subheader("Login")
        user_role = st.selectbox("Select Role", ["Purchaser", "End User", "HOD", "CEO"])
        if st.button("Login", use_container_width=True):
            st.session_state.role = user_role
            st.rerun()
    else:
        st.info(f"Logged in as: **{st.session_state.role}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()
        
        st.divider()
        st.write("Current Workflow Stage:")
        if st.session_state.role == "Purchaser":
            menu = st.radio("Navigation", ["Manage RFQs", "Approved PRs (for SAP)"])
        else:
            menu = st.radio("Navigation", ["Pending Actions", "History"])

# --- 4. MAIN INTERFACE ---
st.title("🏗️ Industrial Procurement Portal")

if st.session_state.role is None:
    st.warning("Please login from the sidebar to access the portal.")
    st.stop()

# --- PURCHASER LOGIC ---
if st.session_state.role == "Purchaser":
    if menu == "Manage RFQs":
        st.header("Purchaser Dashboard - RFQ Management")
        for rfq in st.session_state.rfq_data:
            if rfq['status'] == 'OPEN':
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    col1.write(f"**{rfq['id']}**: {rfq['item']} ({rfq['dept']})")
                    if col2.button("Generate CS", key=rfq['id']):
                        rfq['status'] = 'CS_GENERATED'
                        rfq['l1_price'] = 5000 # Simulated logic
                        rfq['l1_vendor'] = "Default Vendor"
                        st.rerun()
    
    elif menu == "Approved PRs (for SAP)":
        st.header("Approved PRs for SAP B1 Entry")
        approved = [r for r in st.session_state.rfq_data if r['status'] == 'PR_APPROVED']
        if approved:
            st.dataframe(pd.DataFrame(approved), use_container_width=True)
            st.success("The items above are ready to be manually entered into SAP B1.")
        else:
            st.info("No approved PRs currently waiting for SAP entry.")

# --- END USER LOGIC ---
elif st.session_state.role == "End User":
    st.header("End User - PR Generation")
    cs_list = [r for r in st.session_state.rfq_data if r['status'] == 'CS_GENERATED']
    
    if not cs_list:
        st.info("No CS ready for review.")
    else:
        for rfq in cs_list:
            with st.expander(f"Review Comparison for {rfq['item']}"):
                st.write(f"**L1 Vendor:** {rfq['l1_vendor']}")
                st.write(f"**L1 Price:** {rfq['l1_price']}")
                if st.button(f"Raise PR for {rfq['id']}"):
                    rfq['status'] = 'PR_PENDING_APPROVAL'
                    st.success("PR Raised! Sent for Approval.")
                    st.rerun()

# --- APPROVER LOGIC ---
elif st.session_state.role in ["HOD", "CEO"]:
    st.header("Approval Center")
    to_approve = [r for r in st.session_state.rfq_data if r['status'] == 'PR_PENDING_APPROVAL']
    
    if not to_approve:
        st.info("Everything is caught up! No PRs pending.")
    else:
        for rfq in to_approve:
            with st.container(border=True):
                st.write(f"**Request from {rfq['dept']}**: {rfq['item']} (L1: {rfq['l1_price']})")
                if st.button("Approve PR", key=f"app_{rfq['id']}"):
                    rfq['status'] = 'PR_APPROVED'
                    st.rerun()

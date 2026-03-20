import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Procurement ERP", layout="wide")

# --- HIERARCHY SETUP ---
roles = {
    "End User / PPC": 1,
    "Purchaser": 2,
    "Purchase HOD": 3,
    "Sr. GM Commercial": 4,
    "Finance Head": 5,
    "CEO / MD": 6
}

# --- SIDEBAR LOGIN ---
st.sidebar.title("🔐 Secure Login")
user_role = st.sidebar.selectbox("Select Your Role", list(roles.keys()))
st.sidebar.success(f"Logged in as: {user_role}")

st.title("📦 Digital Procurement System (RFQ to PR)")
st.markdown(f"**Current Stage:** Step {roles[user_role]} of 6")

# --- STEP 1: RFQ (Visible to End User) ---
if user_role == "End User / PPC":
    st.header("Step 1: Raise New RFQ")
    with st.form("rfq_form"):
        item = st.text_input("Item Description")
        qty = st.number_input("Quantity", min_value=1)
        dept = st.selectbox("Department", ["Production", "PPC", "Maintenance"])
        submitted = st.form_submit_button("Submit RFQ to Purchase")
        if submitted:
            st.info(f"RFQ for {item} has been sent to the Purchaser.")

# --- STEP 2 & 3: QUOTATIONS & COMPARISON (Visible to Purchaser & Above) ---
if roles[user_role] >= 2:
    st.header("Step 3: Automatic Comparison Statement (CS)")
    
    # Simulated Data
    data = {
        "Supplier": ["Vendor Alpha", "Vendor Beta", "Vendor Gamma"],
        "Price (INR)": [450, 410, 425],
        "Lead Time (Days)": [7, 5, 10],
        "Payment Terms": ["30 Days", "Advance", "45 Days"],
        "Rank": ["L2", "L1", "L3"]
    }
    df = pd.DataFrame(data)

    # Highlight L1 Row automatically
    def highlight_l1(s):
        return ['background-color: #e8f5e9' if s.Rank == 'L1' else '' for _ in s]

    st.table(df.style.apply(highlight_l1, axis=1))
    st.caption("✨ System Note: Vendor Beta is automatically selected as L1 (Lowest Price).")

# --- STEP 4 & 5: PR APPROVAL (Visible to HOD and Seniors) ---
if roles[user_role] >= 3:
    st.header("Step 4 & 5: PR Approval Workflow")
    st.warning(f"ACTION REQUIRED: PR #1002 (Value: ₹ 2.1L) is pending for {user_role} approval.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve PR", use_container_width=True):
            st.success("PR Approved and forwarded to the next level.")
    with col2:
        if st.button("❌ Reject / Query", use_container_width=True):
            st.error("PR Sent back to Purchaser for clarification.")

# --- STEP 6: MIS DASHBOARD (Visible to All) ---
st.divider()
st.header("Step 6: MIS Tracking & Analytics")
m1, m2, m3 = st.columns(3)
m1.metric("Open RFQs", "12", "+2")
m2.metric("Pending PRs", "5", "-1")
m3.metric("Cost Savings", "14.2%", "Target: 10%")

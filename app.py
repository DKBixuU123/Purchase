import streamlit as st

# 1. Logic for the End User to see Generated CS
if st.session_state.role == "End User":
    st.subheader("Pending Purchase Requisitions")
    
    # Filter data where CS is ready but PR isn't raised yet
    pending_pr = [r for r in st.session_state.rfq_data if r['status'] == 'CS_GENERATED']
    
    if not pending_pr:
        st.info("No Comparative Statements ready for PR at the moment.")
    else:
        for rfq in pending_pr:
            with st.expander(f"RFQ: {rfq['id']} - {rfq['item']}"):
                st.write(f"**Selected L1 Supplier:** {rfq['l1_supplier']}")
                st.write(f"**L1 Price:** {rfq['l1_price']}")
                
                if st.button(f"Raise PR for {rfq['id']}", key=rfq['id']):
                    rfq['status'] = 'PR_PENDING_APPROVAL'
                    st.success(f"PR for {rfq['id']} has been sent for approval!")
                    st.rerun()

# 2. Logic for Approver (HOD/CEO)
elif st.session_state.role in ["HOD", "CEO"]:
    st.subheader("PR Approval Dashboard")
    
    to_approve = [r for r in st.session_state.rfq_data if r['status'] == 'PR_PENDING_APPROVAL']
    
    for rfq in to_approve:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**PR Request:** {rfq['item']} from {rfq['department']}")
        with col2:
            if st.button("Approve", key=f"app_{rfq['id']}"):
                rfq['status'] = 'PR_APPROVED'
                st.balloons()
                st.rerun()

# 3. Final View for Purchaser (to copy to SAP B1)
if st.session_state.role == "Purchaser":
    st.subheader("Approved PRs (Ready for SAP B1)")
    approved_list = [r for r in st.session_state.rfq_data if r['status'] == 'PR_APPROVED']
    
    if approved_list:
        st.table(approved_list)
        st.caption("Copy the details above into SAP B1 to generate the official PO.")

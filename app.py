import streamlit as st
import pandas as pd

# --- 1. INITIALIZATION (Prevents AttributeError) ---
if 'rfq_data' not in st.session_state:
    st.session_state.rfq_data = []

if 'departments' not in st.session_state:
    st.session_state.departments = ["PE & Facility", "HR & Admin", "Stores", "Engineering", "IT"]

# --- 2. MAIN NAVIGATION ---
st.title("🏗️ Industrial Procurement Portal")
menu = st.sidebar.selectbox("Main Menu", ["Raise RFQ", "View Dashboard / Generate CS"])

# --- 3. RAISE RFQ MODULE ---
if menu == "Raise RFQ":
    st.header("Raise New Request for Quotation")
    with st.form("rfq_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input("Item Description")
            qty = st.number_input("Quantity", min_value=1)
        with col2:
            dept = st.selectbox("Department", st.session_state.departments)
            deadline = st.date_input("Target Date")
        
        submit = st.form_submit_button("Submit RFQ")
        
        if submit and item_name:
            new_rfq = {
                "id": f"RFQ-{len(st.session_state.rfq_data) + 101}",
                "item": item_name,
                "qty": qty,
                "dept": dept,
                "status": "Open",
                "quotes": [] # To be filled in later
            }
            st.session_state.rfq_data.append(new_rfq)
            st.success(f"RFQ {new_rfq['id']} raised successfully!")

# --- 4. DASHBOARD & CS MODULE ---
elif menu == "View Dashboard / Generate CS":
    st.header("Procurement Dashboard")
    
    if not st.session_state.rfq_data:
        st.info("No RFQs found. Start by raising a request.")
    else:
        # Create a summary table
        df = pd.DataFrame(st.session_state.rfq_data)
        st.dataframe(df[['id', 'item', 'qty', 'dept', 'status']], use_container_width=True)
        
        st.divider()
        st.subheader("Generate Comparative Statement (CS)")
        
        # Select an RFQ to process
        rfq_to_process = st.selectbox("Select RFQ for Comparison", 
                                      [r['id'] for r in st.session_state.rfq_data if r['status'] == "Open"])
        
        if rfq_to_process:
            selected_rfq = next(item for item in st.session_state.rfq_data if item["id"] == rfq_to_process)
            
            st.write(f"Processing: **{selected_rfq['item']}**")
            
            # Simple simulation of quote entry
            with st.expander("Enter Supplier Quotes"):
                s1_price = st.number_input("Supplier A Price", key="s1")
                s2_price = st.number_input("Supplier B Price", key="s2")
                
                if st.button("Finalize CS & Identify L1"):
                    l1_price = min(s1_price, s2_price)
                    l1_vendor = "Supplier A" if s1_price <= s2_price else "Supplier B"
                    
                    # Update data
                    for r in st.session_state.rfq_data:
                        if r['id'] == rfq_to_process:
                            r['status'] = "CS Finalized"
                            r['l1'] = l1_vendor
                            r['price'] = l1_price
                    
                    st.success(f"CS Completed! L1 is {l1_vendor} at {l1_price}")
                    st.rerun()

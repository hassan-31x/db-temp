import streamlit as st
import pandas as pd
from pages import blood_drive
from db import cursor, connection

def hospital_page():
    st.title("Hospital Dashboard")
    
    # menu = ["Profile", "Blood Requests", "Appointments", "Inventory", "Dispatch", "Blood Drives"]
    menu = ["Profile", "Blood Requests", "Inventory", "Dispatch"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Profile":
        profile()
    elif choice == "Blood Requests":
        blood_requests()
    elif choice == "Appointments":
        appointments()
    elif choice == "Inventory":
        inventory()
    elif choice == "Dispatch":
        dispatch()
    elif choice == "Blood Drives":
        blood_drive.blood_drive_page()

def profile():
    st.subheader("Hospital Profile")
    
    # Fetch current hospital information
    query = """
    SELECT h.id, h.name, h.location, h.contactInformation, h.bloodBankInventoryId,
           FORMAT(h.createdAt, 'yyyy-MM-dd') as joinDate
    FROM Hospital h
    JOIN [User] u ON h.id = u.associatedHospitalId
    WHERE u.id = ?
    """
    cursor.execute(query, (st.session_state.user['id'],))
    hospital_info = cursor.fetchone()
    
    if hospital_info:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Edit Hospital Information")
            with st.form("edit_hospital_info_form"):
                new_name = st.text_input("Hospital Name", value=hospital_info[1])
                new_location = st.text_area("Location", value=hospital_info[2])
                new_contact = st.text_area("Contact Information", value=hospital_info[3])
                submit_button = st.form_submit_button("Update Hospital Information")
                
                if submit_button:
                    try:
                        update_query = """
                        UPDATE h
                        SET h.name = ?, 
                            h.location = ?,
                            h.contactInformation = ?,
                            h.updatedAt = GETDATE()
                        FROM Hospital h
                        JOIN [User] u ON h.id = u.associatedHospitalId
                        WHERE u.id = ?
                        """
                        cursor.execute(update_query, (new_name, new_location, new_contact, st.session_state.user['id']))
                        connection.commit()
                        st.success("Hospital information updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating information: {str(e)}")
        
        with col2:
            st.markdown("### Hospital Details")
            st.write("**Registration Date:**", hospital_info[5])
            
            # Show blood bank inventory status
            if hospital_info[4]:  # if bloodBankInventoryId exists
                st.write("**Blood Bank Status:** Active")
                
            else:
                st.write("**Blood Bank Status:** Pending Approval")
                st.info("Your blood bank registration is under review by the administration.")
            
            # Show recent activity
            st.markdown("#### Recent Activity")
            activity_query = """
            SELECT 
                FORMAT(appointmentDate, 'yyyy-MM-dd') as Date,
                COUNT(*) as 'Appointments'
            FROM Appointment
            WHERE hospitalId = ?
            GROUP BY appointmentDate
            ORDER BY appointmentDate DESC
            LIMIT 5
            """
            cursor.execute(activity_query, (hospital_info[0],))
            activity_data = cursor.fetchall()
            print(activity_data)
            
            if activity_data:
                activity_data = [row if isinstance(row, tuple) else tuple(row) for row in activity_data]
                activity_df = pd.DataFrame(activity_data, columns=['Date', 'Appointments'])
                st.table(activity_df)
            else:
                st.write("No recent activity")

def blood_requests():
    st.subheader("Blood Requests")
    
    # First check if hospital is approved
    check_query = """
    SELECT h.bloodBankInventoryId, h.id
    FROM Hospital h
    JOIN [User] u ON h.id = u.associatedHospitalId
    WHERE u.id = ?
    """
    cursor.execute(check_query, (st.session_state.user['id'],))
    hospital_status = cursor.fetchone()
    
    if not hospital_status or not hospital_status[0]:
        st.warning("Your hospital is not approved yet. Blood request functionality will be available after approval.")
        return
        
    # If approved, show existing requests
    hospital_id = hospital_status[1]
    query = """
    SELECT 
        bt.bloodType as 'Blood Type',
        br.requestedQuantity as 'Requested Units',
        br.fulfilledQuantity as 'Fulfilled Units',
        br.urgencyLevel as 'Urgency',
        br.requestStatus as 'Status',
        FORMAT(br.createdAt, 'yyyy-MM-dd') as 'Request Date'
    FROM BloodRequest br
    JOIN BloodType bt ON br.bloodTypeId = bt.id
    WHERE br.hospitalId = ?
    ORDER BY br.createdAt DESC
    """
    cursor.execute(query, (hospital_id,))
    data = cursor.fetchall()
    data = [row if isinstance(row, tuple) else tuple(row) for row in data]
    requests = pd.DataFrame(data, 
                          columns=['Blood Type', 'Requested Units', 'Fulfilled Units', 
                                 'Urgency', 'Status', 'Request Date'])
    
    if not requests.empty:
        st.markdown("### Current Requests")
        st.table(requests)
    else:
        st.info("No blood requests found.")
    
    # Add new request form
    st.markdown("### New Blood Request")
    with st.form("blood_request_form"):
        # Get blood types for dropdown
        cursor.execute("SELECT id, bloodType FROM BloodType")
        blood_types = {bt[1]: bt[0] for bt in cursor.fetchall()}
        
        selected_blood_type = st.selectbox("Blood Type", list(blood_types.keys()))
        quantity = st.number_input("Quantity Required (units)", min_value=1, max_value=100)
        urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High", "Critical"])
        
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            try:
                insert_query = """
                INSERT INTO BloodRequest (
                    hospitalId,
                    bloodTypeId,
                    urgencyLevel,
                    requestStatus,
                    requestedQuantity,
                    fulfilledQuantity,
                    createdAt,
                    updatedAt
                ) VALUES (?, ?, ?, 'Pending', ?, 0, GETDATE(), GETDATE())
                """
                cursor.execute(insert_query, 
                             (hospital_id, blood_types[selected_blood_type], 
                              urgency, quantity))
                connection.commit()
                st.success("Blood request submitted successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error submitting request: {str(e)}")

def appointments():
    st.subheader("Appointments")
    query = """
    SELECT d.name as 'Donor Name',
           bt.bloodType as 'Blood Type',
           FORMAT(a.appointmentDate, 'yyyy-MM-dd') as Date,
           FORMAT(a.appointmentTime, 'HH:mm') as Time,
           a.status as Status
    FROM Appointment a
    JOIN Donor d ON a.donorId = d.id
    JOIN BloodType bt ON d.bloodTypeId = bt.id
    JOIN Hospital h ON a.hospitalId = h.id
    JOIN [User] u ON h.id = u.associatedHospitalId
    WHERE u.id = ?
    ORDER BY a.appointmentDate, a.appointmentTime
    """
    cursor.execute(query, (st.session_state.user['id'],))
    data = cursor.fetchall()
    data = [row if isinstance(row, tuple) else tuple(row) for row in data]
    appointments = pd.DataFrame(data, 
                              columns=['Donor Name', 'Blood Type', 'Date', 'Time', 'Status'])
    st.table(appointments)

def inventory():
    st.subheader("Blood Bank Inventory")
    
    # First check if hospital is approved
    check_query = """
    SELECT h.bloodBankInventoryId, h.id
    FROM Hospital h
    JOIN [User] u ON h.id = u.associatedHospitalId
    WHERE u.id = ?
    """
    cursor.execute(check_query, (st.session_state.user['id'],))
    hospital_status = cursor.fetchone()
    
    if not hospital_status or not hospital_status[0]:
        st.warning("Your hospital is not approved yet. Inventory management will be available after approval.")
        return
        
    hospital_id = hospital_status[1]
    
    # Show current inventory
    query = """
    SELECT 
        bt.id as blood_type_id,
        bt.bloodType as 'Blood Type',
        bbi.quantityInStock as 'Units Available',
        FORMAT(bbi.expirationDate, 'yyyy-MM-dd') as 'Expiration Date',
        bbi.id as inventory_id
    FROM BloodBankInventory bbi
    JOIN BloodType bt ON bbi.bloodTypeId = bt.id
    WHERE bbi.hospitalId = ?
    """
    cursor.execute(query, (hospital_id,))
    inventory_data = cursor.fetchall()
    
    if inventory_data:
        st.markdown("### Current Inventory")
        inventory_data = [row if isinstance(row, tuple) else tuple(row) for row in inventory_data]
        inventory_df = pd.DataFrame(inventory_data, 
                                  columns=['blood_type_id', 'Blood Type', 'Units Available', 
                                         'Expiration Date', 'inventory_id'])
        # Display only relevant columns
        display_df = inventory_df[['Blood Type', 'Units Available', 'Expiration Date']]
        st.table(display_df)
    else:
        st.info("No inventory records found.")
    
    # Add/Update inventory form
    st.markdown("### Update Inventory")
    with st.form("update_inventory_form"):
        # Get blood types for dropdown
        cursor.execute("SELECT id, bloodType FROM BloodType")
        blood_types = {bt[1]: bt[0] for bt in cursor.fetchall()}
        
        selected_blood_type = st.selectbox("Blood Type", list(blood_types.keys()))
        quantity = st.number_input("Quantity in Stock", min_value=0, max_value=1000)
        expiration_date = st.date_input("Expiration Date")
        
        submitted = st.form_submit_button("Update Inventory")
        
        if submitted:
            try:
                # Check if inventory entry exists for this blood type
                check_inventory_query = """
                SELECT id FROM BloodBankInventory 
                WHERE hospitalId = ? AND bloodTypeId = ?
                """
                cursor.execute(check_inventory_query, (hospital_id, blood_types[selected_blood_type]))
                existing_inventory = cursor.fetchone()
                
                if existing_inventory:
                    # Update existing inventory
                    update_query = """
                    UPDATE BloodBankInventory 
                    SET quantityInStock = ?,
                        expirationDate = ?,
                        updatedAt = GETDATE()
                    WHERE id = ?
                    """
                    cursor.execute(update_query, (quantity, expiration_date, existing_inventory[0]))
                else:
                    # Insert new inventory entry
                    insert_query = """
                    INSERT INTO BloodBankInventory (
                        hospitalId,
                        bloodTypeId,
                        quantityInStock,
                        expirationDate,
                        createdAt,
                        updatedAt
                    ) VALUES (?, ?, ?, ?, GETDATE(), GETDATE())
                    """
                    cursor.execute(insert_query, 
                                 (hospital_id, blood_types[selected_blood_type], 
                                  quantity, expiration_date))
                
                connection.commit()
                st.success("Inventory updated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error updating inventory: {str(e)}")
    
    # Add inventory history or low stock alerts
    if inventory_data:
        st.markdown("### Inventory Alerts")
        low_stock_items = display_df[display_df['Units Available'] < 10]
        if not low_stock_items.empty:
            st.warning("Low Stock Alert!")
            st.table(low_stock_items)
        
        expiring_soon = display_df[pd.to_datetime(display_df['Expiration Date']) < 
                                 pd.Timestamp.now() + pd.Timedelta(days=30)]
        if not expiring_soon.empty:
            st.warning("Items Expiring Soon!")
            st.table(expiring_soon)

def dispatch():
    st.subheader("Dispatch")
    dispatch_form = st.form("dispatch_form")
    with dispatch_form:
        query = "SELECT bloodType FROM BloodType"
        cursor.execute(query)
        blood_types = [bt[0] for bt in cursor.fetchall()]
        
        blood_type = st.selectbox("Blood Type", blood_types)
        quantity = st.number_input("Quantity", min_value=1, max_value=5)
        destination = st.text_input("Destination")
        submitted = st.form_submit_button("Dispatch Blood")
    
    if submitted:
        # Add dispatch logic here
        st.success(f"Dispatched {quantity} units of {blood_type} blood to {destination}.")
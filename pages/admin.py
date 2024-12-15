import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pages import blood_drive
from db import cursor, connection

def admin_page():
    st.title("Admin Dashboard")
    
    menu = ["User Management", "Hospital Approval", "Blood Bank Inventory", "Reports"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Blood Drives":
        blood_drive.blood_drive_page()
    elif choice == "User Management":
        user_management()
    elif choice == "Hospital Approval":
        hospital_approval()
    elif choice == "Blood Bank Inventory":
        blood_bank_inventory()
    elif choice == "Reports":
        reports()

def user_management():
    st.subheader("User Management")
    query = """
        SELECT u.id, u.username, r.name as Role, u.status as Status
        FROM [User] u
        JOIN Role r ON u.roleId = r.id
    """
    cursor.execute(query)
    data = cursor.fetchall()
    data = [row if isinstance(row, tuple) else tuple(row) for row in data]
    users_df = pd.DataFrame(data, columns=["ID", "Username", "Role", "Status"])
    
    # Display each user with delete button
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Admin & Donor Users")
        for _, user in users_df[users_df['Role'].isin(['Admin', 'Donor'])].iterrows():
            with st.expander(f"{user['Username']} - {user['Role']}"):
                st.write(f"**Role:** {user['Role']}")
                st.write(f"**Status:** {user['Status']}")
                
                # Don't allow admin to delete themselves
                if user['ID'] != st.session_state.user['id']:
                    if st.button("Delete Account", key=f"delete_user_{user['ID']}", type="secondary"):
                        try:
                            if user['Role'] == 'Donor':
                                # Delete donor appointments
                                cursor.execute("""
                                    DELETE FROM Appointment 
                                    WHERE donorId IN (SELECT id FROM Donor WHERE userId = ?)
                                """, (user['ID'],))
                                connection.commit()
                                
                                # Delete donor records
                                cursor.execute("DELETE FROM Donor WHERE userId = ?", (user['ID'],))
                                connection.commit()
                            
                            # Finally delete the user
                            cursor.execute("DELETE FROM [User] WHERE id = ?", (user['ID'],))
                            connection.commit()
                            
                            st.success(f"Account for {user['Username']} has been deleted")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error deleting account: {str(e)}")

    with col2:
        st.markdown("### Hospital Users") 
        for _, user in users_df[users_df['Role'] == 'Hospital'].iterrows():
            with st.expander(f"{user['Username']} - {user['Role']}"):
                st.write(f"**Role:** {user['Role']}")
                st.write(f"**Status:** {user['Status']}")
                
                if user['ID'] != st.session_state.user['id']:
                    if st.button("Delete Account", key=f"delete_user_{user['ID']}", type="secondary"):
                        try:
                            # Delete hospital's blood requests
                            cursor.execute("""
                                DELETE FROM BloodRequest 
                                WHERE hospitalId IN (SELECT id FROM Hospital WHERE id IN 
                                    (SELECT associatedHospitalId FROM [User] WHERE id = ?))
                            """, (user['ID'],))
                            connection.commit()
                            
                            # Delete hospital's inventory
                            cursor.execute("""
                                DELETE FROM BloodBankInventory 
                                WHERE hospitalId IN (SELECT associatedHospitalId FROM [User] WHERE id = ?)
                            """, (user['ID'],))
                            connection.commit()
                            
                            # Delete hospital record
                            cursor.execute("""
                                DELETE FROM Hospital 
                                WHERE id IN (SELECT associatedHospitalId FROM [User] WHERE id = ?)
                            """, (user['ID'],))
                            connection.commit()
                            
                            # Finally delete the user
                            cursor.execute("DELETE FROM [User] WHERE id = ?", (user['ID'],))
                            connection.commit()
                            
                            st.success(f"Account for {user['Username']} has been deleted")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error deleting account: {str(e)}")

def hospital_approval():
    st.subheader("Hospital Approval")
    
    # Modified query to get hospital status from User table
    query = """
        SELECT 
            h.id,
            h.name as 'Hospital Name', 
            h.location as Location,
            h.bloodBankInventoryId,
            u.status as Status
        FROM Hospital h 
        LEFT JOIN [User] u ON h.id = u.associatedHospitalId AND u.roleId = (SELECT id FROM Role WHERE name = 'Hospital')
    """
    cursor.execute(query)
    data = cursor.fetchall()
    data = [row if isinstance(row, tuple) else tuple(row) for row in data]
    hospitals = pd.DataFrame(data, columns=["ID", "Hospital Name", "Location", "InventoryID", "Status"])
    
    # Display hospitals with action buttons
    st.markdown("### Hospital Approval Management")
    
    for _, hospital in hospitals.iterrows():
        with st.expander(f"{hospital['Hospital Name']} - {hospital['Status']}"):
            st.write(f"**Location:** {hospital['Location']}")
            st.write(f"**Current Status:** {hospital['Status']}")
            
            if hospital['Status'] == 'Inactive' or hospital['Status'] is None:
                if st.button(f"Approve {hospital['Hospital Name']}", key=f"approve_{hospital['ID']}"):
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        
                        # First, create inventory entries for each blood type
                        blood_types_query = "SELECT id FROM BloodType"
                        cursor.execute(blood_types_query)
                        blood_type_ids = cursor.fetchall()
                        
                        for blood_type_id in blood_type_ids:
                            inventory_insert = """
                            INSERT INTO BloodBankInventory (
                                hospitalId, bloodTypeId, quantityInStock, 
                                expirationDate, createdAt, updatedAt
                            ) VALUES (?, ?, 0, DATEADD(year, 1, GETDATE()), GETDATE(), GETDATE())
                            """
                            cursor.execute(inventory_insert, (hospital['ID'], blood_type_id[0]))
                        
                        # Update hospital user status to Active
                        update_user_query = """
                        UPDATE [User]
                        SET status = 'Active',
                            updatedAt = GETDATE()
                        WHERE associatedHospitalId = ? AND roleId = (SELECT id FROM Role WHERE name = 'Hospital')
                        """
                        cursor.execute(update_user_query, (hospital['ID'],))
                        
                        connection.commit()
                        st.success(f"Successfully approved {hospital['Hospital Name']}")
                        st.rerun()
                        
                    except Exception as e:
                        connection.rollback()
                        st.error(f"Error approving hospital: {str(e)}")
                        
            else:  # Hospital is approved
                if st.button(f"Revoke Approval for {hospital['Hospital Name']}", 
                           key=f"revoke_{hospital['ID']}",
                           type="secondary"):
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        
                        # Update user status to Inactive
                        update_user_query = """
                        UPDATE [User]
                        SET status = 'Inactive',
                            updatedAt = GETDATE()
                        WHERE associatedHospitalId = ? AND roleId = (SELECT id FROM Role WHERE name = 'Hospital')
                        """
                        cursor.execute(update_user_query, (hospital['ID'],))
                        
                        
                        connection.commit()
                        st.success(f"Successfully revoked approval for {hospital['Hospital Name']}")
                        st.rerun()
                        
                    except Exception as e:
                        connection.rollback()
                        st.error(f"Error revoking approval: {str(e)}")
    
    # Display summary statistics
    st.markdown("### Summary")
    total_hospitals = len(hospitals)
    approved_hospitals = len(hospitals[hospitals['Status'] == 'Approved'])
    pending_hospitals = len(hospitals[hospitals['Status'] == 'Pending'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Hospitals", total_hospitals)
    with col2:
        st.metric("Approved Hospitals", approved_hospitals)
    with col3:
        st.metric("Pending Approvals", pending_hospitals)

def blood_bank_inventory():
    st.subheader("Blood Bank Inventory")
    query = """
        SELECT bt.bloodType as 'Blood Type', 
        SUM(bbi.quantityInStock) as 'Units Available'
        FROM BloodBankInventory bbi
        JOIN BloodType bt ON bbi.bloodTypeId = bt.id
        GROUP BY bt.bloodType
    """
    cursor.execute(query)
    data = cursor.fetchall()
    data = [row if isinstance(row, tuple) else tuple(row) for row in data]
    inventory = pd.DataFrame(data, columns=["Blood Type", "Units Available"])
    st.table(inventory)

def reports():
    st.subheader("Reports")
    report_types = [
        "Donation Statistics", 
        "Hospital Requests",
        "Inventory Levels",
        "Blood Type Distribution",
        "Hospital Performance",
        "Donor Activity",
        "Request Fulfillment",
        "Dispatch Status"
    ]
    selected_report = st.selectbox("Select Report Type", report_types)
    
    if selected_report == "Donation Statistics":
        query = """
        SELECT 
            FORMAT(a.createdAt, 'yyyy-MM') as Month,
            COUNT(DISTINCT a.donorId) as Donors,
            bt.bloodType as BloodType,
            COUNT(a.id) as TotalDonations
        FROM Appointment a
        JOIN Donor d ON a.donorId = d.id 
        JOIN BloodType bt ON d.bloodTypeId = bt.id
        WHERE a.status = 'Completed'
        GROUP BY FORMAT(a.createdAt, 'yyyy-MM'), bt.bloodType
        ORDER BY Month DESC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        stats = pd.DataFrame(data, columns=["Month", "Donors", "BloodType", "TotalDonations"])
        stats['Month'] = pd.to_datetime(stats['Month'], format='%Y-%m')
        
        st.write("Monthly Donation Trends")
        st.bar_chart(stats.pivot_table(index='Month', columns='BloodType', values='TotalDonations'))
        
    elif selected_report == "Hospital Requests":
        query = """
        SELECT 
            h.name as HospitalName,
            bt.bloodType as BloodType,
            br.urgencyLevel as Urgency,
            br.requestStatus as Status,
            br.requestedQuantity as Requested,
            br.fulfilledQuantity as Fulfilled,
            FORMAT(br.createdAt, 'yyyy-MM-dd') as RequestDate
        FROM BloodRequest br
        JOIN Hospital h ON br.hospitalId = h.id
        JOIN BloodType bt ON br.bloodTypeId = bt.id
        ORDER BY br.createdAt DESC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        requests = pd.DataFrame(data, columns=[
            "Hospital", "Blood Type", "Urgency", "Status", 
            "Requested Units", "Fulfilled Units", "Request Date"
        ])
        st.write("Blood Request Analysis")
        st.dataframe(requests)
        
    elif selected_report == "Inventory Levels":
        query = """
        SELECT 
            h.name as HospitalName,
            bt.bloodType as BloodType,
            bbi.quantityInStock as Stock,
            FORMAT(bbi.expirationDate, 'yyyy-MM-dd') as ExpiryDate
        FROM BloodBankInventory bbi
        JOIN Hospital h ON bbi.hospitalId = h.id
        JOIN BloodType bt ON bbi.bloodTypeId = bt.id
        ORDER BY bbi.expirationDate ASC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        inventory = pd.DataFrame(data, columns=["Hospital", "Blood Type", "Stock", "Expiry Date"])
        st.write("Current Inventory Status")
        st.dataframe(inventory)
        
    elif selected_report == "Blood Type Distribution":
        query = """
        SELECT 
            bt.bloodType as BloodType,
            COUNT(d.id) as DonorCount
        FROM BloodType bt
        LEFT JOIN Donor d ON bt.id = d.bloodTypeId
        GROUP BY bt.bloodType
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        distribution = pd.DataFrame(data, columns=["Blood Type", "Donor Count"])
        st.write("Donor Blood Type Distribution")
        
        # Create pie chart using matplotlib
        fig, ax = plt.subplots()
        ax.pie(distribution["Donor Count"], labels=distribution["Blood Type"], autopct='%1.1f%%')
        st.pyplot(fig)
        
    elif selected_report == "Hospital Performance":
        query = """
        SELECT 
            h.name as HospitalName,
            COUNT(br.id) as TotalRequests,
            AVG(CAST(br.fulfilledQuantity AS FLOAT)/NULLIF(br.requestedQuantity, 0)) * 100 as FulfillmentRate,
            AVG(DATEDIFF(hour, br.createdAt, bd.dispatchDate)) as AvgResponseTime
        FROM Hospital h
        LEFT JOIN BloodRequest br ON h.id = br.hospitalId
        LEFT JOIN BloodDispatch bd ON br.id = bd.requestId
        GROUP BY h.name
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        performance = pd.DataFrame(data, columns=[
            "Hospital", "Total Requests", "Fulfillment Rate (%)", "Avg Response Time (hrs)"
        ])
        st.write("Hospital Performance Metrics")
        st.dataframe(performance)
        
    elif selected_report == "Donor Activity":
        query = """
        SELECT 
            d.name as DonorName,
            bt.bloodType as BloodType,
            COUNT(a.id) as DonationCount,
            MAX(a.appointmentDate) as LastDonation
        FROM Donor d
        JOIN BloodType bt ON d.bloodTypeId = bt.id
        LEFT JOIN Appointment a ON d.id = a.donorId
        WHERE a.status = 'Completed'
        GROUP BY d.name, bt.bloodType
        ORDER BY DonationCount DESC
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        activity = pd.DataFrame(data, columns=["Donor", "Blood Type", "Donations", "Last Donation"])
        st.write("Donor Activity Summary")
        st.dataframe(activity)
        
    elif selected_report == "Request Fulfillment":
        query = """
        SELECT 
            bt.bloodType as BloodType,
            br.urgencyLevel as Urgency,
            COUNT(*) as RequestCount,
            AVG(CAST(br.fulfilledQuantity AS FLOAT)/NULLIF(br.requestedQuantity, 0)) * 100 as FulfillmentRate
        FROM BloodRequest br
        JOIN BloodType bt ON br.bloodTypeId = bt.id
        GROUP BY bt.bloodType, br.urgencyLevel
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        fulfillment = pd.DataFrame(data, columns=[
            "Blood Type", "Urgency", "Request Count", "Fulfillment Rate (%)"
        ])
        st.write("Request Fulfillment Analysis")
        st.dataframe(fulfillment)
        
    elif selected_report == "Dispatch Status":
        query = """
        SELECT 
            bd.deliveryStatus as Status,
            bt.bloodType as BloodType,
            COUNT(*) as DispatchCount,
            AVG(DATEDIFF(minute, bd.dispatchDate, bd.estimatedArrival)) as AvgDeliveryTime
        FROM BloodDispatch bd
        JOIN BloodType bt ON bd.bloodTypeId = bt.id
        GROUP BY bd.deliveryStatus, bt.bloodType
        """
        cursor.execute(query)
        data = cursor.fetchall()
        data = [row if isinstance(row, tuple) else tuple(row) for row in data]
        dispatch = pd.DataFrame(data, columns=[
            "Status", "Blood Type", "Dispatch Count", "Avg Delivery Time (mins)"
        ])
        st.write("Blood Dispatch Statistics")
        st.dataframe(dispatch)

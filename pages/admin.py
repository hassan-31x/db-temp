import streamlit as st
import pandas as pd
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
        SELECT u.username, r.name as Role, 
        CASE WHEN u.associatedHospitalId IS NULL THEN 'Active' ELSE 'Inactive' END as Status
        FROM [User] u
        JOIN Role r ON u.roleId = r.id
    """
    cursor.execute(query)
    data = cursor.fetchall()
    data = [row if isinstance(row, tuple) else tuple(row) for row in data]
    users_df = pd.DataFrame(data, columns=["Username", "Role", "Status"])
    
    st.table(users_df)

def hospital_approval():
    st.subheader("Hospital Approval")
    
    # Modified query for SQL Server
    query = """
        SELECT 
            h.id,
            h.name as 'Hospital Name', 
            h.location as Location,
            h.bloodBankInventoryId,
            CASE 
                WHEN h.bloodBankInventoryId IS NOT NULL THEN 'Approved'
                ELSE 'Pending'
            END as Status
        FROM Hospital h
    """
    cursor.execute(query)
    data = cursor.fetchall()
    hospitals = pd.DataFrame(data, columns=["ID", "Hospital Name", "Location", "InventoryID", "Status"])
    
    # Display hospitals with action buttons
    st.markdown("### Hospital Approval Management")
    
    for _, hospital in hospitals.iterrows():
        with st.expander(f"{hospital['Hospital Name']} - {hospital['Status']}"):
            st.write(f"**Location:** {hospital['Location']}")
            st.write(f"**Current Status:** {hospital['Status']}")
            
            if hospital['Status'] == 'Pending':
                if st.button(f"Approve {hospital['Hospital Name']}", key=f"approve_{hospital['ID']}"):
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        
                        inventory_query = """
                        INSERT INTO BloodBankInventory 
                        (hospitalId, bloodTypeId, quantityInStock, expirationDate, createdAt, updatedAt)
                        SELECT 
                            ?, 
                            bt.id, 
                            0, 
                            DATEADD(year, 1, CAST(GETDATE() AS DATE)), 
                            GETDATE(), 
                            GETDATE()
                        FROM BloodType bt
                        """
                        cursor.execute(inventory_query, (hospital['ID'],))
                        
                        cursor.execute("SELECT SCOPE_IDENTITY()")
                        inventory_id = cursor.fetchone()[0]
                        
                        update_query = """
                        UPDATE Hospital 
                        SET bloodBankInventoryId = ?,
                            updatedAt = GETDATE()
                        WHERE id = ?
                        """
                        cursor.execute(update_query, (inventory_id, hospital['ID']))
                        
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
                        
                        delete_inventory_query = """
                        DELETE FROM BloodBankInventory 
                        WHERE hospitalId = ?
                        """
                        cursor.execute(delete_inventory_query, (hospital['ID'],))
                        
                        update_query = """
                        UPDATE Hospital 
                        SET bloodBankInventoryId = NULL,
                            updatedAt = GETDATE()
                        WHERE id = ?
                        """
                        cursor.execute(update_query, (hospital['ID'],))
                        
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
    inventory = pd.DataFrame(data, columns=["Blood Type", "Units Available"])
    st.table(inventory)

def reports():
    st.subheader("Reports")
    report_types = ["Donation Statistics", "Hospital Requests", "Inventory Levels"]
    selected_report = st.selectbox("Select Report Type", report_types)
    
    if selected_report == "Donation Statistics":
        query = """
        SELECT 
            FORMAT(createdAt, 'yyyy-MM') as Month,
            COUNT(DISTINCT donorId) as Donors
        FROM Appointment
        WHERE status = 'Completed'
        GROUP BY FORMAT(createdAt, 'yyyy-MM')
        ORDER BY Month DESC
        OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY
        """
        cursor.execute(query)
        data = cursor.fetchall()
        stats = pd.DataFrame(data, columns=["Month", "Donors"])
        stats['Month'] = pd.to_datetime(stats['Month'], format='%Y-%m')
        st.bar_chart(stats.set_index("Month"))
        
    elif selected_report == "Hospital Requests":
        query = """
        SELECT 
            FORMAT(createdAt, 'yyyy-MM') as Month,
            COUNT(*) as Requests
        FROM BloodRequest
        GROUP BY FORMAT(createdAt, 'yyyy-MM')
        ORDER BY Month DESC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
        """
        cursor.execute(query)
        data = cursor.fetchall()
        requests = pd.DataFrame(data, columns=["Month", "Requests"])
        requests['Month'] = pd.to_datetime(requests['Month'], format='%Y-%m')
        st.line_chart(requests.set_index("Month"))

import streamlit as st
import pandas as pd
from pages import blood_drive
from a import cursor, cnx

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
        FROM User u
        JOIN Role r ON u.roleId = r.id
    """
    cursor.execute(query)
    data = cursor.fetchall()
    users = pd.DataFrame(data, columns=["Username", "Role", "Status"])
    st.table(users)

def hospital_approval():
    st.subheader("Hospital Approval")
    query = """
        SELECT h.name as 'Hospital Name', h.location as Location,
        CASE 
            WHEN h.bloodBankInventoryId IS NOT NULL THEN 'Approved'
            ELSE 'Pending'
        END as Status
        FROM Hospital h
    """
    cursor.execute(query)
    data = cursor.fetchall()
    hospitals = pd.DataFrame(data, columns=["Hospital Name", "Location", "Status"])
    st.table(hospitals)

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
            DATE_FORMAT(createdAt, '%Y-%m') as Month,
            COUNT(DISTINCT donorId) as Donors
        FROM Appointment
        WHERE status = 'Completed'
        GROUP BY DATE_FORMAT(createdAt, '%Y-%m')
        ORDER BY Month DESC
        LIMIT 3
        """
        cursor.execute(query)
        data = cursor.fetchall()
        stats = pd.DataFrame(data, columns=["Month", "Donors"])
        stats['Month'] = pd.to_datetime(stats['Month'], format='%Y-%m')
        st.bar_chart(stats.set_index("Month"))
        
    elif selected_report == "Hospital Requests":
        query = """
        SELECT 
            DATE_FORMAT(createdAt, '%Y-%m') as Month,
            COUNT(*) as Requests
        FROM BloodRequest
        GROUP BY DATE_FORMAT(createdAt, '%Y-%m')
        ORDER BY Month DESC
        LIMIT 5
        """
        cursor.execute(query)
        data = cursor.fetchall()
        requests = pd.DataFrame(data, columns=["Month", "Requests"])
        requests['Month'] = pd.to_datetime(requests['Month'], format='%Y-%m')
        st.line_chart(requests.set_index("Month"))

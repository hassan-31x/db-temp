import streamlit as st
import pandas as pd
from pages import blood_drive
from a import cursor, cnx

def hospital_page():
    st.title("Hospital Dashboard")
    
    menu = ["Profile", "Blood Requests", "Appointments", "Inventory", "Dispatch", "Blood Drives"]
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
    query = """
    SELECT h.name, h.location, h.contactInformation
    FROM Hospital h
    JOIN User u ON h.id = u.associatedHospitalId
    WHERE u.id = %s
    """
    cursor.execute(query, (st.session_state.user['id'],))
    hospital_info = cursor.fetchone()
    st.write(f"Hospital Name: {hospital_info[0]}")
    st.write(f"Location: {hospital_info[1]}")
    st.write(f"Contact: {hospital_info[2]}")

def blood_requests():
    st.subheader("Blood Requests")
    query = """
    SELECT bt.bloodType as 'Blood Type',
           br.requestedQuantity as Quantity,
           br.requestStatus as Status,
           DATE_FORMAT(br.createdAt, '%Y-%m-%d') as Date
    FROM BloodRequest br
    JOIN BloodType bt ON br.bloodTypeId = bt.id
    JOIN Hospital h ON br.hospitalId = h.id
    JOIN User u ON h.id = u.associatedHospitalId
    WHERE u.id = %s
    ORDER BY br.createdAt DESC
    """
    cursor.execute(query, (st.session_state.user['id'],))
    requests = pd.DataFrame(cursor.fetchall(), columns=['Blood Type', 'Quantity', 'Status', 'Date'])
    st.table(requests)

def appointments():
    st.subheader("Appointments")
    query = """
    SELECT d.name as 'Donor Name',
           bt.bloodType as 'Blood Type',
           DATE_FORMAT(a.appointmentDate, '%Y-%m-%d') as Date,
           TIME_FORMAT(a.appointmentTime, '%H:%i') as Time,
           a.status as Status
    FROM Appointment a
    JOIN Donor d ON a.donorId = d.id
    JOIN BloodType bt ON d.bloodTypeId = bt.id
    JOIN Hospital h ON a.hospitalId = h.id
    JOIN User u ON h.id = u.associatedHospitalId
    WHERE u.id = %s
    ORDER BY a.appointmentDate, a.appointmentTime
    """
    cursor.execute(query, (st.session_state.user['id'],))
    appointments = pd.DataFrame(cursor.fetchall(), 
                              columns=['Donor Name', 'Blood Type', 'Date', 'Time', 'Status'])
    st.table(appointments)

def inventory():
    st.subheader("Inventory")
    query = """
    SELECT bt.bloodType as 'Blood Type',
           bbi.quantityInStock as 'Units Available',
           DATE_FORMAT(bbi.expirationDate, '%Y-%m-%d') as 'Expiration Date'
    FROM BloodBankInventory bbi
    JOIN BloodType bt ON bbi.bloodTypeId = bt.id
    JOIN Hospital h ON bbi.hospitalId = h.id
    JOIN User u ON h.id = u.associatedHospitalId
    WHERE u.id = %s
    """
    cursor.execute(query, (st.session_state.user['id'],))
    inventory = pd.DataFrame(cursor.fetchall(), 
                           columns=['Blood Type', 'Units Available', 'Expiration Date'])
    st.table(inventory)

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
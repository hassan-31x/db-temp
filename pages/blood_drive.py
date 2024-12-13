import streamlit as st
import pandas as pd
from a import cursor, cnx

def blood_drive_page():
    st.title("Blood Drive Management")
    
    if st.session_state.user['role'] == 'admin':
        admin_blood_drive_page()
    elif st.session_state.user['role'] == 'donor':
        donor_blood_drive_page()
    elif st.session_state.user['role'] == 'hospital':
        hospital_blood_drive_page()

def admin_blood_drive_page():
    st.subheader("Admin Blood Drive Management")
    
    new_drive_form = st.form("new_drive_form")
    with new_drive_form:
        drive_name = st.text_input("Drive Name")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        location = st.text_input("Location")
        submitted = st.form_submit_button("Add Blood Drive")
    
    if submitted:
        query = """
        INSERT INTO BloodDrive (name, startDate, endDate, location, createdAt, updatedAt)
        VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(query, (drive_name, start_date, end_date, location))
        cnx.commit()
        st.success(f"Blood drive '{drive_name}' added successfully.")
    
    query = """
    SELECT name as 'Drive Name', 
           DATE_FORMAT(startDate, '%Y-%m-%d') as 'Start Date',
           DATE_FORMAT(endDate, '%Y-%m-%d') as 'End Date',
           location as Location
    FROM BloodDrive
    WHERE endDate >= CURDATE()
    """
    cursor.execute(query)
    active_drives = pd.DataFrame(cursor.fetchall(), columns=['Drive Name', 'Start Date', 'End Date', 'Location'])
    st.table(active_drives)

def donor_blood_drive_page():
    st.subheader("Donor Blood Drive View")
    
    query = """
    SELECT name as 'Drive Name', 
           DATE_FORMAT(startDate, '%Y-%m-%d') as 'Start Date',
           DATE_FORMAT(endDate, '%Y-%m-%d') as 'End Date',
           location as Location
    FROM BloodDrive
    WHERE endDate >= CURDATE()
    """
    cursor.execute(query)
    active_drives = pd.DataFrame(cursor.fetchall(), columns=['Drive Name', 'Start Date', 'End Date', 'Location'])
    st.table(active_drives)
    
    selected_drive = st.selectbox("Select Blood Drive", active_drives["Drive Name"])
    if st.button("Register for Drive"):
        query = """
        INSERT INTO DriveRegistration (driveId, donorId, status, createdAt, updatedAt)
        SELECT bd.id, d.id, 'Registered', NOW(), NOW()
        FROM BloodDrive bd, Donor d
        WHERE bd.name = %s AND d.userId = %s
        """
        cursor.execute(query, (selected_drive, st.session_state.user['id']))
        cnx.commit()
        st.success(f"You have successfully registered for the '{selected_drive}' blood drive.")

def hospital_blood_drive_page():
    st.subheader("Hospital Blood Drive View")
    
    query = """
    SELECT name as 'Drive Name', 
           DATE_FORMAT(startDate, '%Y-%m-%d') as 'Start Date',
           DATE_FORMAT(endDate, '%Y-%m-%d') as 'End Date',
           location as Location
    FROM BloodDrive
    WHERE endDate >= CURDATE()
    """
    cursor.execute(query)
    active_drives = pd.DataFrame(cursor.fetchall(), columns=['Drive Name', 'Start Date', 'End Date', 'Location'])
    st.table(active_drives)
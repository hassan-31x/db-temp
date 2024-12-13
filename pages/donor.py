import streamlit as st
import pandas as pd
from pages import blood_drive
from a import cursor, cnx

def donor_page():
    st.title("Donor Dashboard")
    
    menu = ["Profile", "Appointments", "Donation History", "Blood Requests", "Blood Drives"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Profile":
        profile()
    elif choice == "Appointments":
        appointments()
    elif choice == "Donation History":
        donation_history()
    elif choice == "Blood Requests":
        blood_requests()
    elif choice == "Blood Drives":
        blood_drive.blood_drive_page()

def profile():
    st.subheader("Donor Profile")
    
    # First, fetch current donor information
    query = """
    SELECT d.name, bt.bloodType, d.lastDonationDate, d.contactInformation, d.medicalHistory, d.eligibilityStatus
    FROM Donor d
    JOIN BloodType bt ON d.bloodTypeId = bt.id
    JOIN User u ON d.userId = u.id
    WHERE u.id = %s
    """
    cursor.execute(query, (st.session_state.user['id'],))
    donor_info = cursor.fetchone()
    
    if donor_info:
        # Create two columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Personal Information")
            # Edit name form
            with st.form("edit_personal_info_form"):
                new_name = st.text_input("Full Name", value=donor_info[0])
                new_contact = st.text_area("Contact Information", value=donor_info[3])
                submit_button = st.form_submit_button("Update Personal Information")
                
                if submit_button:
                    try:
                        update_query = """
                        UPDATE Donor d
                        JOIN User u ON d.userId = u.id
                        SET d.name = %s, 
                            d.contactInformation = %s,
                            d.updatedAt = NOW()
                        WHERE u.id = %s
                        """
                        cursor.execute(update_query, (new_name, new_contact, st.session_state.user['id']))
                        cnx.commit()
                        st.success("Personal information updated successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating information: {str(e)}")
            
            
        
        with col2:
            st.markdown("### Other Information")
            st.write(f"**Medical History:**")
            st.text(donor_info[4])

            st.write(f"**Blood Type:** {donor_info[1]}")
            st.write(f"**Last Donation:** {donor_info[2] if donor_info[2] else 'No donations yet'}")
            st.write(f"**Eligibility Status:** {'Eligible' if donor_info[5] else 'Not Eligible'}")
            

def appointments():
    st.subheader("Appointments")
    query = """
    SELECT DATE_FORMAT(a.appointmentDate, '%Y-%m-%d') as Date,
           TIME_FORMAT(a.appointmentTime, '%H:%i') as Time,
           h.name as Location,all
           a.status as Status
    FROM Appointment a
    JOIN Hospital h ON a.hospitalId = h.id
    JOIN Donor d ON a.donorId = d.id
    WHERE d.userId = %s
    ORDER BY a.appointmentDate DESC
    """
    cursor.execute(query, (st.session_state.user['id'],))
    appointments = pd.DataFrame(cursor.fetchall(), columns=['Date', 'Time', 'Location', 'Status'])
    st.table(appointments)

def donation_history():
    st.subheader("Donation History")
    query = """
    SELECT DATE_FORMAT(a.appointmentDate, '%Y-%m-%d') as Date,
           h.name as Location,
           bt.bloodType as 'Blood Type',
           450 as 'Amount (ml)'
    FROM Appointment a
    JOIN Hospital h ON a.hospitalId = h.id
    JOIN Donor d ON a.donorId = d.id
    JOIN BloodType bt ON d.bloodTypeId = bt.id
    WHERE d.userId = %s AND a.status = 'Completed'
    ORDER BY a.appointmentDate DESC
    """
    cursor.execute(query, (st.session_state.user['id'],))
    history = pd.DataFrame(cursor.fetchall(), columns=['Date', 'Location', 'Blood Type', 'Amount (ml)'])
    st.table(history)

def blood_requests():
    st.subheader("Blood Requests")
    requests = pd.DataFrame({
        "Hospital": ["City Hospital", "Central Clinic", "Metro Healthcare"],
        "Blood Type": ["A+", "O-", "B+"],
        "Urgency": ["High", "Medium", "Low"],
        "Distance": ["5 km", "10 km", "15 km"]
    })
    st.table(requests)
    
    if st.button("Respond to Request"):
        st.success("Thank you for your willingness to donate! The hospital will contact you with further details.")
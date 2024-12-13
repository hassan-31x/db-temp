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
    
    # Get all appointments with detailed information
    query = """
    SELECT 
        DATE_FORMAT(a.appointmentDate, '%Y-%m-%d') as Date,
        TIME_FORMAT(a.appointmentTime, '%H:%i') as Time,
        h.name as Hospital,
        h.location as Location,
        h.contactInformation as 'Hospital Contact',
        bt.bloodType as 'Blood Type',
        a.status as Status,
        CASE 
            WHEN a.appointmentDate < CURDATE() THEN 'Past'
            WHEN a.appointmentDate = CURDATE() THEN 'Today'
            ELSE 'Upcoming'
        END as Timeline
    FROM Appointment a
    JOIN Hospital h ON a.hospitalId = h.id
    JOIN Donor d ON a.donorId = d.id
    JOIN BloodType bt ON d.bloodTypeId = bt.id
    WHERE d.userId = %s
    ORDER BY 
        a.appointmentDate DESC,
        a.appointmentTime DESC
    """
    cursor.execute(query, (st.session_state.user['id'],))
    appointments_data = cursor.fetchall()
    
    if appointments_data:
        appointments_df = pd.DataFrame(appointments_data, 
                                     columns=['Date', 'Time', 'Hospital', 'Location', 
                                            'Hospital Contact', 'Blood Type', 'Status', 'Timeline'])
        
        # Create tabs for different appointment timelines
        tab1, tab2, tab3 = st.tabs(["Upcoming", "Today", "Past"])
        
        with tab1:
            upcoming = appointments_df[appointments_df['Timeline'] == 'Upcoming']
            if not upcoming.empty:
                st.markdown("### Upcoming Appointments")
                for _, appt in upcoming.iterrows():
                    with st.expander(f"{appt['Date']} - {appt['Hospital']}"):
                        st.write(f"**Time:** {appt['Time']}")
                        st.write(f"**Hospital:** {appt['Hospital']}")
                        st.write(f"**Location:** {appt['Location']}")
                        st.write(f"**Contact:** {appt['Hospital Contact']}")
                        st.write(f"**Blood Type:** {appt['Blood Type']}")
                        st.write(f"**Status:** {appt['Status']}")
                        
                        #TODO: Add cancellation option for upcoming appointments
                        # Add cancellation option for upcoming appointments
                        # if st.button("Cancel Appointment", key=f"cancel_{appt['Date']}_{appt['Time']}"):
                        #     try:
                        #         cancel_query = """
                        #         UPDATE Appointment a
                        #         JOIN Donor d ON a.donorId = d.id
                        #         SET a.status = 'Cancelled',
                        #             a.updatedAt = NOW()
                        #         WHERE d.userId = %s
                        #         AND DATE_FORMAT(a.appointmentDate, '%Y-%m-%d') = %s
                        #         AND TIME_FORMAT(a.appointmentTime, '%H:%i') = %s
                        #         """
                        #         cursor.execute(cancel_query, 
                        #                      (st.session_state.user['id'], appt['Date'], appt['Time']))
                        #         cnx.commit()
                        #         st.success("Appointment cancelled successfully!")
                        #         st.rerun()
                        #     except Exception as e:
                        #         st.error(f"Error cancelling appointment: {str(e)}")
            else:
                st.info("No upcoming appointments")
        
        with tab2:
            today = appointments_df[appointments_df['Timeline'] == 'Today']
            if not today.empty:
                st.markdown("### Today's Appointments")
                st.table(today[['Time', 'Hospital', 'Location', 'Blood Type', 'Status']])
            else:
                st.info("No appointments scheduled for today")
        
        with tab3:
            past = appointments_df[appointments_df['Timeline'] == 'Past']
            if not past.empty:
                st.markdown("### Past Appointments")
                st.table(past[['Date', 'Hospital', 'Blood Type', 'Status']])
            else:
                st.info("No past appointments")
                
        # Show appointment statistics
        st.markdown("### Appointment Statistics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            completed = len(appointments_df[appointments_df['Status'] == 'Completed'])
            st.metric("Completed Donations", completed)
        
        with col2:
            upcoming_count = len(appointments_df[appointments_df['Timeline'] == 'Upcoming'])
            st.metric("Upcoming Appointments", upcoming_count)
        
        with col3:
            cancelled = len(appointments_df[appointments_df['Status'] == 'Cancelled'])
            st.metric("Cancelled Appointments", cancelled)
            
    else:
        st.info("No appointments found")
        st.write("You can schedule appointments by responding to blood requests or registering for blood drives.")

def donation_history():
    st.subheader("Donation History")
    
    # First get the donor ID for the current user
    donor_query = """
    SELECT d.id 
    FROM Donor d
    JOIN User u ON d.userId = u.id
    WHERE u.id = %s
    """
    cursor.execute(donor_query, (st.session_state.user['id'],))
    donor_result = cursor.fetchone()
    
    if not donor_result:
        st.error("Donor information not found.")
        return
        
    donor_id = donor_result[0]
    
    # Get donation history from BloodRequest table
    query = """
    SELECT 
        DATE_FORMAT(br.createdAt, '%Y-%m-%d') as Date,
        h.name as Hospital,
        bt.bloodType as 'Blood Type',
        br.requestedQuantity as 'Amount (units)',
        br.urgencyLevel as 'Urgency Level'
    FROM BloodRequest br
    JOIN Hospital h ON br.hospitalId = h.id
    JOIN BloodType bt ON br.bloodTypeId = bt.id
    WHERE br.requestStatus = 'Fulfilled' 
    AND br.fulfilledBy = %s
    ORDER BY br.createdAt DESC
    """
    cursor.execute(query, (donor_id,))
    history = pd.DataFrame(cursor.fetchall(), 
                         columns=['Date', 'Hospital', 'Blood Type', 'Amount (units)', 'Urgency Level'])
    
    if history.empty:
        st.info("No donation history found.")
    else:
        st.table(history)

def blood_requests():
    st.subheader("Blood Requests")
    
    # Get donor's blood type
    donor_query = """
    SELECT bt.bloodType, bt.id, d.id as donor_id
    FROM Donor d
    JOIN BloodType bt ON d.bloodTypeId = bt.id
    JOIN User u ON d.userId = u.id
    WHERE u.id = %s
    """
    cursor.execute(donor_query, (st.session_state.user['id'],))
    donor_blood_info = cursor.fetchone()
    
    if not donor_blood_info:
        st.error("Donor information not found.")
        return
        
    # Get pending blood requests matching donor's blood type
    query = """
    SELECT 
        br.id,
        h.name as Hospital,
        bt.bloodType as 'Blood Type',
        br.urgencyLevel as Urgency,
        br.requestedQuantity as 'Units Needed',
        h.location as Location,
        h.id as hospital_id
    FROM BloodRequest br
    JOIN Hospital h ON br.hospitalId = h.id
    JOIN BloodType bt ON br.bloodTypeId = bt.id
    WHERE br.requestStatus = 'Pending'
    AND br.bloodTypeId = %s
    AND br.requestedQuantity > br.fulfilledQuantity
    ORDER BY 
        CASE br.urgencyLevel
            WHEN 'Critical' THEN 1
            WHEN 'High' THEN 2
            WHEN 'Medium' THEN 3
            WHEN 'Low' THEN 4
        END,
        br.createdAt DESC
    """
    cursor.execute(query, (donor_blood_info[1],))
    requests_data = cursor.fetchall()
    
    if not requests_data:
        st.info(f"No pending blood requests for your blood type ({donor_blood_info[0]}) at this time.")
        return
    
    st.write(f"Showing blood requests matching your blood type: {donor_blood_info[0]}")
    
    # Display each request with a response button
    for request in requests_data:
        with st.expander(f"{request[1]} - {request[2]} ({request[3]} Urgency)"):
            st.write(f"**Hospital:** {request[1]}")
            st.write(f"**Location:** {request[5]}")
            st.write(f"**Blood Type Needed:** {request[2]}")
            st.write(f"**Urgency Level:** {request[3]}")
            st.write(f"**Units Needed:** {request[4]}")
            
            # Response form
            with st.form(f"response_form_{request[0]}"):
                st.write("### Schedule Donation Appointment")
                
                # Get available dates (next 7 days)
                available_dates = pd.date_range(
                    start=pd.Timestamp.now() + pd.Timedelta(days=1),
                    end=pd.Timestamp.now() + pd.Timedelta(days=7),
                    freq='D'
                )
                selected_date = st.date_input(
                    "Select Date",
                    min_value=available_dates[0],
                    max_value=available_dates[-1],
                    value=available_dates[0]
                )
                
                # Time slots (9 AM to 5 PM, hourly)
                time_slots = [f"{hour:02d}:00" for hour in range(9, 17)]
                selected_time = st.selectbox("Select Time", time_slots)
                
                submit_response = st.form_submit_button("Schedule Appointment")
                
                if submit_response:
                    try:
                        # Start transaction
                        cursor.execute("START TRANSACTION")
                        
                        # Create appointment
                        appointment_query = """
                        INSERT INTO Appointment (
                            donorId, hospitalId, appointmentDate, appointmentTime,
                            status, createdAt, updatedAt
                        ) VALUES (%s, %s, %s, %s, 'Scheduled', NOW(), NOW())
                        """
                        cursor.execute(appointment_query, (
                            donor_blood_info[2],  # donor_id
                            request[6],           # hospital_id
                            selected_date,
                            selected_time
                        ))
                        
                        # Update blood request
                        update_request_query = """
                        UPDATE BloodRequest 
                        SET fulfilledQuantity = requestedQuantity,
                            requestStatus = 'Fulfilled',
                            updatedAt = NOW()
                        WHERE id = %s
                        """
                        cursor.execute(update_request_query, (request[0],))
                        
                        # Update donor's last donation date
                        update_donor_query = """
                        UPDATE Donor 
                        SET lastDonationDate = %s,
                            updatedAt = NOW()
                        WHERE id = %s
                        """
                        cursor.execute(update_donor_query, (selected_date, donor_blood_info[2]))
                        
                        # Commit transaction
                        cnx.commit()
                        st.success("Appointment scheduled successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        st.error(f"Error scheduling appointment: {str(e)}")
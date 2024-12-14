import streamlit as st
from db import cursor, connection

def auth_page():
    st.title("Blood Donation Management System")
    page = st.radio("Choose an option", ["Login", "Register"])
    
    if page == "Login":
        login_page()
    else:
        register_page()

def login_page():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        query = "SELECT * FROM [User] WHERE username = ? AND password_hash = ?"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            # Get user's ID and role
            user_id = user[0]
            role_id = user[4]  # Assuming roleId is the 4th column
            
            role = 0
            if role_id == 1:
                role = 'admin'
            elif role_id == 2:
                role = 'donor'
            else:
                role = 'hospital'
                
            # Store both user ID and role in session state
            st.session_state.user = {
                "id": user_id,
                "username": username, 
                "role": role
            }
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def register_page():
    st.subheader("Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    role = st.selectbox("Role", ["donor", "hospital"])

    # Additional fields based on role
    if role == "donor":
        name = st.text_input("Full Name")
        blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        contact = st.text_input("Contact Information")
        medical_history = st.text_area("Medical History")
    else:  # hospital
        hospital_name = st.text_input("Hospital Name")
        location = st.text_input("Location")
        contact_info = st.text_input("Contact Information")

    roleId = 2 if role == 'donor' else 3
    
    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters long")
        else:
            try:
                # Check if username exists
                checkQuery = "SELECT username FROM [User] WHERE username = ?"
                cursor.execute(checkQuery, (username,))

                if cursor.fetchone():
                    st.error("Username already exists. Please choose a different username.")
                else:
                    # Insert into User table
                    userQuery = """
                    INSERT INTO [User] (username, password_hash, roleId, createdAt, updatedAt) 
                    VALUES (?, ?, ?, GETDATE(), GETDATE())"""
                    cursor.execute(userQuery, (username, password, roleId))
                    connection.commit()
                    
                    # Get the newly created user's ID
                    cursor.execute("SELECT @@IDENTITY")
                    result = cursor.fetchone()
                    if result is None or result[0] is None:
                        raise Exception("Failed to get new user ID")
                    user_id = result[0]
                    
                    if role == 'donor':
                        # Get blood type ID
                        cursor.execute("SELECT id FROM BloodType WHERE bloodType = ?", (blood_type,))
                        blood_type_id = cursor.fetchone()[0]

                        # Insert into Donor table
                        donorQuery = """
                        INSERT INTO Donor (userId, name, bloodTypeId, contactInformation, 
                                         medicalHistory, eligibilityStatus, createdAt, updatedAt)
                        VALUES (?, ?, ?, ?, ?, 1, GETDATE(), GETDATE())
                        """
                        cursor.execute(donorQuery, (user_id, name, blood_type_id, contact, medical_history))
                        connection.commit()
                    
                    else:  # hospital
                        # Insert into Hospital table
                        hospitalQuery = """
                        INSERT INTO Hospital (name, location, contactInformation, createdAt, updatedAt)
                        VALUES (?, ?, ?, GETDATE(), GETDATE())
                        """
                        cursor.execute(hospitalQuery, (hospital_name, location, contact_info))
                        connection.commit()

                        # Get the newly created hospital's ID
                        cursor.execute("SELECT @@IDENTITY")
                        result = cursor.fetchone()
                        if result is None or result[0] is None:
                            raise Exception("Failed to get new hospital ID")
                        hospital_id = result[0]
                        
                        # Update User table with associated hospital ID
                        cursor.execute("UPDATE [User] SET associatedHospitalId = ? WHERE id = ?", 
                                     (hospital_id, user_id))
                        connection.commit()
                    
                    st.success("Registration successful! Please log in.")
                    
            except Exception as e:
                st.error(f"An error occurred during registration: {str(e)}")

import streamlit as st
from pages import auth, admin, hospital, donor, blood_drive

st.set_page_config(page_title="Blood Donation Management System", layout="wide")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

def main():
    # Check if user is logged in
    if not st.session_state.user:
        auth.auth_page()
    else:
        # Show sidebar with user info and logout button
        with st.sidebar:
            st.write(f"Logged in as: {st.session_state.user['username']} ({st.session_state.user['role']})")
            if st.button("Logout"):
                st.session_state.user = None
                st.rerun()

        # Route to appropriate dashboard based on role
        role = st.session_state.user['role']
        if role == 'admin':
            admin.admin_page()
        elif role == 'hospital':
            hospital.hospital_page()
        elif role == 'donor':
            donor.donor_page()

if __name__ == "__main__":
    main()

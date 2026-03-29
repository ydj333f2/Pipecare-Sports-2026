import streamlit as st
import pandas as pd
import smtplib
import random
import os
from datetime import datetime

# --- 1. LOAD SECRETS ---
# These are pulled from the Secrets menu you just filled in
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASS = st.secrets["GMAIL_PASS"]

# --- 2. SESSION STATE ---
# This keeps track of whether the user has passed the OTP stage
if 'verified' not in st.session_state:
    st.session_state.verified = False
if 'otp_code' not in st.session_state:
    st.session_state.otp_code = None

# --- 3. EMAIL FUNCTION ---
def send_otp(recipient):
    otp = str(random.randint(1000, 9999))
    st.session_state.otp_code = otp
    try:
        # Connect to Gmail Server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        subject = "PIPECARE Sports Event Verification"
        body = f"Your 4-digit verification code is: {otp}"
        msg = f"Subject: {subject}\n\n{body}"
        server.sendmail(GMAIL_USER, recipient, msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# --- 4. APP INTERFACE ---
st.title("🏆 PIPECARE Noida Sports Event")

# STEP A: VERIFICATION GATE
if not st.session_state.verified:
    st.subheader("Email Verification")
    st.info("To register, please verify your official @pipecaregroup.com email.")
    
    email_input = st.text_input("Company Email ID")
    
    if st.button("Send OTP"):
        if "@pipecaregroup.com" in email_input.lower():
            if send_otp(email_input):
                st.success("OTP sent! Please check your Outlook inbox.")
        else:
            st.error("Please enter a valid company email address.")

    user_otp = st.text_input("Enter 4-Digit Code")
    if st.button("Verify & Open Form"):
        if user_otp == st.session_state.otp_code and st.session_state.otp_code is not None:
            st.session_state.verified = True
            st.rerun()
        else:
            st.error("Invalid or missing code. Please try again.")

# STEP B: THE ACTUAL FORM (Unlocks after verification)
else:
    st.success(f"✅ Email Verified. Welcome to the Registration Portal!")
    
    with st.form("main_registration"):
        st.subheader("1. Personal Details")
        name = st.text_input("Full Name*")
        whatsapp = st.text_input("WhatsApp Number*")
        location = st.radio("Primary Work Location", ["Noida Office", "Noida Workshop"])
        
        st.divider()
        
        st.subheader("2. Choose Your Sport")
        sport = st.selectbox("What would you like to play?", ["Cricket", "Badminton", "Both", "Other Games"])
        
        # Sport-Specific Logic
        if sport in ["Cricket", "Both"]:
            st.info("🏏 Cricket Configuration")
            c_format = st.selectbox("Format", ["Proper Ground", "Box Cricket"])
            c_ball = st.radio("Ball", ["Tennis Ball", "Leather Ball"])
            c_overs = st.select_slider("Overs", options=[10, 20])
            
        if sport in ["Badminton", "Both"]:
            st.info("🏸 Badminton Configuration")
            b_cat = st.radio("Category", ["Singles", "Doubles", "Both"])
            b_score = st.selectbox("Scoring", ["11 pts (Best of 3)", "15 pts (Best of 3)", "21 pts (1 set)"])

        st.divider()
        
        st.subheader("3. Logistics")
        day = st.selectbox("Preferred Day", ["Saturday", "Sunday", "Both"])
        travel = st.select_slider("Travel Distance (kms)", options=[10, 20, 30])
        
        submit = st.form_submit_button("Submit Registration")
        
        if submit:
            if name and whatsapp:
                # Store data in CSV
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now(),
                    "Name": name,
                    "WhatsApp": whatsapp,
                    "Location": location,
                    "Sport": sport
                }])
                
                # Append to file
                if not os.path.isfile('data.csv'):
                    new_entry.to_csv('data.csv', index=False)
                else:
                    new_entry.to_csv('data.csv', mode='a', index=False, header=False)
                
                st.balloons()
                st.success("Registration complete! Invite your team members.")

# --- FOOTER ---
st.divider()
st.subheader("📊 Live Event Trends")
# (Chart code would go here once we have real data in data.csv)

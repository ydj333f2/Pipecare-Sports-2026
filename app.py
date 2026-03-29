import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random

# --- 1. SET THEME (MILD SKYBLUE) ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="centered", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd; color: #0d47a1; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1976d2; color: white; height: 3em; border: none; font-weight: bold; }
    .stTextInput>div>div>input { background-color: white; color: black; }
    .step-header { color: #0d47a1; font-weight: bold; font-size: 1.5rem; margin-bottom: 20px; }
    .receipt-box { padding: 20px; border-radius: 10px; background: white; border: 2px solid #1976d2; color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & SESSION STATE ---
DB_FILE = 'data.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

if 'step' not in st.session_state: st.session_state.step = 0
if 'verified' not in st.session_state: st.session_state.verified = False
if 'form_data' not in st.session_state: st.session_state.form_data = {}

def save_data(data_dict):
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
    new_df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)

# --- 3. STEP 0: OTP VERIFICATION ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Sports Portal")
    st.subheader("Employee Verification")
    email = st.text_input("Company Email")
    if st.button("Send Code"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email, f"Subject: Sports Code\n\nYour code is: {otp}")
                server.quit()
                st.success("OTP Sent!")
            except: st.error("Email Error.")
    
    input_otp = st.text_input("Enter 4-Digit Code")
    if st.button("Verify & Start"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            st.session_state.step = 1
            st.rerun()

# --- 4. MULTI-STEP FORM ---
elif st.session_state.step > 0:
    st.title("🏆 Registration")
    
    # --- STEP 1: IDENTITY & CONTACT ---
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Step 1: Identity & Contact</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Participation"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2
                st.rerun()
            else: st.error("Please fill all fields.")

    # --- STEP 2: PARTICIPATION & LOGISTICS ---
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Step 2: Participation & Logistics</div>', unsafe_allow_html=True)
        st.session_state.form_data['type'] = st.selectbox("Role", ["Athlete (Player)", "Audience/Support", "Not Attending"])
        
        if st.session_state.form_data['type'] != "Not Attending":
            st.session_state.form_data['travel'] = st.select_slider("Travel Radius", options=["10 km", "20 km", "30 km"])
            st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday", "Holidays"])
        else:
            st.session_state.form_data['travel'] = "N/A"
            st.session_state.form_data['schedule'] = "N/A"

        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Game Selection"):
            if st.session_state.form_data['type'] == "Not Attending":
                st.session_state.step = 5 # Jump to Finish
            else:
                st.session_state.step = 3
            st.rerun()

    # --- STEP 3: GAME SELECTION ---
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Step 3: Game Selection</div>', unsafe_allow_html=True)
        st.session_state.form_data['sport_main'] = st.selectbox("Which Sport?", ["Cricket", "Badminton", "Both", "Other Games"])
        
        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next: Set Rules"):
            st.session_state.step = 4
            st.rerun()

    # --- STEP 4: GAME SPECIFICS (THE POP-UP LOGIC) ---
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">Step 4: Rules & Preferences</div>', unsafe_allow_html=True)
        details = ""
        sport = st.session_state.form_data['sport_main']

        if sport in ["Cricket", "Both"]:
            st.info("🏏 Cricket Specs")
            c_fmt = st.selectbox("Format", ["Proper Ground", "Box Cricket"])
            c_ball = st.radio("Ball", ["Tennis", "Leather"], horizontal=True)
            if c_fmt == "Box Cricket":
                c_ovr = st.selectbox("Overs", [10, 15, 20])
                c_team = st.selectbox("Team Size", [6, 8, 10])
                details += f"Cricket: {c_fmt}, {c_ball}, {c_ovr} Overs, {c_team} Players. "
            else: details += f"Cricket: {c_fmt}, {c_ball}. "

        if sport in ["Badminton", "Both"]:
            st.info("🏸 Badminton Specs")
            b_mode = st.multiselect("Format", ["Singles", "Doubles"])
            if "Singles" in b_mode:
                b_s = st.selectbox("Singles Pts", ["11 (Best of 3)", "15 (Best of 3)", "21 (1 Set)", "21 (Best of 3)"])
                details += f"Badminton Singles: {b_s}. "
            if "Doubles" in b_mode:
                b_d = st.selectbox("Doubles Pts", ["15 (Best of 3)", "21 (Best of 3)"])
                details += f"Badminton Doubles: {b_d}. "
        
        if sport == "Other Games":
            others = st.multiselect("Interests", ["TT", "Snooker", "Tug of War", "7 Stones", "Chess", "Carrom"])
            details += f"Games: {others}. "

        custom = st.text_area("Custom Suggestions")
        st.session_state.form_data['details'] = details + " | " + custom

        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Submit Final Registration"):
            st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(st.session_state.form_data)
            st.session_state.step = 5
            st.balloons()
            st.rerun()

    # --- STEP 5: FINAL RECEIPT & POLLS ---
    elif st.session_state.step == 5:
        st.success("✅ Submission Complete!")
        res_col1, res_col2 = st.columns([1, 1.2], gap="large")
        
        with res_col1:
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.subheader("Your Selection")
            st.write(f"**Name:** {st.session_state.form_data['name']}")
            st.write(f"**WhatsApp:** {st.session_state.form_data['whatsapp']}")
            st.write(f"**Schedule:** {st.session_state.form_data['schedule']}")
            st.info(f"**Rules:** {st.session_state.form_data.get('details', 'N/A')}")
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("Edit Response"): st.session_state.step = 1; st.rerun()

        with res_col2:
            st.subheader("Live Polls")
            df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
            if not df.empty:
                st.plotly_chart(px.pie(df, names='Type', hole=0.4), use_container_width=True)
                st.plotly_chart(px.histogram(df[df['Type']!='Not Attending'], x='schedule', color='unit', barmode='group'), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random
from urllib.parse import quote

# --- 1. SET THEME (MILD SKYBLUE) ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="centered", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd; color: #0d47a1; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1976d2; color: white; height: 3em; border: none; font-weight: bold; }
    .stTextInput>div>div>input { background-color: white; color: black; }
    .step-header { color: #0d47a1; font-weight: bold; font-size: 1.5rem; margin-bottom: 20px; border-bottom: 2px solid #1976d2; padding-bottom: 5px; }
    .hr-box { padding: 15px; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #5d4037; font-size: 0.9rem; margin-top: 10px; }
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

# --- 3. STEP 0: RESTORED OTP VERIFICATION ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Sports Portal")
    st.subheader("Employee Verification")
    email = st.text_input("Company Email")
    if st.button("Send Code"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            try:
                # This uses your original Gmail setup
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email, f"Subject: Sports Code\n\nYour code is: {otp}")
                server.quit()
                st.success("OTP Sent to your email!")
            except Exception as e: 
                st.error(f"Email Error: {e}. Check st.secrets configuration.")
    
    input_otp = st.text_input("Enter 4-Digit Code", type="password")
    if st.button("Verify & Start"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("Incorrect Code.")

# --- 4. MULTI-STEP FORM ---
elif st.session_state.step > 0:
    
    # --- STEP 1: IDENTITY ---
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Step 1: Identity & Contact</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Sport Selection"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2
                st.rerun()
            else: st.error("Please fill all fields.")

    # --- STEP 2: REFINED MULTI-SPORT SELECTION ---
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Step 2: Sport Selection</div>', unsafe_allow_html=True)
        
        # Now users can select multiple
        sports = st.multiselect("Which sports would you like to play?", 
                                ["Cricket", "Badminton", "Table Tennis", "Snooker/Billiards", "Chess", "Carrom", "Other"])
        
        custom_sport = ""
        if "Other" in sports:
            custom_sport = st.text_input("Enter your custom sport choice:")
        
        st.session_state.form_data['selected_sports'] = sports
        st.session_state.form_data['custom_sport'] = custom_sport

        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Rules & Logistics"):
            if sports:
                st.session_state.step = 3
                st.rerun()
            else: st.error("Please select at least one option.")

    # --- STEP 3: DYNAMIC RULES (POP-OUTS) ---
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Step 3: Format & Rules</div>', unsafe_allow_html=True)
        chosen = st.session_state.form_data['selected_sports']
        details = ""

        if "Cricket" in chosen:
            with st.expander("🏏 Cricket Specs", expanded=True):
                c_fmt = st.selectbox("Format", ["Proper Ground", "Box Cricket", "Both"])
                c_ball = st.radio("Ball", ["Tennis", "Leather"], horizontal=True)
                if c_fmt == "Box Cricket":
                    c_team = st.selectbox("Team Size", [6, 8, 11])
                    c_ovr = st.selectbox("Box Overs", [6, 8, 10])
                    details += f"Cricket: {c_fmt} ({c_team} Players, {c_ovr} Overs, {c_ball}). "
                else:
                    c_g_ovr = st.radio("Ground Overs", ["10 Overs", "20 Overs"])
                    details += f"Cricket: Ground ({c_g_ovr}, {c_ball}). "

        if "Badminton" in chosen:
            with st.expander("🏸 Badminton Specs", expanded=True):
                b_mode = st.multiselect("Interested In", ["Singles", "Doubles"])
                if "Singles" in b_mode:
                    b_s = st.selectbox("Singles Pts", ["11 (Best of 3)", "15 (Best of 3)", "21 (1 Set)", "21 (Best of 3)"])
                    details += f"Badminton Singles: {b_s}. "
                if "Doubles" in b_mode:
                    b_d = st.selectbox("Doubles Pts", ["15 (Best of 3)", "21 (Best of 3)"])
                    details += f"Badminton Doubles: {b_d}. "

        st.session_state.form_data['details_summary'] = details
        
        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next: Final Logistics"):
            st.session_state.step = 4
            st.rerun()

    # --- STEP 4: FRIDAY OPTION & HR NOTES ---
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">Step 4: Logistics & HR Policy</div>', unsafe_allow_html=True)
        
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = st.select_slider("Travel Radius", options=["10 km", "20 km", "30 km"])
        
        st.markdown("### 📝 HR & Event Notes")
        st.warning("🏸 **Note:** Badminton players must bring their own court shoes, racquets, and attire.")
        st.markdown("""<div class="hr-box"><b>📢 HR Policy:</b> Tournament schedules and locations are subject to final HR approval and participation numbers.</div>""", unsafe_allow_html=True)
        
        st.session_state.form_data['ack'] = st.checkbox("I acknowledge the guidelines and attire requirements.")

        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Submit Registration"):
            if st.session_state.form_data['ack']:
                st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(st.session_state.form_data)
                st.session_state.step = 5
                st.balloons()
                st.rerun()
            else: st.error("Please acknowledge the guidelines.")

    # --- STEP 5: RESULTS & SHARE ---
    elif st.session_state.step == 5:
        st.success("✅ Registration Captured!")
        
        # WhatsApp Share
        msg = quote(f"Hey! I registered for the PIPECARE Sports Event. Register here: https://your-link.streamlit.app")
        st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer;">Share via WhatsApp ✅</button></a>', unsafe_allow_html=True)

        st.divider()
        st.subheader("Live Participation Data")
        df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
        if not df.empty:
            st.plotly_chart(px.pie(df, names='schedule', title="Preferred Day Split"), use_container_width=True)
            st.plotly_chart(px.bar(df, x='unit', color='schedule', title="Participation by Unit"), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import random
from urllib.parse import quote

# --- 1. APP CONFIG & THEME ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="centered", page_icon="🏆")

# Custom CSS for PIPECARE branding and UI
st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd; color: #0d47a1; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1976d2; color: white; font-weight: bold; height: 3.5em; border: none; }
    .stButton>button:hover { background-color: #1565c0; border: 1px solid white; }
    .step-header { color: #0d47a1; font-weight: bold; font-size: 1.6rem; margin-bottom: 20px; border-bottom: 3px solid #1976d2; padding-bottom: 8px; }
    .hr-notice { padding: 15px; background-color: #fff3e0; border-left: 6px solid #ff9800; border-radius: 8px; color: #5d4037; font-size: 0.95rem; margin: 15px 0; }
    .config-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #90caf9; margin-bottom: 15px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA HANDLING ---
DB_FILE = 'pipecare_sports_2026.csv'

def save_to_csv(data_dict):
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
    new_entry = pd.DataFrame([data_dict])
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- 3. SESSION STATE ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'verified' not in st.session_state: st.session_state.verified = False
if 'form_data' not in st.session_state: st.session_state.form_data = {}

# --- 4. STEP 0: SECURITY & OTP ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Noida Sports Portal")
    st.info("Authorized Personnel Only")
    
    email = st.text_input("Enter Company Email ID", placeholder="example@pipecaregroup.com")
    
    if st.button("Send Access PIN"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            # For production: use st.secrets and smtplib to send real email.
            st.warning(f"ACCESS PIN (System Generated): {otp}") 
        else:
            st.error("Access Denied: Please use a valid @pipecaregroup.com email.")

    input_otp = st.text_input("Enter 4-Digit PIN", type="password")
    if st.button("Verify & Start Registration"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            st.session_state.step = 1
            st.rerun()
        else:
            st.error("Incorrect PIN. Please try again.")

# --- 5. MULTI-STEP FORM ---
elif st.session_state.step > 0:

    # STEP 1: IDENTITY
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Part 1: Basic Information</div>', unsafe_allow_html=True)
        st.session_state.form_data['Name'] = st.text_input("Full Name*", value=st.session_state.form_data.get('Name', ''))
        st.session_state.form_data['WhatsApp'] = st.text_input("WhatsApp Number*", value=st.session_state.form_data.get('WhatsApp', ''))
        st.session_state.form_data['Unit'] = st.radio("Primary Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Sport Selection ➡️"):
            if st.session_state.form_data['Name'] and st.session_state.form_data['WhatsApp']:
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Required: Please enter your Name and WhatsApp number.")

    # STEP 2: DYNAMIC SPORT CONFIGURATION
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Part 2: Game Preferences</div>', unsafe_allow_html=True)
        
        sports_choice = st.multiselect("Which sports would you like to participate in?", 
                                       ["Cricket", "Badminton", "Table Tennis", "Snooker/Billiards", "Chess", "Carrom", "Other"])
        
        rules_collected = []

        # Cricket Logic
        if "Cricket" in sports_choice:
            st.markdown('<div class="config-card">🏏 <b>Cricket Configuration</b>', unsafe_allow_html=True)
            c_venue = st.selectbox("Preferred Match Venue", ["Proper Cricket Ground", "Box Cricket", "Both/Any"])
            c_ball = st.radio("Ball Preference", ["Tennis Ball", "Leather Ball"], horizontal=True)
            
            if c_venue == "Box Cricket":
                c_team = st.selectbox("Team Size (Box)", [6, 8, 11])
                c_overs = st.select_slider("Overs per Side (Box)", options=[6, 8, 10])
                rules_collected.append(f"Cricket: Box ({c_team}p, {c_overs}ov, {c_ball})")
            else:
                c_ovr_g = st.radio("Match Length (Ground)", ["10 Overs", "20 Overs"], horizontal=True)
                rules_collected.append(f"Cricket: Ground ({c_ovr_g}, {c_ball})")
            st.markdown('</div>', unsafe_allow_html=True)

        # Badminton Logic
        if "Badminton" in sports_choice:
            st.markdown('<div class="config-card">🏸 <b>Badminton Configuration</b>', unsafe_allow_html=True)
            b_cat = st.multiselect("Interested Categories", ["Singles", "Doubles"])
            if "Singles" in b_cat:
                b_s_pts = st.selectbox("Singles Point Format", ["11 Pts (Best of 3)", "15 Pts (Best of 3)", "21 Pts (1 Set)", "21 Pts (Best of 3)"])
                rules_collected.append(f"Badminton Singles: {b_s_pts}")
            if "Doubles" in b_cat:
                b_d_pts = st.selectbox("Doubles Point Format", ["15 Pts (Best of 3)", "21 Pts (Best of 3)"])
                rules_collected.append(f"Badminton Doubles: {b_d_pts}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Other/Blank Option
        if "Other" in sports_choice:
            custom_val = st.text_input("Please specify the game/sport you'd like to suggest:")
            rules_collected.append(f"Custom Sport: {custom_val}")

        st.session_state.form_data['Selected_Sports'] = ", ".join(sports_choice)
        st.session_state.form_data['Rule_Details'] = " | ".join(rules_collected)

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Logistics ➡️"):
            if sports_choice:
                st.session_state.step = 3
                st.rerun()
            else:
                st.error("Please select at least one sport to proceed.")

    # STEP 3: LOGISTICS & HR DISCLOSURE
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Part 3: Final Logistics & Guidelines</div>', unsafe_allow_html=True)
        
        st.session_state.form_data['Day_Pref'] = st.selectbox("Preferred Event Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['Travel_Dist'] = st.radio("Willing to Travel (from Noida Office)", ["Within 10 kms", "Within 20 kms", "Within 30 kms"])
        st.session_state.form_data['Suggestion'] = st.text_area("Any other suggestions for the Sports Committee?")

        st.markdown("### 📝 Event Constraints & Attire")
        st.info("🏸 **Badminton Equipment:** Players must bring their own court-appropriate shoes (non-marking), sports attire, and racquets.")
        st.markdown("""<div class="hr-notice">
            <b>📢 HR Management Policy:</b> Final venue selection, match fixtures, and participation are subject to 
            total registration counts and HR approval. Participation numbers will dictate if certain categories are conducted.
            </div>""", unsafe_allow_html=True)
        
        agree = st.checkbox("I acknowledge the dress code and event guidelines set by HR.")

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Submit Registration 🏆"):
            if agree:
                st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_to_csv(st.session_state.form_data)
                st.session_state.step = 4
                st.balloons()
                st.rerun()
            else:
                st.error("Acknowledgement is required to complete registration.")

    # STEP 4: LIVE RESULTS & DASHBOARD
    elif st.session_state.step == 4:
        st.success("Registration Successful! Your details have been shared with HR.")
        
        # Share on WhatsApp
        app_link = "https://pipecare-sports.streamlit.app" 
        wa_msg = quote(f"Hey! I've registered for the PIPECARE Sports Event. You should too! Register here: {app_link}")
        st.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="background-color:#25D366; color:white; width:100%; border:none; padding:12px; border-radius:10px; font-weight:bold; cursor:pointer;">Invite Team on WhatsApp ✅</button></a>', unsafe_allow_html=True)
        
        st.divider()
        st.subheader("📊 Live Tournament Pulse")
        df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
        if not df.empty:
            st.plotly_chart(px.pie(df, names='Day_Pref', hole=0.4, title="Participation Preference by Day"), use_container_width=True)
            st.plotly_chart(px.histogram(df, x='Unit', color='Day_Pref', barmode='group', title="Office vs Workshop Participation"), use_container_width=True)
        
        if st.button("New Registration"):
            st.session_state.step = 0
            st.session_state.verified = False
            st.rerun()

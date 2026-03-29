import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random
from urllib.parse import quote

# --- 1. SET THEME (MILD SKYBLUE & CORPORATE BLUE) ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="centered", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd; color: #0d47a1; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1976d2; color: white; height: 3em; border: none; font-weight: bold; }
    .step-header { color: #0d47a1; font-weight: bold; font-size: 1.5rem; margin-bottom: 20px; border-bottom: 2px solid #1976d2; padding-bottom: 5px; }
    .hr-box { padding: 15px; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #5d4037; font-size: 0.9rem; margin-top: 10px; }
    .config-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #bbdefb; margin-bottom: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); color: black; }
    .receipt-box { padding: 20px; border-radius: 10px; background: white; border: 2px solid #1976d2; color: black; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & SESSION STATE ---
DB_FILE = 'sports_data_2026.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

if 'step' not in st.session_state: st.session_state.step = 0
if 'verified' not in st.session_state: st.session_state.verified = False
if 'form_data' not in st.session_state: st.session_state.form_data = {}
if 'submitted' not in st.session_state: st.session_state.submitted = False

def save_data(data_dict):
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
    if not df.empty and 'whatsapp' in data_dict:
        df = df[df['whatsapp'] != data_dict['whatsapp']]
    new_df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)

# --- 3. STEP 0: OTP VERIFICATION (GMAIL SMTP) ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Sports Portal")
    st.subheader("Employee Verification")
    email = st.text_input("Company Email", placeholder="user@pipecaregroup.com")
    if st.button("Send Verification Code"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email, f"Subject: PIPECARE Sports Code\n\nYour 4-digit verification code is: {otp}")
                server.quit()
                st.success("OTP Sent! Please check your Outlook/Gmail.")
            except: st.error("Email Error. Please check your st.secrets for GMAIL_USER/PASS.")
    
    input_otp = st.text_input("Enter 4-Digit PIN", type="password")
    if st.button("Verify & Start Registration"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            st.session_state.step = 1
            st.rerun()
        else: st.error("Invalid PIN. Please try again.")

# --- 4. MULTI-STEP FORM LOGIC ---
elif st.session_state.step > 0:

    # --- STEP 1: IDENTITY ---
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Step 1: Basic Information</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Primary Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Participation Type ➡️"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2
                st.rerun()
            else: st.error("Required: Name and WhatsApp Number.")

    # --- STEP 2: ROLE SELECTION ---
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Step 2: Participation Role</div>', unsafe_allow_html=True)
        role = st.selectbox("I am joining as:", ["Athlete (Player)", "Audience/Support", "Not Participating"], 
                            index=["Athlete (Player)", "Audience/Support", "Not Participating"].index(st.session_state.form_data.get('role', "Athlete (Player)")))
        st.session_state.form_data['role'] = role

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Logistics ➡️"):
            st.session_state.step = 5 if role == "Not Participating" else 3
            st.rerun()

    # --- STEP 3: LOGISTICS (BEFORE GAMES) ---
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Step 3: Logistics & Schedule</div>', unsafe_allow_html=True)
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"],
                                                              index=["Friday (Last Working Day)", "Saturday", "Sunday"].index(st.session_state.form_data.get('schedule', "Friday (Last Working Day)")))
        st.session_state.form_data['travel'] = st.select_slider("Willing to Travel (from Office)", options=["10 km", "20 km", "30 km"], value=st.session_state.form_data.get('travel', "20 km"))
        
        st.markdown('<div class="hr-box"><b>📢 HR & Attire Note:</b> Proper sports attire is mandatory. Badminton requires non-marking court shoes. Match schedules are subject to participation numbers.</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next: Game Configuration ➡️"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 5
            st.rerun()

    # --- STEP 4: DETAILED GAME CONFIGURATIONS ---
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">Step 4: Game-Specific Rules</div>', unsafe_allow_html=True)
        
        sports = st.multiselect("Select the games you will play:", ["Cricket", "Badminton", "Table Tennis", "Snooker/Billiards", "Chess", "Carrom", "Other"],
                                default=st.session_state.form_data.get('selected_sports_list', []))
        st.session_state.form_data['selected_sports_list'] = sports
        details = {}

        if "Cricket" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏏 <b>Cricket Configuration</b>', unsafe_allow_html=True)
                c_ways = st.multiselect("Format Choice:", ["Proper Ground", "Box Cricket"], key="c_ways")
                c_ball = st.radio("Ball Type:", ["Tennis", "Leather"], horizontal=True)
                c_res = f"Ball: {c_ball}. "
                if "Box Cricket" in c_ways:
                    c_res += f"Box (Team: {st.selectbox('Box Team Size', [6,8,11])}, Overs: {st.selectbox('Box Overs', [6,8,10])}). "
                if "Proper Ground" in c_ways:
                    c_res += f"Ground ({st.radio('Ground Overs', ['10 Overs', '20 Overs'])}). "
                details['Cricket'] = c_res
                st.markdown('</div>', unsafe_allow_html=True)

        if "Badminton" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏸 <b>Badminton Configuration</b>', unsafe_allow_html=True)
                b_ways = st.multiselect("Category Choice:", ["Singles", "Doubles"], key="b_ways")
                b_res = ""
                if "Singles" in b_ways:
                    b_res += f"Singles: {st.selectbox('Singles Pts Format', ['11 (Best of 3)', '15 (Best of 3)', '21 (1 set)', '21 (Best of 3)'])}; "
                if "Doubles" in b_ways:
                    b_res += f"Doubles: {st.selectbox('Doubles Pts Format', ['15 (Best of 3)', '21 (Best of 3)'])}; "
                details['Badminton'] = b_res
                st.markdown('</div>', unsafe_allow_html=True)

        if "Chess" in sports:
            with st.container():
                st.markdown('<div class="config-card">♟️ <b>Chess Configuration</b>', unsafe_allow_html=True)
                details['Chess'] = f"Chess: {st.radio('Environment', ['Online', 'Offline'], horizontal=True)}, {st.selectbox('Format', ['Knockout', 'Round Robin'])}, {st.select_slider('Duration', ['5 mins', '10 mins', '15 mins'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Table Tennis" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏓 <b>Table Tennis Configuration</b>', unsafe_allow_html=True)
                details['TT'] = f"TT Category: {st.multiselect('TT Category Choice', ['Singles', 'Doubles'])}, Format: {st.radio('Match Best of', ['3 Sets (11 pts)', '5 Sets (11 pts)'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Snooker/Billiards" in sports:
            with st.container():
                st.markdown('<div class="config-card">🎱 <b>Snooker & Billiards</b>', unsafe_allow_html=True)
                details['Snooker'] = f"{st.radio('Game Selection', ['Snooker', 'Billiards'])}, Style: {st.selectbox('Format Style', ['Point Based (Timed)', 'Frame Based'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Carrom" in sports:
            with st.container():
                st.markdown('<div class="config-card">⚪ <b>Carrom Configuration</b>', unsafe_allow_html=True)
                details['Carrom'] = f"Format: {st.radio('Carrom Choice', ['Singles', 'Doubles'])}, Rule: {st.selectbox('Winning criteria', ['First to 25 pts', 'Best of 3 Boards', '15 mins Timed'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Other" in sports:
            details['Other'] = st.text_input("Other Game Suggestion & Rule Preference:")

        st.session_state.form_data['game_details'] = str(details)
        st.session_state.form_data['suggestions'] = st.text_area("Final suggestions for HR?")
        
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Review & Finalize ➡️"):
            if sports:
                st.session_state.step = 5
                st.rerun()
            else: st.error("Please select at least one sport to play.")

    # --- STEP 5: FINAL RECEIPT & LIVE ANALYTICS (SIDE-BY-SIDE) ---
    elif st.session_state.step == 5:
        st.markdown('<div class="step-header">Step 5: Review & Submission</div>', unsafe_allow_html=True)
        
        if not st.session_state.submitted:
            # PRE-SUBMISSION REVIEW
            st.write("### Confirm Your Registration Details")
            col_rev1, col_rev2 = st.columns(2)
            with col_rev1:
                st.write(f"**Name:** {st.session_state.form_data['name']}")
                st.write(f"**Unit:** {st.session_state.form_data['unit']}")
                st.write(f"**Role:** {st.session_state.form_data['role']}")
            with col_rev2:
                st.write(f"**WhatsApp:** {st.session_state.form_data['whatsapp']}")
                st.write(f"**Schedule:** {st.session_state.form_data.get('schedule', 'N/A')}")
                st.write(f"**Travel Radius:** {st.session_state.form_data.get('travel', 'N/A')}")
            
            st.info(f"**Game Selections:** {st.session_state.form_data.get('game_details', 'None (Audience/Not Attending)')}")
            
            c1, c2 = st.columns(2)
            if c1.button("✍️ Edit/Go Back"):
                st.session_state.step = 1
                st.rerun()
            if c2.button("🚀 Confirm & Submit Registration"):
                st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(st.session_state.form_data)
                st.session_state.submitted = True
                st.balloons()
                st.rerun()
        
        else:
            # POST-SUBMISSION VIEW: RECEIPT + LIVE CHARTS
            st.success("✅ Submission Successful! Thank you for registering.")
            
            res_col1, res_col2 = st.columns([1, 1.2], gap="large")
            
            with res_col1:
                st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
                st.subheader("📄 Your Receipt")
                st.write(f"**Player:** {st.session_state.form_data['name']}")
                st.write(f"**Status:** {st.session_state.form_data['role']}")
                st.write(f"**Preferred Day:** {st.session_state.form_data.get('schedule')}")
                st.write(f"**Games Configured:** {st.session_state.form_data.get('game_details')}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button("🔄 Edit/Update My Entry"):
                    st.session_state.submitted = False
                    st.session_state.step = 1
                    st.rerun()
                
                # WhatsApp Share Logic
                app_link = "https://your-pipecare-sports.streamlit.app" 
                wa_msg = quote(f"Hey! I registered for the PIPECARE Sports Event. Register yours here: {app_link}")
                st.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; font-weight:bold; cursor:pointer; margin-top:10px;">Share Link via WhatsApp ✅</button></a>', unsafe_allow_html=True)

            with res_col2:
                st.subheader("📊 Live Event Pulse")
                df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
                if not df.empty:
                    # Chart 1: Role Distribution
                    fig1 = px.pie(df, names='role', hole=0.4, title="Participation Split")
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    # Chart 2: Preferred Day by Unit
                    if 'schedule' in df.columns:
                        fig2 = px.histogram(df[df['role']!='Not Participating'], x='schedule', color='unit', barmode='group', title="Attendance Preference by Unit")
                        st.plotly_chart(fig2, use_container_width=True)

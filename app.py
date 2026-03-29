import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random
from urllib.parse import quote

# --- 1. SET THEME ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="centered", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #e3f2fd; color: #0d47a1; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1976d2; color: white; height: 3em; border: none; font-weight: bold; }
    .step-header { color: #0d47a1; font-weight: bold; font-size: 1.5rem; margin-bottom: 20px; border-bottom: 2px solid #1976d2; padding-bottom: 5px; }
    .hr-box { padding: 15px; background-color: #fff3e0; border-left: 5px solid #ff9800; border-radius: 5px; color: #5d4037; font-size: 0.9rem; margin-top: 10px; }
    .config-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #bbdefb; margin-bottom: 15px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
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
            except Exception as e: 
                st.error("Email Error. Check your Streamlit Secrets setup.")
    
    input_otp = st.text_input("Enter 4-Digit Code", type="password")
    if st.button("Verify & Start"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            st.session_state.step = 1
            st.rerun()
        else: st.error("Incorrect PIN.")

# --- 4. MULTI-STEP FORM ---
elif st.session_state.step > 0:

    # --- STEP 1: IDENTITY ---
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Step 1: Identity</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Participation Type"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2
                st.rerun()
            else: st.error("Please fill Name and WhatsApp.")

    # --- STEP 2: PARTICIPATION ROLE ---
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Step 2: Participation Role</div>', unsafe_allow_html=True)
        role = st.selectbox("I am joining as:", ["Athlete (Player)", "Audience/Support", "Not Participating"])
        st.session_state.form_data['role'] = role

        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Logistics"):
            st.session_state.step = 5 if role == "Not Participating" else 3
            st.rerun()

    # --- STEP 3: LOGISTICS (WHEN & WHERE) ---
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Step 3: Logistics & Schedule</div>', unsafe_allow_html=True)
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = st.select_slider("Willing to Travel", options=["10 km", "20 km", "30 km"])
        
        st.markdown('<div class="hr-box"><b>📢 HR & Attire Note:</b> Appropriate sports attire required. Badminton requires non-marking shoes. Final venue decided by total registrations.</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next: Game Configuration"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 5
            st.rerun()

    # --- STEP 4: GAME CONFIGURATIONS (MULTI-WAY PLAYING LOGIC) ---
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">Step 4: Custom Game Rules</div>', unsafe_allow_html=True)
        
        sports = st.multiselect("Select your games:", ["Cricket", "Badminton", "Table Tennis", "Snooker/Billiards", "Chess", "Carrom", "Other"])
        details = {}

        if "Cricket" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏏 <b>Cricket Configuration</b>', unsafe_allow_html=True)
                c_ways = st.multiselect("Select one or both ways to play:", ["Proper Ground", "Box Cricket"])
                c_ball = st.multiselect("Select ball preference(s):", ["Tennis", "Leather"])
                
                c_summary = []
                if "Box Cricket" in c_ways:
                    c_summary.append(f"Box ({st.selectbox('Box Team', [6,8,11])}p, {st.selectbox('Box Overs', [6,8,10])}ov)")
                if "Proper Ground" in c_ways:
                    c_summary.append(f"Ground ({st.radio('Ground Match Type', ['10 Overs', '20 Overs'])})")
                
                details['cricket'] = f"{' & '.join(c_ways)} | Ball: {', '.join(c_ball)} | Rules: {'; '.join(c_summary)}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Badminton" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏸 <b>Badminton Configuration</b>', unsafe_allow_html=True)
                b_ways = st.multiselect("Category(s):", ["Singles", "Doubles"])
                b_det = []
                if "Singles" in b_ways:
                    b_det.append(f"Singles ({st.selectbox('Singles Format', ['11 Pts (3 sets)', '15 Pts (3 sets)', '21 Pts (1 set)', '21 Pts (3 sets)'])})")
                if "Doubles" in b_ways:
                    b_det.append(f"Doubles ({st.selectbox('Doubles Format', ['15 Pts (3 sets)', '21 Pts (3 sets)'])})")
                
                details['badminton'] = f"{' & '.join(b_ways)} | {'; '.join(b_det)}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Chess" in sports:
            with st.container():
                st.markdown('<div class="config-card">♟️ <b>Chess Configuration</b>', unsafe_allow_html=True)
                c_ways = st.multiselect("Mode:", ["Online", "Offline"])
                details['chess'] = f"Chess ({', '.join(c_ways)}) | {st.selectbox('Tournament', ['Knockout', 'Round Robin'])} | {st.select_slider('Duration', ['5 mins', '10 mins', '15 mins'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Table Tennis" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏓 <b>Table Tennis Configuration</b>', unsafe_allow_html=True)
                t_ways = st.multiselect("TT Category:", ["Singles", "Doubles"])
                details['tt'] = f"TT ({', '.join(t_ways)}) | {st.radio('Best of Format', ['3 Sets (11 pts)', '5 Sets (11 pts)'], horizontal=True)}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Snooker/Billiards" in sports:
            with st.container():
                st.markdown('<div class="config-card">🎱 <b>Snooker/Billiards Configuration</b>', unsafe_allow_html=True)
                s_ways = st.multiselect("Game Type:", ["Snooker", "Billiards"])
                details['snooker'] = f"{', '.join(s_ways)} | {st.selectbox('Match Style', ['Point Based', 'Frame Based (Best of 3)'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Carrom" in sports:
            with st.container():
                st.markdown('<div class="config-card">⚪ <b>Carrom Configuration</b>', unsafe_allow_html=True)
                cr_ways = st.multiselect("Carrom Category:", ["Singles", "Doubles"])
                details['carrom'] = f"Carrom ({', '.join(cr_ways)}) | {st.selectbox('Winning Criteria', ['First to 25 pts', 'Best of 3 Boards', '15 min Timed'])}"
                st.markdown('</div>', unsafe_allow_html=True)

        if "Other" in sports:
            details['other'] = st.text_input("Custom Sport & Preferred Rules:")

        st.session_state.form_data['game_details'] = str(details)
        
        col1, col2 = st.columns(2)
        if col1.button("Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Final Review & Submit"):
            if sports:
                st.session_state.step = 5
                st.rerun()
            else: st.error("Select at least one game.")

    # --- STEP 5: FINAL CONFIRM & SAVE ---
    elif st.session_state.step == 5:
        st.markdown('<div class="step-header">Step 5: Review & Save</div>', unsafe_allow_html=True)
        
        st.write(f"**Name:** {st.session_state.form_data['name']}")
        st.write(f"**Role:** {st.session_state.form_data['role']}")
        
        if st.session_state.form_data['role'] != "Not Participating":
            st.write(f"**Preferred Schedule:** {st.session_state.form_data.get('schedule')}")
            st.info(f"**Game Configuration:** {st.session_state.form_data.get('game_details', 'Audience only')}")
        
        if st.button("Finalize Registration 🏆"):
            st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(st.session_state.form_data)
            st.balloons()
            st.success("Successfully Registered! You can close this app.")
            
        st.divider()
        st.subheader("Live Stats")
        df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
        if not df.empty:
            st.plotly_chart(px.pie(df, names='role', title="Attendance Split"), use_container_width=True)

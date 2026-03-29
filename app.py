import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import smtplib
import random
from urllib.parse import quote
import ast

# --- 1. PRO THEME & UI ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #f0f4f8; color: #102a43; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #243b53; color: white; height: 3.5em; font-weight: bold; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #334e68; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .step-header { color: #102a43; font-weight: 800; font-size: 1.8rem; margin-bottom: 15px; border-bottom: 4px solid #48bb78; padding-bottom: 10px; }
    .config-card { background: white; padding: 25px; border-radius: 15px; border: 1px solid #d9e2ec; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: #102a43; }
    .hr-notice { padding: 20px; background-color: #fffaf0; border-left: 6px solid #f6ad55; border-radius: 8px; color: #7b341e; font-size: 1rem; margin: 20px 0; }
    .receipt-box { padding: 25px; border-radius: 15px; background: #ffffff; border: 2px solid #243b53; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & AUTH CONFIG ---
DB_FILE = 'pipecare_sports_final.csv'
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

# --- 3. STEP 0: SECURE OTP ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Noida Sports Portal")
    st.subheader("Official Employee Verification")
    email = st.text_input("Enter Company Email", placeholder="name@pipecaregroup.com")
    
    if st.button("Generate Access PIN"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email, f"Subject: PIPECARE Sports PIN\n\nYour 4-digit PIN: {otp}")
                server.quit()
                st.success("Verification PIN sent to your Outlook.")
            except: st.error("Email Error. Verify st.secrets setup.")
    
    input_otp = st.text_input("Enter PIN", type="password")
    if st.button("Verify & Start Registration"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            st.session_state.step = 1
            st.rerun()
        else: st.error("Invalid PIN.")

# --- 4. MULTI-STEP FORM LOGIC ---
elif st.session_state.step > 0:

    # STEP 1: IDENTITY
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">01. Identity & Location</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        st.session_state.form_data['name'] = c1.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = c2.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Primary Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Participation Role ➡️"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2
                st.rerun()
            else: st.error("Name and WhatsApp are mandatory.")

    # STEP 2: ROLE
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">02. Participation Role</div>', unsafe_allow_html=True)
        role = st.selectbox("I am joining as:", ["Athlete (Player)", "Audience/Support", "Not Participating"], 
                            index=["Athlete (Player)", "Audience/Support", "Not Participating"].index(st.session_state.form_data.get('role', "Athlete (Player)")))
        st.session_state.form_data['role'] = role

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Logistics ➡️"):
            st.session_state.step = 5 if role == "Not Participating" else 3
            st.rerun()

    # STEP 3: LOGISTICS (BEFORE GAMES)
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">03. Logistics & Schedule</div>', unsafe_allow_html=True)
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = st.select_slider("Willing to Travel from Office", options=["10 km", "20 km", "30 km"])
        
        st.markdown('<div class="hr-notice"><b>📢 HR & ATTIRE POLICY:</b> Proper sports gear is required. Badminton participants MUST bring their own non-marking court shoes, attire, and racquets. Final schedules depend on registration density.</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next: Game Configuration ➡️"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 5
            st.rerun()

    # STEP 4: DETAILED GAME CONFIG
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">04. Game Specific Rules</div>', unsafe_allow_html=True)
        
        sports = st.multiselect("Select your game(s):", ["Cricket", "Badminton", "Table Tennis", "Snooker/Billiards", "Chess", "Carrom", "Other"], 
                                default=st.session_state.form_data.get('selected_list', []))
        st.session_state.form_data['selected_list'] = sports
        rules = {}

        if "Cricket" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏏 <b>Cricket</b>', unsafe_allow_html=True)
                c_ways = st.multiselect("Format Choice:", ["Proper Ground", "Box Cricket"])
                c_ball = st.radio("Ball Preference:", ["Tennis", "Leather"], horizontal=True)
                c_data = {"Ball": c_ball, "Formats": c_ways}
                if "Box Cricket" in c_ways:
                    c_data["Box_Team"] = st.selectbox("Box Team Size", [6, 8, 11])
                    c_data["Box_Overs"] = st.selectbox("Box Overs", [6, 8, 10])
                if "Proper Ground" in c_ways:
                    c_data["Ground_Overs"] = st.radio("Ground Overs", ["10 Overs", "20 Overs"])
                rules['Cricket'] = c_data
                st.markdown('</div>', unsafe_allow_html=True)

        if "Badminton" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏸 <b>Badminton</b>', unsafe_allow_html=True)
                b_cat = st.multiselect("Category Choice:", ["Singles", "Doubles"])
                b_data = {"Categories": b_cat}
                if "Singles" in b_cat:
                    b_data["Singles_Pts"] = st.selectbox("Singles Point System", ["11 (3 sets)", "15 (3 sets)", "21 (1 set)", "21 (3 sets)"])
                if "Doubles" in b_cat:
                    b_data["Doubles_Pts"] = st.selectbox("Doubles Point System", ["15 (3 sets)", "21 (3 sets)"])
                rules['Badminton'] = b_data
                st.markdown('</div>', unsafe_allow_html=True)

        if "Chess" in sports:
            with st.container():
                st.markdown('<div class="config-card">♟️ <b>Chess</b>', unsafe_allow_html=True)
                rules['Chess'] = {
                    "Mode": st.radio("Environment", ["Online", "Offline"], horizontal=True),
                    "Format": st.selectbox("Format", ["Knockout", "Round Robin"]),
                    "Timer": st.select_slider("Duration", ["5 mins", "10 mins", "15 mins"])
                }
                st.markdown('</div>', unsafe_allow_html=True)

        if "Table Tennis" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏓 <b>Table Tennis</b>', unsafe_allow_html=True)
                rules['TT'] = {
                    "Mode": st.multiselect("Format ", ["Singles", "Doubles"]),
                    "Rules": st.radio("Match Best of", ["3 Sets (11 pts)", "5 Sets (11 pts)"])
                }
                st.markdown('</div>', unsafe_allow_html=True)

        if "Snooker/Billiards" in sports:
            with st.container():
                st.markdown('<div class="config-card">🎱 <b>Snooker/Billiards</b>', unsafe_allow_html=True)
                rules['Snooker'] = {
                    "Game": st.radio("Game Type", ["Snooker", "Billiards"]),
                    "Style": st.selectbox("Scoring", ["Point Based", "Frame Based"])
                }
                st.markdown('</div>', unsafe_allow_html=True)

        if "Carrom" in sports:
            with st.container():
                st.markdown('<div class="config-card">⚪ <b>Carrom</b>', unsafe_allow_html=True)
                rules['Carrom'] = {
                    "Mode": st.radio("Carrom Format", ["Singles", "Doubles"]),
                    "Winning": st.selectbox("Criteria", ["First to 25 pts", "Best of 3 Boards", "15 mins Timed"])
                }
                st.markdown('</div>', unsafe_allow_html=True)

        if "Other" in sports:
            rules['Other'] = st.text_input("Specify Game and Preferred Rules:")

        st.session_state.form_data['game_rules'] = str(rules)
        st.session_state.form_data['suggestions'] = st.text_area("Final comments/suggestions for HR?")

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Review & Finish ➡️"):
            if sports: st.session_state.step = 5; st.rerun()
            else: st.error("Please select a game.")

    # STEP 5: RECEIPT & PRO DASHBOARD
    elif st.session_state.step == 5:
        st.markdown('<div class="step-header">05. Validation & Live Pulse</div>', unsafe_allow_html=True)
        
        if not st.session_state.submitted:
            # PRE-SUBMISSION
            st.write("### Confirm Your Registration Details")
            st.info(f"**Employee:** {st.session_state.form_data['name']} | **WhatsApp:** {st.session_state.form_data['whatsapp']}")
            st.write(f"**Selection:** {st.session_state.form_data.get('game_rules', 'Audience/Not Participating')}")
            
            c1, c2 = st.columns(2)
            if c1.button("✍️ Edit Entry"): st.session_state.step = 1; st.rerun()
            if c2.button("🚀 Submit Final Registration"):
                st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(st.session_state.form_data)
                st.session_state.submitted = True
                st.balloons()
                st.rerun()
        
        else:
            # POST-SUBMISSION: RECEIPT BESIDE DASHBOARD
            st.success("✅ Success! Your registration is captured.")
            
            dash_l, dash_r = st.columns([1, 1.5], gap="large")
            
            with dash_l:
                st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
                st.subheader("Personal Receipt")
                st.write(f"**{st.session_state.form_data['name']}** ({st.session_state.form_data['unit']})")
                st.write(f"**Role:** {st.session_state.form_data['role']}")
                st.write(f"**Preferred Day:** {st.session_state.form_data.get('schedule')}")
                st.write("**Rules Configured:**")
                st.write(st.session_state.form_data.get('game_rules'))
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button("🔄 Change/Update Response"):
                    st.session_state.submitted = False
                    st.session_state.step = 1; st.rerun()
                
                app_url = "https://your-app.streamlit.app"
                wa_msg = quote(f"Hey! I registered for PIPECARE Sports 2026. Join here: {app_url}")
                st.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:10px; font-weight:bold; cursor:pointer; margin-top:10px;">Share via WhatsApp ✅</button></a>', unsafe_allow_html=True)

            with dash_r:
                st.subheader("💹 Real-Time Analytics")
                df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
                if not df.empty:
                    # Metric Row
                    m1, m2 = st.columns(2)
                    m1.metric("Total Players", len(df[df['role'] == "Athlete (Player)"]))
                    m2.metric("Noida Workshop Participation", len(df[df['unit'] == "Noida Workshop"]))
                    
                    # Pro Charts
                    fig1 = px.pie(df, names='role', hole=0.5, title="Attendance Topology", color_discrete_sequence=px.colors.qualitative.Prism)
                    st.plotly_chart(fig1, use_container_width=True)
                    
                    if 'schedule' in df.columns:
                        fig2 = px.histogram(df[df['role']!='Not Participating'], x='schedule', color='unit', barmode='group', title="Logistics Heatmap")
                        st.plotly_chart(fig2, use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
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
    .stApp { background-color: #f8fafc; color: #0f172a; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #1e293b; color: white; height: 3.5em; font-weight: bold; border: none; }
    .step-header { color: #1e293b; font-weight: 800; font-size: 2rem; border-bottom: 4px solid #10b981; padding-bottom: 10px; margin-bottom: 25px; }
    .config-card { background: white; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: black; }
    .hr-notice { padding: 20px; background-color: #fffbeb; border-left: 6px solid #f59e0b; border-radius: 8px; color: #92400e; font-size: 1rem; }
    .receipt-box { padding: 30px; border-radius: 20px; background: #ffffff; border: 2px solid #1e293b; color: black; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & EMAIL CORE ---
DB_FILE = 'pipecare_sports_vfinal.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

if 'step' not in st.session_state: st.session_state.step = 0
if 'verified' not in st.session_state: st.session_state.verified = False
if 'form_data' not in st.session_state: st.session_state.form_data = {}
if 'submitted' not in st.session_state: st.session_state.submitted = False

def send_mail(to_email, subject, body):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, to_email, f"Subject: {subject}\n\n{body}")
        server.quit()
        return True
    except: return False

def save_data(data_dict):
    df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
    if not df.empty and 'whatsapp' in data_dict:
        # Ensure WhatsApp is treated as string for matching
        df['whatsapp'] = df['whatsapp'].astype(str)
        df = df[df['whatsapp'] != str(data_dict['whatsapp'])]
    new_df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)

def check_existing_user(email):
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        existing = df[df['email'] == email]
        if not existing.empty:
            return existing.iloc[-1].to_dict()
    return None

# --- 3. IDENTITY & PERSISTENCE ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Noida Sports Portal")
    email = st.text_input("Corporate Email", placeholder="user@pipecaregroup.com")
    
    if st.button("Request Access PIN"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            if send_mail(email, "PIPECARE Sports PIN", f"Your Access PIN: {otp}"):
                st.success("PIN sent to Outlook.")
            else: st.error("Email Error. Check Secrets.")
    
    input_otp = st.text_input("Enter PIN", type="password")
    if st.button("Verify & Continue"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            user_record = check_existing_user(email)
            if user_record:
                st.session_state.form_data = user_record
                # Parse strings back to dictionaries for the UI
                if isinstance(st.session_state.form_data.get('game_rules'), str):
                    st.session_state.form_data['game_rules'] = ast.literal_eval(st.session_state.form_data['game_rules'])
                if isinstance(st.session_state.form_data.get('selected_list'), str):
                    st.session_state.form_data['selected_list'] = ast.literal_eval(st.session_state.form_data['selected_list'])
                st.session_state.submitted = True
                st.session_state.step = 5
            else:
                st.session_state.form_data['email'] = email
                st.session_state.step = 1
            st.rerun()

# --- 4. MULTI-STEP FLOW ---
elif st.session_state.step < 5:
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">01. Identity</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Full Name", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp Number", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Primary Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        if st.button("Next: Participation Type ➡️"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">02. Participation Role</div>', unsafe_allow_html=True)
        role_options = ["Athlete (Player)", "Audience/Support", "Not Participating"]
        default_role = st.session_state.form_data.get('role', "Athlete (Player)")
        role = st.selectbox("I am joining as:", role_options, index=role_options.index(default_role))
        st.session_state.form_data['role'] = role
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next: Logistics ➡️"):
            st.session_state.step = 5 if role == "Not Participating" else 3
            st.rerun()

    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">03. Logistics & Schedule</div>', unsafe_allow_html=True)
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = st.select_slider("Willing to Travel", options=["10 km", "20 km", "30 km"])
        st.markdown('<div class="hr-notice"><b>📢 HR Note:</b> Badminton requires non-marking shoes. Final venue depends on registration density.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next: Game Configuration ➡️"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 5
            st.rerun()

    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">04. Game Specific Rules</div>', unsafe_allow_html=True)
        sports_options = ["Cricket", "Badminton", "Table Tennis", "Snooker/Billiards", "Chess", "Carrom", "Other"]
        sports = st.multiselect("Select your game(s):", sports_options, default=st.session_state.form_data.get('selected_list', []))
        st.session_state.form_data['selected_list'] = sports
        rules = {}

        if "Cricket" in sports:
            with st.container():
                st.markdown('<div class="config-card">🏏 <b>Cricket</b>', unsafe_allow_html=True)
                c_ways = st.multiselect("Format Choice:", ["Proper Ground", "Box Cricket"])
                c_ball = st.radio("Ball Preference:", ["Tennis", "Leather"], horizontal=True)
                c_data = {"Ball": c_ball, "Formats": c_ways}
                if "Box Cricket" in c_ways:
                    c_data["Box_Team"] = st.selectbox("Box Team Strength", [6, 8, 11])
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
                    "Mode": st.radio("Mode", ["Online", "Offline"], horizontal=True),
                    "Format": st.selectbox("Match Style", ["Knockout", "Round Robin"]),
                    "Timer": st.select_slider("Time Control", ["5 mins", "10 mins", "15 mins"])
                }
                st.markdown('</div>', unsafe_allow_html=True)

        st.session_state.form_data['game_rules'] = rules
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Review & Finalize ➡️"):
            if sports: st.session_state.step = 5; st.rerun()
            else: st.error("Please select a game.")

# --- 5. ELITE ANALYTICS & RECEIPT ---
elif st.session_state.step == 5:
    if not st.session_state.submitted:
        st.markdown('<div class="step-header">05. Final Review</div>', unsafe_allow_html=True)
        st.info(f"Reviewing for **{st.session_state.form_data['name']}**")
        c1, c2 = st.columns(2)
        if c1.button("✍️ Edit Entry"): st.session_state.step = 1; st.rerun()
        if c2.button("🚀 Confirm & Submit"):
            st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(st.session_state.form_data)
            receipt_msg = f"PIPECARE Sports 2026 Registration Confirmed.\nGames: {st.session_state.form_data.get('game_rules')}\nDay: {st.session_state.form_data.get('schedule')}"
            send_mail(st.session_state.form_data['email'], "Confirmed: Noida Sports", receipt_msg)
            st.session_state.submitted = True
            st.balloons(); st.rerun()
    else:
        st.success("✅ Registration Active. Welcome back!")
        dash_l, dash_r = st.columns([1, 2], gap="large")
        with dash_l:
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.subheader("Your Submission")
            st.write(f"**Name:** {st.session_state.form_data['name']}")
            st.write(f"**Role:** {st.session_state.form_data['role']} | **Day:** {st.session_state.form_data.get('schedule')}")
            st.json(st.session_state.form_data.get('game_rules'))
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("Edit My Response"): 
                st.session_state.submitted = False; st.session_state.step = 1; st.rerun()

        with dash_r:
            st.subheader("📊 Elite Event Analytics")
            df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
            if not df.empty:
                # Safely parse game_rules for plotting
                df['game_rules'] = df['game_rules'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                c_a, c_b = st.columns(2)
                c_a.plotly_chart(px.pie(df, names='role', hole=0.5, title="Role Topology"), use_container_width=True)
                c_b.plotly_chart(px.bar(df, x='travel', color='unit', title="Travel Capacity"), use_container_width=True)
                
                # Dynamic Cricket Rule Analytics
                st.markdown("### 🔍 Rule Deep-Dive")
                c_balls = [r['Cricket']['Ball'] for r in df['game_rules'] if isinstance(r, dict) and 'Cricket' in r]
                if c_balls:
                    st.plotly_chart(px.pie(values=pd.Series(c_balls).value_counts(), names=pd.Series(c_balls).value_counts().index, title="Cricket: Ball Preference"), use_container_width=True)

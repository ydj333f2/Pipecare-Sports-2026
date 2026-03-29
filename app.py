import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random
from urllib.parse import quote
import ast

# --- 1. PRO THEME & CONFIG ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; color: #0f172a; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #1e293b; color: white; height: 3.5em; font-weight: bold; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #334155; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .step-header { color: #1e293b; font-weight: 800; font-size: 2rem; border-bottom: 4px solid #10b981; padding-bottom: 10px; margin-bottom: 25px; }
    .config-card { background: white; padding: 25px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .hr-notice { padding: 20px; background-color: #fffbeb; border-left: 6px solid #f59e0b; border-radius: 8px; color: #92400e; font-size: 1rem; }
    .receipt-box { padding: 30px; border-radius: 20px; background: #ffffff; border: 2px solid #1e293b; color: #1e293b; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
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
        df = df[df['whatsapp'] != data_dict['whatsapp']]
    new_df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)

def check_existing(email):
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        existing = df[df['email'] == email]
        if not existing.empty:
            return existing.iloc[-1].to_dict()
    return None

# --- 3. IDENTITY VERIFICATION & PERSISTENCE ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Noida Sports Portal")
    email = st.text_input("Corporate Email", placeholder="user@pipecaregroup.com")
    
    if st.button("Request Access PIN"):
        if "@pipecaregroup.com" in email.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            if send_mail(email, "PIPECARE Sports PIN", f"Your Access PIN: {otp}"):
                st.success("PIN sent to Outlook.")
            else: st.error("Email Error. Check Secrets config.")
    
    input_otp = st.text_input("Enter PIN", type="password")
    if st.button("Verify & Continue"):
        if input_otp == st.session_state.get('otp_val'):
            st.session_state.verified = True
            user_record = check_existing(email)
            if user_record:
                st.session_state.form_data = user_record
                if isinstance(st.session_state.form_data.get('game_rules'), str):
                    st.session_state.form_data['game_rules'] = ast.literal_eval(st.session_state.form_data['game_rules'])
                st.session_state.submitted = True
                st.session_state.step = 5
            else:
                st.session_state.form_data['email'] = email
                st.session_state.step = 1
            st.rerun()

# --- 4. STEP-BY-STEP FLOW ---
elif st.session_state.step < 5:
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">Step 1: Identity</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Name", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        if st.button("Next ➡️"): st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">Step 2: Role</div>', unsafe_allow_html=True)
        st.session_state.form_data['role'] = st.selectbox("I am joining as:", ["Athlete (Player)", "Audience/Support", "Not Participating"])
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next ➡️"):
            st.session_state.step = 5 if st.session_state.form_data['role'] == "Not Participating" else 3
            st.rerun()

    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">Step 3: Logistics (Before Games)</div>', unsafe_allow_html=True)
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = st.select_slider("Willing to Travel", options=["10 km", "20 km", "30 km"])
        st.markdown('<div class="hr-notice"><b>📢 HR Note:</b> Proper attire is mandatory. Badminton requires non-marking shoes.</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next ➡️"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 5
            st.rerun()

    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">Step 4: Game Specifics</div>', unsafe_allow_html=True)
        s_list = st.multiselect("Select Games:", ["Cricket", "Badminton", "Chess", "Table Tennis", "Other"])
        rules = {}
        if "Cricket" in s_list:
            with st.container():
                st.markdown('<div class="config-card">🏏 <b>Cricket</b>', unsafe_allow_html=True)
                rules['Cricket'] = {"Ball": st.radio("Ball", ["Tennis", "Leather"], horizontal=True), 
                                    "Team": st.selectbox("Team Size", [6,8,11]), "Overs": st.selectbox("Overs", [6,8,10,20])}
        if "Badminton" in s_list:
            with st.container():
                st.markdown('<div class="config-card">🏸 <b>Badminton</b>', unsafe_allow_html=True)
                rules['Badminton'] = {"Category": st.multiselect("Category", ["Singles", "Doubles"]), "Pts": st.selectbox("Pts", ["11 (3 sets)", "21 (3 sets)"])}
        if "Chess" in s_list:
            with st.container():
                st.markdown('<div class="config-card">♟️ <b>Chess</b>', unsafe_allow_html=True)
                rules['Chess'] = {"Mode": st.radio("Mode", ["Online", "Offline"], horizontal=True), "Time": st.select_slider("Duration", ["5m", "10m", "15m"])}
        
        st.session_state.form_data['game_rules'] = rules
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Review ➡️"): st.session_state.step = 5; st.rerun()

# --- 5. ELITE DASHBOARD & PERSISTENCE ---
elif st.session_state.step == 5:
    if not st.session_state.submitted:
        st.markdown('<div class="step-header">05. Finalize</div>', unsafe_allow_html=True)
        st.write(f"Reviewing profile for **{st.session_state.form_data['name']}**")
        if st.button("Confirm & Submit Registration 🚀"):
            st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(st.session_state.form_data)
            receipt_body = f"Hello {st.session_state.form_data['name']},\n\nYour registration is confirmed.\nGames: {st.session_state.form_data.get('game_rules')}\nSchedule: {st.session_state.form_data.get('schedule')}"
            send_mail(st.session_state.form_data['email'], "Confirmed: PIPECARE Sports 2026", receipt_body)
            st.session_state.submitted = True
            st.rerun()
    else:
        st.success("✅ Registration Active. Welcome back!")
        d_l, d_r = st.columns([1, 2], gap="large")
        with d_l:
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.subheader("Your Submission")
            st.write(f"**Name:** {st.session_state.form_data['name']}")
            st.write(f"**Unit:** {st.session_state.form_data['unit']}")
            st.json(st.session_state.form_data.get('game_rules'))
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("Edit My Response"): st.session_state.submitted = False; st.session_state.step = 1; st.rerun()

        with d_r:
            st.subheader("📊 Elite Event Analytics")
            df = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame()
            if not df.empty:
                df['game_rules'] = df['game_rules'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
                c_1, c_2 = st.columns(2)
                c_1.plotly_chart(px.pie(df, names='role', hole=0.5, title="Role Topology"), use_container_width=True)
                c_2.plotly_chart(px.bar(df, x='travel', color='unit', title="Travel Logistics"), use_container_width=True)
                
                # Game-specific rule parsing for Elite Analytics
                c_balls = [r['Cricket']['Ball'] for r in df['game_rules'] if isinstance(r, dict) and 'Cricket' in r]
                if c_balls:
                    st.plotly_chart(px.pie(values=pd.Series(c_balls).value_counts(), names=pd.Series(c_balls).value_counts().index, title="Cricket: Ball Preference Heatmap"), use_container_width=True)

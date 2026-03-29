import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta
import smtplib
import random
import ast

# --- 1. PRO CONFIG ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    .stButton>button { width: 100%; border-radius: 12px; background-color: #1e293b; color: white; height: 3.5em; font-weight: bold; border: none; }
    .step-header { color: #1e293b; font-weight: 800; font-size: 2rem; border-bottom: 4px solid #10b981; padding-bottom: 10px; margin-bottom: 25px; }
    .config-card { background: white; padding: 30px; border-radius: 15px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: black; }
    .hr-notice { padding: 20px; background-color: #fffbeb; border-left: 6px solid #f59e0b; border-radius: 8px; color: #92400e; font-size: 1rem; }
    .receipt-box { padding: 30px; border-radius: 20px; background: #ffffff; border: 2px solid #1e293b; color: black; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = 'pipecare_sports_vfinal.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

# --- 2. DATA ENGINE ---
@st.cache_data
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def safe_parse(val):
    try:
        return ast.literal_eval(val) if isinstance(val, str) else val
    except:
        return {}

def save_data(data_dict):
    df = load_data()
    if not df.empty:
        df = df[df['email'] != data_dict['email']]
    new_df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)
    st.cache_data.clear()

# --- 3. SESSION STATE ---
defaults = {
    "step": 0, "verified": False, "submitted": False,
    "form_data": {"game_rules": {}}, "game_queue": [], "queue_index": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 4. AUTH ---
if not st.session_state.verified:
    st.title("🏆 Noida Sports Portal")
    email = st.text_input("Corporate Email (@pipecaregroup.com)")

    if st.button("Send Access PIN"):
        if email.endswith("@pipecaregroup.com"):
            otp = str(random.randint(1000, 9999))
            st.session_state.otp_val = otp
            st.session_state.otp_time = datetime.now()
            
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email, f"Subject: Sports PIN\n\nYour Access PIN: {otp}")
                server.quit()
                st.success("PIN sent. Valid for 5 mins.")
            except:
                st.error("Email failed. Check st.secrets.")

    input_otp = st.text_input("Enter 4-Digit PIN", type="password")

    if st.button("Verify Identity"):
        if 'otp_val' in st.session_state:
            if datetime.now() - st.session_state.otp_time > timedelta(minutes=5):
                st.error("OTP expired")
            elif input_otp == st.session_state.otp_val:
                st.session_state.verified = True
                df = load_data()
                existing = df[df['email'] == email] if not df.empty else pd.DataFrame()
                if not existing.empty:
                    st.session_state.form_data = existing.iloc[-1].to_dict()
                    st.session_state.form_data['game_rules'] = safe_parse(st.session_state.form_data.get('game_rules'))
                    st.session_state.form_data['selected_list'] = safe_parse(st.session_state.form_data.get('selected_list', '[]'))
                    st.session_state.submitted = True
                    st.session_state.step = 100
                else:
                    st.session_state.form_data['email'] = email
                    st.session_state.step = 1
                st.rerun()

# --- 5. DYNAMIC FLOW ---
elif st.session_state.step != 100:

    if st.session_state.step == 1:
        st.markdown('<div class="step-header">01. Identity</div>', unsafe_allow_html=True)
        st.session_state.form_data['name'] = st.text_input("Name", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = st.text_input("WhatsApp", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
        if st.button("Next"): st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">02. Role</div>', unsafe_allow_html=True)
        role = st.selectbox("Role", ["Athlete (Player)", "Audience/Support", "Not Participating"])
        st.session_state.form_data['role'] = role
        if st.button("Next"):
            st.session_state.step = 100 if role == "Not Participating" else 3
            st.rerun()

    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">03. Logistics</div>', unsafe_allow_html=True)
        st.session_state.form_data['schedule'] = st.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = st.select_slider("Travel Radius", options=["10 km", "20 km", "30 km"])
        st.markdown('<div class="hr-notice"><b>📢 Note:</b> Badminton requires non-marking shoes. Friday events start after 3:00 PM.</div>', unsafe_allow_html=True)
        if st.button("Next"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 100
            st.rerun()

    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">04. Sport Selection</div>', unsafe_allow_html=True)
        sports = st.multiselect("Select Games", ["Cricket", "Badminton", "Table Tennis", "Chess", "Carrom", "Other"])
        if st.button("Next: Configure Each Game ➡️"):
            if sports:
                st.session_state.form_data['selected_list'] = sports
                st.session_state.game_queue = sports
                st.session_state.queue_index = 0
                st.session_state.step = 10; st.rerun()
            else: st.error("Select at least one sport.")

    elif st.session_state.step == 10:
        game = st.session_state.game_queue[st.session_state.queue_index]
        st.markdown(f'<div class="step-header">Config: {game} ({st.session_state.queue_index + 1}/{len(st.session_state.game_queue)})</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            if game == "Cricket":
                c_ways = st.multiselect("Format", ["Proper Ground", "Box Cricket"], key="cw")
                c_ball = st.radio("Ball", ["Tennis", "Leather"], horizontal=True)
                rules = {"Ball": c_ball, "Formats": c_ways}
                if "Box Cricket" in c_ways:
                    rules["Box_Team"] = st.selectbox("Team Size", [6, 8, 11])
                    rules["Box_Overs"] = st.selectbox("Overs", [6, 8, 10])
                if "Proper Ground" in c_ways:
                    rules["Ground_Overs"] = st.radio("Ground Overs", ["10 Overs", "20 Overs"])
                st.session_state.form_data['game_rules']['Cricket'] = rules
            
            elif game == "Badminton":
                b_cat = st.multiselect("Category", ["Singles", "Doubles"])
                st.session_state.form_data['game_rules']['Badminton'] = {"Cat": b_cat, "Pts": st.selectbox("Point System", ["11 (3 sets)", "15 (3 sets)", "21 (1 set)", "21 (3 sets)"])}
            
            elif game == "Chess":
                st.session_state.form_data['game_rules']['Chess'] = {"Mode": st.radio("Mode", ["Online", "Offline"]), "Time": st.select_slider("Duration", ["5 mins", "10 mins", "15 mins"])}
            
            elif game == "Other":
                st.session_state.form_data['other_name'] = st.text_input("Name of Sport & Rules")
            st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"):
            if st.session_state.queue_index > 0: st.session_state.queue_index -= 1
            else: st.session_state.step = 4
            st.rerun()
        if col2.button("Next Game ➡️" if st.session_state.queue_index < len(st.session_state.game_queue) - 1 else "Finish ➡️"):
            if st.session_state.queue_index < len(st.session_state.game_queue) - 1:
                st.session_state.queue_index += 1
            else: st.session_state.step = 100
            st.rerun()

# --- 6. DASHBOARD ---
elif st.session_state.step == 100:
    if not st.session_state.submitted:
        st.markdown('<div class="step-header">Review & Submit</div>', unsafe_allow_html=True)
        st.json(st.session_state.form_data)
        if st.button("🚀 Confirm Submission"):
            st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(st.session_state.form_data)
            st.session_state.submitted = True; st.rerun()
    else:
        st.success("✅ Registration Active.")
        dl, dr = st.columns([1, 2], gap="large")
        with dl:
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.subheader("Your Submission")
            st.write(f"**Name:** {st.session_state.form_data['name']}")
            st.json(st.session_state.form_data.get('game_rules'))
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("✍️ Edit Entry"): 
                st.session_state.submitted = False; st.session_state.step = 1; st.rerun()

        with dr:
            st.subheader("📊 Live Event Pulse")
            df = load_data()
            if not df.empty:
                df['game_rules'] = df['game_rules'].apply(safe_parse)
                c1, c2 = st.columns(2)
                c1.plotly_chart(px.pie(df, names='role', hole=0.5, title="Participation Split"), use_container_width=True)
                c2.plotly_chart(px.bar(df, x='travel', color='unit', title="Travel Logistics"), use_container_width=True)
                
                # Cricket Rule Deep-Dive
                c_balls = [r['Cricket']['Ball'] for r in df['game_rules'] if isinstance(r, dict) and 'Cricket' in r]
                if c_balls:
                    st.plotly_chart(px.pie(values=pd.Series(c_balls).value_counts(), names=pd.Series(c_balls).value_counts().index, title="Cricket Ball Consensus", hole=0.3), use_container_width=True)

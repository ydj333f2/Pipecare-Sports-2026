import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta
import smtplib
import random
import json

# ==========================================
# 1. ENTERPRISE CONFIGURATION & UI STYLING
# ==========================================
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    /* Premium Corporate UI */
    .stApp { background-color: #f4f7f6; color: #1a202c; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2b6cb0; color: white; height: 3.2em; font-weight: 600; border: none; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #2c5282; box-shadow: 0 4px 12px rgba(43, 108, 176, 0.2); transform: translateY(-2px); }
    .step-header { color: #2d3748; font-weight: 800; font-size: 2.2rem; border-bottom: 3px solid #3182ce; padding-bottom: 8px; margin-bottom: 25px; }
    .config-card { background: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.03); color: #2d3748; }
    .alert-box { padding: 15px; background-color: #fffaf0; border-left: 5px solid #dd6b20; border-radius: 6px; color: #c05621; font-size: 0.95rem; margin-bottom: 20px; }
    .ticket-box { padding: 30px; border-radius: 15px; background: linear-gradient(135deg, #ffffff 0%, #f7fafc 100%); border: 1px solid #cbd5e0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); color: #1a202c; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = 'pipecare_sports_master.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

# ==========================================
# 2. CORE DATA ENGINE & PERSISTENCE
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def safe_json_parse(val):
    """Safely converts stringified JSON back into Python dictionaries."""
    try:
        return json.loads(val) if isinstance(val, str) else val
    except:
        return {}

def save_data(data_dict):
    """Saves user data. Overwrites existing entry if email matches."""
    df = load_data()
    save_dict = data_dict.copy()
    
    # Strictly serialize dictionaries/lists to JSON for flat CSV storage
    save_dict['game_rules'] = json.dumps(save_dict.get('game_rules', {}))
    save_dict['selected_list'] = json.dumps(save_dict.get('selected_list', []))
    
    if not df.empty and 'email' in df.columns:
        df = df[df['email'] != save_dict['email']]
        
    new_df = pd.concat([df, pd.DataFrame([save_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)
    st.cache_data.clear() # Clear cache to instantly reflect on Analytics dashboard

def send_mail(to_email, subject, body):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASS)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(GMAIL_USER, to_email, message)
        server.quit()
        return True
    except:
        return False

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
defaults = {
    "step": 0, "verified": False, "submitted": False,
    "form_data": {"game_rules": {}}, "game_queue": [], "queue_index": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==========================================
# 4. SECURE OTP AUTHENTICATION (STEP 0)
# ==========================================
if not st.session_state.verified:
    st.title("🏆 PIPECARE Sports Portal")
    st.markdown("Please authenticate using your corporate email address.")
    
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Corporate Email", placeholder="employee@pipecaregroup.com")
        if st.button("Generate Secure PIN"):
            if email.endswith("@pipecaregroup.com"):
                otp = str(random.randint(1000, 9999))
                st.session_state.otp_val = otp
                st.session_state.otp_time = datetime.now()
                if send_mail(email, "PIPECARE Sports Auth PIN", f"Your secure login PIN is: {otp}\nThis PIN is valid for 5 minutes."):
                    st.success("PIN sent to your inbox.")
                else:
                    st.error("Email delivery failed. Check SMTP configurations.")
            else:
                st.error("Unauthorized Domain. Use @pipecaregroup.com")

    with col2:
        input_otp = st.text_input("Enter 4-Digit PIN", type="password")
        if st.button("Verify Identity"):
            if 'otp_val' in st.session_state:
                if datetime.now() - st.session_state.otp_time > timedelta(minutes=5):
                    st.error("Security Timeout: PIN has expired.")
                elif input_otp == st.session_state.otp_val:
                    st.session_state.verified = True
                    
                    # --- PERSISTENCE LOGIC ---
                    df = load_data()
                    existing = df[df['email'] == email] if not df.empty else pd.DataFrame()
                    if not existing.empty:
                        # User exists! Load their previous data and jump to the Dashboard
                        st.session_state.form_data = existing.iloc[-1].to_dict()
                        st.session_state.form_data['game_rules'] = safe_json_parse(st.session_state.form_data.get('game_rules'))
                        st.session_state.form_data['selected_list'] = safe_json_parse(st.session_state.form_data.get('selected_list', '[]'))
                        st.session_state.submitted = True
                        st.session_state.step = 100 
                    else:
                        # New user! Start the registration flow
                        st.session_state.form_data['email'] = email
                        st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("Invalid PIN.")

# ==========================================
# 5. DYNAMIC REGISTRATION FLOW (STEPS 1-10)
# ==========================================
elif st.session_state.step != 100:

    # --- STEP 1: IDENTITY ---
    if st.session_state.step == 1:
        st.markdown('<div class="step-header">01. Employee Profile</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        st.session_state.form_data['name'] = col1.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = col2.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Primary Unit*", ["Noida Office", "Noida Workshop"], horizontal=True)
        
        if st.button("Next: Participation Role ➡️"):
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2; st.rerun()
            else:
                st.error("Name and WhatsApp are mandatory fields.")

    # --- STEP 2: ROLE ---
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">02. Participation Role</div>', unsafe_allow_html=True)
        role = st.selectbox("I am joining as:", ["Athlete (Player)", "Audience/Support", "Not Participating"])
        st.session_state.form_data['role'] = role
        
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if col2.button("Next Step ➡️"):
            st.session_state.step = 100 if role == "Not Participating" else 3
            st.rerun()

    # --- STEP 3: LOGISTICS ---
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">03. Logistics & Schedule</div>', unsafe_allow_html=True)
        st.markdown('<div class="alert-box"><b>📢 HR Policy:</b> Friday events commence after 3:00 PM. Badminton requires proper non-marking shoes.</div>', unsafe_allow_html=True)
        
        col_s, col_t = st.columns(2)
        st.session_state.form_data['schedule'] = col_s.selectbox("Preferred Day", ["Friday (Last Working Day)", "Saturday", "Sunday"])
        st.session_state.form_data['travel'] = col_t.select_slider("Travel Radius Willingness", options=["10 km", "20 km", "30 km"])
            
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if col2.button("Next Step ➡️"):
            st.session_state.step = 4 if st.session_state.form_data['role'] == "Athlete (Player)" else 100
            st.rerun()

    # --- STEP 4: SPORT SELECTION ---
    elif st.session_state.step == 4:
        st.markdown('<div class="step-header">04. Tournament Entry</div>', unsafe_allow_html=True)
        sports = st.multiselect("Select your events:", ["Cricket", "Badminton", "Table Tennis", "Chess", "Carrom", "Snooker", "Other"])
        
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"): st.session_state.step = 3; st.rerun()
        if col2.button("Configure Match Rules ➡️"):
            if sports:
                st.session_state.form_data['selected_list'] = sports
                st.session_state.game_queue = sports
                st.session_state.queue_index = 0
                st.session_state.form_data['game_rules'] = {} # Clean slate for rules
                st.session_state.step = 10; st.rerun()
            else:
                st.error("Select at least one event.")

    # --- STEP 10: DYNAMIC NESTED CONFIGURATION (THE QUEUE) ---
    elif st.session_state.step == 10:
        game = st.session_state.game_queue[st.session_state.queue_index]
        st.markdown(f'<div class="step-header">Configuring: {game} <span style="font-size: 1.2rem; color: #718096;">(Sport {st.session_state.queue_index + 1} of {len(st.session_state.game_queue)})</span></div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="config-card">', unsafe_allow_html=True)
            
            # 🏏 CRICKET (Fully Nested)
            if game == "Cricket":
                c_ball = st.radio("Primary Ball Preference", ["Tennis", "Leather"], horizontal=True)
                c_fmts = st.multiselect("Select Formats (Choose multiple if playing both):", ["Proper Ground", "Box Cricket"])
                c_rules = {"Ball": c_ball, "Formats": {}}
                
                if "Proper Ground" in c_fmts:
                    st.markdown("#### 🏟️ Proper Ground Specification")
                    col_c1, col_c2 = st.columns(2)
                    c_rules["Formats"]["Proper Ground"] = {
                        "Overs": col_c1.selectbox("Overs Format", [10, 15, 20], key="g_ov"),
                        "Team": col_c2.selectbox("Squad Size", [11, 15, 18], key="g_tm")
                    }
                
                if "Box Cricket" in c_fmts:
                    st.markdown("#### 📦 Box Cricket Specification")
                    col_b1, col_b2 = st.columns(2)
                    c_rules["Formats"]["Box Cricket"] = {
                        "Overs": col_b1.selectbox("Overs Format", [6, 8, 10], key="b_ov"),
                        "Team": col_b2.selectbox("Team Strength", [6, 7, 8, 11], key="b_tm")
                    }
                st.session_state.form_data['game_rules']['Cricket'] = c_rules

            # 🏸 BADMINTON (Fully Nested)
            elif game == "Badminton":
                b_fmts = st.multiselect("Bracket Entry (Choose multiple if playing both):", ["Singles", "Doubles"])
                b_rules = {"Formats": {}}
                
                if "Singles" in b_fmts:
                    st.markdown("#### 👤 Singles Bracket")
                    col_s1, col_s2 = st.columns(2)
                    b_rules["Formats"]["Singles"] = {
                        "Points": col_s1.selectbox("Scoring System", ["11 Pts", "15 Pts", "21 Pts"], key="s_pts"),
                        "Sets": col_s2.selectbox("Match Length", ["Best of 3", "Best of 5"], key="s_set")
                    }
                if "Doubles" in b_fmts:
                    st.markdown("#### 👥 Doubles Bracket")
                    col_d1, col_d2 = st.columns(2)
                    b_rules["Formats"]["Doubles"] = {
                        "Points": col_d1.selectbox("Scoring System", ["15 Pts", "21 Pts"], key="d_pts"),
                        "Sets": col_d2.selectbox("Match Length", ["Best of 3", "Best of 5"], key="d_set")
                    }
                st.session_state.form_data['game_rules']['Badminton'] = b_rules

            # ♟️ CHESS
            elif game == "Chess":
                col_ch1, col_ch2, col_ch3 = st.columns(3)
                st.session_state.form_data['game_rules']['Chess'] = {
                    "Mode": col_ch1.radio("Environment", ["Online", "Offline"]),
                    "Timer": col_ch2.selectbox("Time Control", ["5m (Blitz)", "10m (Rapid)", "15m (Standard)"]),
                    "Structure": col_ch3.selectbox("Tournament Style", ["Knockout", "Round Robin"])
                }

            # 🏓 TABLE TENNIS
            elif game == "Table Tennis":
                st.session_state.form_data['game_rules']['Table Tennis'] = {
                    "Categories": st.multiselect("Tournament Entry", ["Singles", "Doubles"]),
                    "Format": st.radio("Match Length", ["Best of 3 (11 Pts)", "Best of 5 (11 Pts)"], horizontal=True)
                }

            # 🎱 SNOOKER & BILLIARDS
            elif game == "Snooker/Billiards":
                col_sn1, col_sn2 = st.columns(2)
                st.session_state.form_data['game_rules']['Snooker'] = {
                    "Game": col_sn1.radio("Table Game", ["Snooker", "Billiards"]),
                    "Format": col_sn2.selectbox("Scoring Style", ["Point Based", "Frame Based (Best of 3)"])
                }

            # ⚪ CARROM
            elif game == "Carrom":
                col_ca1, col_ca2 = st.columns(2)
                st.session_state.form_data['game_rules']['Carrom'] = {
                    "Category": col_ca1.radio("Format", ["Singles", "Doubles"]),
                    "Victory": col_ca2.selectbox("Winning Condition", ["First to 25 Points", "Best of 3 Boards", "Timed (15m)"])
                }

            # ➕ OTHER
            elif game == "Other":
                st.session_state.form_data['other_desc'] = st.text_area("Specify Sport, Preferred Rules, and Equipment Needs:")
                
            else:
                st.info("Configuration captured. Click Next to proceed.")

            st.markdown('</div>', unsafe_allow_html=True)

        # Dynamic Queue Navigation
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Previous Screen"):
            if st.session_state.queue_index > 0: st.session_state.queue_index -= 1
            else: st.session_state.step = 4
            st.rerun()
            
        is_last = st.session_state.queue_index >= len(st.session_state.game_queue) - 1
        if col2.button("Review & Submit ➡️" if is_last else "Next Event ➡️"):
            if is_last: st.session_state.step = 100
            else: st.session_state.queue_index += 1
            st.rerun()

# ==========================================
# 6. FINAL REVIEW & ELITE DASHBOARD
# ==========================================
elif st.session_state.step == 100:
    
    # 6A. PRE-SUBMISSION REVIEW
    if not st.session_state.submitted:
        st.markdown('<div class="step-header">Final Review & Consent</div>', unsafe_allow_html=True)
        st.write("### Registration Manifest")
        st.json(st.session_state.form_data)
        
        st.markdown("---")
        consent = st.checkbox("I verify that my selections are correct and I adhere to the PIPECARE Code of Conduct.")
        
        col1, col2 = st.columns(2)
        if col1.button("⬅️ Edit Selections"):
            st.session_state.step = 1
            st.rerun()
            
        if col2.button("✅ Confirm & Transmit", disabled=not consent):
            st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            save_data(st.session_state.form_data)
            
            # Send Email Receipt
            receipt_msg = f"Hello {st.session_state.form_data['name']},\n\nYour enrollment for the PIPECARE 2026 Sports Event is confirmed.\nRole: {st.session_state.form_data.get('role')}\nUnit: {st.session_state.form_data.get('unit')}\nSchedule: {st.session_state.form_data.get('schedule', 'N/A')}\n\nSports Selected: {', '.join(st.session_state.form_data.get('selected_list', []))}\n\nThank you,\nPIPECARE Event Team"
            send_mail(st.session_state.form_data['email'], "PIPECARE Registration Confirmed", receipt_msg)
            
            st.session_state.submitted = True
            st.balloons()
            st.rerun()
            
    # 6B. POST-SUBMISSION DASHBOARD
    else:
        st.success("✅ Secure Session Active. Welcome to the Command Center.")
        tab1, tab2 = st.tabs(["🎫 My Ticket", "📊 Global Analytics Dashboard"])
        
        with tab1:
            st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
            st.markdown("## 🎟️ Official Digital Ticket")
            st.write(f"**Employee Name:** {st.session_state.form_data.get('name')}")
            st.write(f"**Affiliation:** {st.session_state.form_data.get('unit')}")
            st.write(f"**Designation:** {st.session_state.form_data.get('role')}")
            if st.session_state.form_data.get('role') == "Athlete (Player)":
                st.write(f"**Availability:** {st.session_state.form_data.get('schedule')}")
                st.markdown("### Approved Configurations:")
                st.json(st.session_state.form_data.get('game_rules'))
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.write("")
            if st.button("🔄 Modify Registration"): 
                st.session_state.submitted = False; st.session_state.step = 1; st.rerun()

        with tab2:
            st.markdown("### Real-Time Event Telemetry")
            df = load_data()
            if not df.empty:
                # Ensure all JSON strings are parsed back to python dicts for Analytics
                df['game_rules'] = df['game_rules'].apply(safe_json_parse)
                
                # High-Level KPIs
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Headcount", len(df))
                m2.metric("Active Athletes", len(df[df['role'].str.contains("Athlete", na=False)]))
                m3.metric("Support Staff", len(df[df['role'].str.contains("Audience", na=False)]))
                m4.metric("Workshop Ratio", f"{(len(df[df['unit'] == 'Noida Workshop']) / len(df) * 100):.1f}%" if len(df)>0 else "0%")

                st.divider()
                
                # General Logistics Charts
                c1, c2 = st.columns(2)
                c1.plotly_chart(px.pie(df, names='role', hole=0.4, title="Demographic Split", color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
                c2.plotly_chart(px.histogram(df[df['role']!='Not Participating'], x='schedule', color='unit', barmode='group', title="Logistical Load per Day"), use_container_width=True)
                
                st.markdown("### 🎯 Multi-Sport Deep Extraction")
                row1_col1, row1_col2 = st.columns(2)
                row2_col1, row2_col2 = st.columns(2)

                # 1. Cricket Analytics
                cricket_data = [fmt for rules in df['game_rules'] if isinstance(rules, dict) and 'Cricket' in rules and 'Formats' in rules['Cricket'] for fmt in rules['Cricket']['Formats'].keys()]
                if cricket_data:
                    row1_col1.plotly_chart(px.pie(names=pd.Series(cricket_data).value_counts().index, values=pd.Series(cricket_data).value_counts().values, title="Cricket: Ground vs Box", hole=0.3, color_discrete_sequence=['#3182ce', '#dd6b20']), use_container_width=True)

                # 2. Badminton Analytics
                badminton_data = [fmt for rules in df['game_rules'] if isinstance(rules, dict) and 'Badminton' in rules and 'Formats' in rules['Badminton'] for fmt in rules['Badminton']['Formats'].keys()]
                if badminton_data:
                    row1_col2.plotly_chart(px.bar(pd.Series(badminton_data).value_counts(), title="Badminton: Singles vs Doubles Demand", color_discrete_sequence=['#38a169']), use_container_width=True)

                # 3. Chess Analytics
                chess_data = [rules['Chess'].get('Mode') for rules in df['game_rules'] if isinstance(rules, dict) and 'Chess' in rules and 'Mode' in rules['Chess']]
                if chess_data:
                    row2_col1.plotly_chart(px.pie(names=pd.Series(chess_data).value_counts().index, values=pd.Series(chess_data).value_counts().values, title="Chess: Online vs Offline", hole=0.3, color_discrete_sequence=['#805ad5', '#e53e3e']), use_container_width=True)

                # 4. Carrom Analytics
                carrom_data = [rules['Carrom'].get('Victory') for rules in df['game_rules'] if isinstance(rules, dict) and 'Carrom' in rules and 'Victory' in rules['Carrom']]
                if carrom_data:
                    row2_col2.plotly_chart(px.bar(pd.Series(carrom_data).value_counts(), title="Carrom: Preferred Winning Conditions", color_discrete_sequence=['#d69e2e']), use_container_width=True)

import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import json

# ==========================================
# 1. ENTERPRISE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; color: #1a202c; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #2b6cb0; color: white; height: 3em; font-weight: 600; border: none; transition: all 0.3s ease; }
    .stButton>button:hover { background-color: #2c5282; transform: translateY(-1px); }
    .step-header { color: #2d3748; font-weight: 800; font-size: 2.2rem; border-bottom: 3px solid #3182ce; padding-bottom: 8px; margin-bottom: 20px; }
    .ticket-box { padding: 30px; border-radius: 15px; background: white; border: 1px solid #cbd5e0; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = 'pipecare_sports_master.csv'

# ==========================================
# 2. DATA LAYER
# ==========================================
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def safe_json(val):
    try: return json.loads(val) if isinstance(val, str) else val
    except: return {}

def save_data(data_dict):
    df = load_data()
    save_dict = data_dict.copy()
    save_dict['game_rules'] = json.dumps(save_dict.get('game_rules', {}))
    save_dict['selected_list'] = json.dumps(save_dict.get('selected_list', []))
    if not df.empty and 'email' in df.columns:
        df = df[df['email'] != save_dict['email']]
    new_df = pd.concat([df, pd.DataFrame([save_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)
    st.cache_data.clear()

# ==========================================
# 3. SECURE AUTHENTICATION (Bypasses Firewall)
# ==========================================
if 'verified_email' not in st.session_state:
    st.title("🏆 PIPECARE Noida Sports Portal")
    st.info("First time? Enter email and create a 4-digit PIN. Returning? Use your PIN to edit.")
    
    col1, col2 = st.columns(2)
    email_in = col1.text_input("Corporate Email", placeholder="name@pipecaregroup.com").lower().strip()
    pin_in = col2.text_input("Access PIN (4 Digits)", type="password")

    if st.button("Enter Portal 🔓"):
        if not email_in.endswith("@pipecaregroup.com"):
            st.error("Access Denied: Use @pipecaregroup.com only.")
        elif len(pin_in) != 4 or not pin_in.isdigit():
            st.error("PIN must be exactly 4 digits.")
        else:
            df = load_data()
            existing = df[df['email'] == email_in] if not df.empty else pd.DataFrame()
            
            if not existing.empty:
                if str(existing.iloc[-1]['pin']) == str(pin_in):
                    rec = existing.iloc[-1].to_dict()
                    rec['game_rules'] = safe_json(rec.get('game_rules'))
                    rec['selected_list'] = safe_json(rec.get('selected_list'))
                    st.session_state.form_data = rec
                    st.session_state.verified_email = email_in
                    st.session_state.step = 100 # Direct to Dashboard
                    st.rerun()
                else: st.error("Incorrect PIN for this email.")
            else:
                st.session_state.verified_email = email_in
                st.session_state.form_data = {'email': email_in, 'pin': pin_in, 'game_rules': {}}
                st.session_state.step = 1; st.rerun()

# ==========================================
# 4. RESTORED REGISTRATION FLOW
# ==========================================
elif st.session_state.step != 100:
    
    if st.session_state.step == 1:
        st.markdown(f'<div class="step-header">01. Profile: {st.session_state.verified_email}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        st.session_state.form_data['name'] = c1.text_input("Full Name*", value=st.session_state.form_data.get('name', ''))
        st.session_state.form_data['whatsapp'] = c2.text_input("WhatsApp Number*", value=st.session_state.form_data.get('whatsapp', ''))
        st.session_state.form_data['unit'] = st.radio("Primary Unit*", ["Noida Office", "Noida Workshop"], horizontal=True)
        if st.button("Next: Role ➡️"): 
            if st.session_state.form_data['name'] and st.session_state.form_data['whatsapp']:
                st.session_state.step = 2; st.rerun()
            else: st.error("Fields required.")

    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">02. Participation Role</div>', unsafe_allow_html=True)
        role = st.selectbox("I am joining as:", ["Athlete (Player)", "Audience/Support", "Not Participating"], 
                            index=["Athlete (Player)", "Audience/Support", "Not Participating"].index(st.session_state.form_data.get('role', "Athlete (Player)")))
        st.session_state.form_data['role'] = role
        if st.button("Next Step ➡️"):
            st.session_state.step = 3 if role != "Not Participating" else 100
            st.rerun()

    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">03. Logistics & Events</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        st.session_state.form_data['schedule'] = c1.selectbox("Preferred Day", ["Friday", "Saturday", "Sunday"])
        sports = st.multiselect("Select your events:", ["Cricket", "Badminton", "Table Tennis", "Chess", "Carrom", "Snooker", "Other"], default=st.session_state.form_data.get('selected_list', []))
        
        if st.button("Configure Match Rules ➡️"):
            if sports:
                st.session_state.form_data['selected_list'] = sports
                st.session_state.game_queue = sports
                st.session_state.q_idx = 0
                st.session_state.step = 10; st.rerun()
            else: st.error("Select at least one event.")

    elif st.session_state.step == 10:
        game = st.session_state.game_queue[st.session_state.q_idx]
        st.markdown(f'<div class="step-header">Configuring: {game}</div>', unsafe_allow_html=True)
        rules = st.session_state.form_data['game_rules'].get(game, {})

        if game == "Cricket":
            ball = st.radio("Ball Preference", ["Tennis", "Leather"], horizontal=True)
            fmt = st.multiselect("Formats", ["Proper Ground", "Box Cricket"], default=rules.get('fmt', []))
            st.session_state.form_data['game_rules'][game] = {'ball': ball, 'fmt': fmt}

        elif game == "Badminton":
            cats = st.multiselect("Category", ["Singles", "Doubles"], default=rules.get('cat', []))
            b_rules = {'cat': cats}
            if "Singles" in cats:
                st.markdown("#### Singles Config")
                col1, col2 = st.columns(2)
                b_rules['s_pts'] = col1.selectbox("Points", ["11 Pts", "21 Pts"], key="bs1")
                b_rules['s_set'] = col2.selectbox("Match Length", ["Best of 3", "Best of 5"], key="bs2")
            if "Doubles" in cats:
                st.markdown("#### Doubles Config")
                col1, col2 = st.columns(2)
                b_rules['d_pts'] = col1.selectbox("Points", ["15 Pts", "21 Pts"], key="bd1")
                b_rules['d_set'] = col2.selectbox("Match Length", ["Best of 3", "Best of 5"], key="bd2")
            st.session_state.form_data['game_rules'][game] = b_rules

        elif game == "Table Tennis":
            cat = st.multiselect("Entry", ["Singles", "Doubles"], default=rules.get('cat', []))
            fmt = st.radio("Format", ["Best of 3 (11 Pts)", "Best of 5 (11 Pts)"], horizontal=True)
            st.session_state.form_data['game_rules'][game] = {'cat': cat, 'fmt': fmt}

        elif game == "Chess":
            st.session_state.form_data['game_rules'][game] = {'mode': st.radio("Mode", ["Online", "Offline"]), 'timer': st.selectbox("Timer", ["5m", "10m", "15m"])}

        elif game == "Snooker":
            st.session_state.form_data['game_rules'][game] = {'type': st.radio("Type", ["Snooker", "Billiards"])}

        elif game == "Carrom":
            st.session_state.form_data['game_rules'][game] = {'cat': st.radio("Format", ["Singles", "Doubles"])}

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Previous"):
            if st.session_state.q_idx > 0: st.session_state.q_idx -= 1
            else: st.session_state.step = 3
            st.rerun()
        
        is_last = st.session_state.q_idx >= len(st.session_state.game_queue) - 1
        if col2.button("Finalize ✅" if is_last else "Next Event ➡️"):
            if is_last:
                st.session_state.form_data['Timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_data(st.session_state.form_data)
                st.session_state.step = 100
            else: st.session_state.q_idx += 1
            st.rerun()

# ==========================================
# 5. DASHBOARD & ANALYTICS
# ==========================================
else:
    st.success("✅ Secure Session Active. Welcome to the Command Center.")
    tab1, tab2 = st.tabs(["🎫 My Ticket", "📊 Global Analytics"])
    
    with tab1:
        st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
        st.header("🎟️ Official Digital Ticket")
        st.write(f"**Name:** {st.session_state.form_data.get('name')}")
        st.write(f"**Unit:** {st.session_state.form_data.get('unit')}")
        st.write(f"**Events:** {', '.join(st.session_state.form_data.get('selected_list', []))}")
        st.json(st.session_state.form_data.get('game_rules'))
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("🔄 Edit Registration"): st.session_state.step = 1; st.rerun()

    with tab2:
        df = load_data()
        if not df.empty:
            df['game_rules'] = df['game_rules'].apply(safe_json)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Players", len(df))
            m2.metric("Noida Office", len(df[df['unit']=='Noida Office']))
            m3.metric("Noida Workshop", len(df[df['unit']=='Noida Workshop']))
            st.plotly_chart(px.pie(df, names='role', hole=0.4, title="Demographic Split"), use_container_width=True)

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import urllib.parse

# ==========================================
# 1. ADMIN CONFIGURATION
# ==========================================
# REPLACE WITH YOUR WHATSAPP NUMBER (with country code, no '+')
ADMIN_WHATSAPP = "918328099699" 
# THE PIN YOU WILL GIVE TO EMPLOYEES WHO MESSAGE YOU
DAILY_ACCESS_PIN = "8899" 
DB_FILE = 'pipecare_sports_master.csv'

st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; color: #1e293b; }
    .auth-card { padding: 30px; background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .wa-link { 
        background-color: #25D366; color: white; padding: 12px 20px; 
        border-radius: 8px; text-decoration: none; font-weight: bold;
        display: inline-block; margin: 10px 0; border: none;
    }
    .step-header { color: #2b6cb0; font-weight: 800; font-size: 2.2rem; border-bottom: 2px solid #e2e8f0; margin-bottom: 20px; }
    .ticket-box { border-left: 5px solid #2b6cb0; padding: 20px; background: #f0f9ff; border-radius: 8px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA PERSISTENCE ENGINE
# ==========================================
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def save_or_update(data_dict):
    df = load_data()
    # Serialize for CSV compatibility
    data_dict['selected_list'] = json.dumps(data_dict.get('selected_list', []))
    data_dict['game_rules'] = json.dumps(data_dict.get('game_rules', {}))
    
    if not df.empty and 'mobile' in df.columns:
        # Match by mobile to allow re-editing/overwriting
        df = df[df['mobile'].astype(str) != str(data_dict['mobile'])]
        
    new_df = pd.concat([df, pd.DataFrame([data_dict])], ignore_index=True)
    new_df.to_csv(DB_FILE, index=False)
    st.cache_data.clear()

def safe_json(val):
    try:
        return json.loads(val) if isinstance(val, str) else val
    except: return []

# ==========================================
# 3. SECURE AUTHENTICATION (The Gate)
# ==========================================
if 'auth_active' not in st.session_state:
    st.title("🏆 PIPECARE Noida Sports Portal")
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    
    st.subheader("Step 1: Identity Verification")
    mobile_num = st.text_input("Mobile Number", placeholder="98XXXXXXXX")
    
    if mobile_num:
        message = f"Hello Admin, I am registering for Noida Sports. Mobile: {mobile_num}. Please send PIN."
        wa_url = f"https://wa.me/{ADMIN_WHATSAPP}?text={urllib.parse.quote(message)}"
        st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">Request PIN via WhatsApp ✅</a>', unsafe_allow_html=True)

    entered_pin = st.text_input("Enter 4-Digit Access PIN", type="password")
    
    if st.button("Enter Portal 🔓"):
        if entered_pin == DAILY_ACCESS_PIN:
            st.session_state.auth_active = True
            st.session_state.user_mobile = mobile_num
            
            # LOAD EXISTING DATA FOR RE-EDITING
            df = load_data()
            if not df.empty and (df['mobile'].astype(str) == str(mobile_num)).any():
                rec = df[df['mobile'].astype(str) == str(mobile_num)].iloc[-1].to_dict()
                rec['selected_list'] = safe_json(rec.get('selected_list'))
                rec['game_rules'] = safe_json(rec.get('game_rules', '{}'))
                st.session_state.form_data = rec
                st.toast("Record Found! You can now update your details.")
            else:
                st.session_state.form_data = {'mobile': mobile_num, 'game_rules': {}}
            
            st.session_state.step = 1
            st.rerun()
        else: st.error("Invalid PIN.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. REGISTRATION / RE-EDIT FLOW
# ==========================================
elif st.session_state.step != 100:
    st.markdown(f'<div class="step-header">Session: +91 {st.session_state.user_mobile}</div>', unsafe_allow_html=True)
    
    if st.session_state.step == 1:
        st.subheader("👤 Profile Details")
        name = st.text_input("Full Name", value=st.session_state.form_data.get('name', ''))
        email = st.text_input("Corporate Email (@pipecaregroup.com)", value=st.session_state.form_data.get('email', ''))
        unit = st.radio("Unit", ["Noida Office", "Noida Workshop"], index=0 if st.session_state.form_data.get('unit')!="Noida Workshop" else 1)
        
        if st.button("Next ➡️"):
            if name and email.endswith("@pipecaregroup.com"):
                st.session_state.form_data.update({'name': name, 'email': email, 'unit': unit})
                st.session_state.step = 2; st.rerun()
            else: st.error("Valid name and corporate email required.")

    elif st.session_state.step == 2:
        st.subheader("🎾 Tournament Selection")
        sports = st.multiselect("Select Games", ["Cricket", "Badminton", "Table Tennis", "Chess"], 
                                default=st.session_state.form_data.get('selected_list', []))
        
        if st.button("Configure Match Rules ➡️"):
            if sports:
                st.session_state.form_data['selected_list'] = sports
                st.session_state.game_queue = sports
                st.session_state.q_idx = 0
                st.session_state.step = 3; st.rerun()
            else: st.error("Select at least one game.")

    elif st.session_state.step == 3:
        game = st.session_state.game_queue[st.session_state.q_idx]
        st.subheader(f"Configuring: {game}")
        
        # Restore previously saved rules for this game
        rules = st.session_state.form_data['game_rules'].get(game, {})
        
        if game == "Cricket":
            ball = st.radio("Ball", ["Tennis", "Leather"], horizontal=True)
            fmt = st.multiselect("Formats", ["Proper Ground", "Box Cricket"], default=rules.get('fmt', []))
            st.session_state.form_data['game_rules'][game] = {'ball': ball, 'fmt': fmt}

        elif game == "Badminton":
            b_fmts = st.multiselect("Category", ["Singles", "Doubles"], default=rules.get('cat', []))
            b_data = {'cat': b_fmts}
            if "Singles" in b_fmts:
                st.markdown("#### 👤 Singles")
                col1, col2 = st.columns(2)
                b_data['s_pts'] = col1.selectbox("Points", ["11", "21"], key="s1")
                b_data['s_set'] = col2.selectbox("Sets", ["B3", "B5"], key="s2")
            if "Doubles" in b_fmts:
                st.markdown("#### 👥 Doubles")
                col1, col2 = st.columns(2)
                b_data['d_pts'] = col1.selectbox("Points", ["15", "21"], key="d1")
                b_data['d_set'] = col2.selectbox("Match Length", ["B3", "B5"], key="d2") # FIXED
            st.session_state.form_data['game_rules'][game] = b_data

        elif game == "Table Tennis":
            st.markdown("#### 🏓 TT Config")
            tt_cat = st.multiselect("Type", ["Singles", "Doubles"], default=rules.get('cat', []))
            tt_len = st.radio("Match Length", ["B3 (11 Pts)", "B5 (11 Pts)"], horizontal=True)
            st.session_state.form_data['game_rules'][game] = {'cat': tt_cat, 'len': tt_len}

        col1, col2 = st.columns(2)
        if col1.button("⬅️ Back"):
            if st.session_state.q_idx > 0: st.session_state.q_idx -= 1
            else: st.session_state.step = 2
            st.rerun()
            
        is_last = st.session_state.q_idx >= len(st.session_state.game_queue) - 1
        if col2.button("Finalize ✅" if is_last else "Next Event ➡️"):
            if is_last:
                save_or_update(st.session_state.form_data)
                st.session_state.step = 100
            else: st.session_state.q_idx += 1
            st.rerun()

# ==========================================
# 5. FINAL TICKET
# ==========================================
else:
    st.balloons()
    st.markdown('<div class="ticket-box">', unsafe_allow_html=True)
    st.success("Registration Locked & Secured.")
    st.write(f"**Player:** {st.session_state.form_data['name']}")
    st.write(f"**Email:** {st.session_state.form_data['email']}")
    st.write(f"**Games:** {', '.join(st.session_state.form_data['selected_list'])}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Edit My Registration"):
        st.session_state.step = 1; st.rerun()
    if st.button("Logout 🚪"):
        st.session_state.clear(); st.rerun()

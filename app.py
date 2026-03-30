import streamlit as st
import pandas as pd
import plotly.express as px
import os, json, ast, time, hashlib
import qrcode
from io import BytesIO
from datetime import datetime

# ==========================================
# 1. ENTERPRISE CONFIGURATION & UI THEME
# ==========================================
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")
DB_FILE = 'pipecare_sports_master.csv'

st.markdown("""
    <style>
    .stApp { background-color: #E6F0FA; color: #0F172A; }
    h1, h2, h3 { color: #1E3A8A !important; font-weight: 800 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; background-color: #2563EB; color: white; border: none; padding: 0.6rem; transition: all 0.2s ease; }
    .stButton>button:hover { background-color: #1D4ED8; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); transform: translateY(-1px); }
    .clean-card { background: #FFFFFF; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); border-top: 4px solid #2563EB; margin-bottom: 15px; }
    .step-header { color: #1E3A8A; font-weight: 800; font-size: 2rem; border-bottom: 2px solid #BFDBFE; padding-bottom: 10px; margin-bottom: 25px; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; font-weight: bold; font-size: 1.1rem;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA ENGINE (Hashing, Migration, & Safe Save)
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def hash_pin(pin):
    return hashlib.sha256(str(pin).encode()).hexdigest()

def safe_parse(x):
    if pd.isna(x): return {}
    try:
        if isinstance(x, str):
            try: return json.loads(x)
            except: return ast.literal_eval(x)
        return x
    except: return {}

def save_or_update(data):
    df = load_data()
    save_dict = data.copy()

    # Hash PIN and serialize JSON for CSV safety
    save_dict['pin'] = hash_pin(save_dict['pin'])
    save_dict['game_rules'] = json.dumps(save_dict.get('game_rules', {}))
    save_dict['selected_list'] = json.dumps(save_dict.get('selected_list', []))

    # Overwrite based on Email (Integrity Lock)
    if not df.empty and 'email' in df.columns:
        df = df[df['email'] != save_dict['email']]

    new_df = pd.concat([df, pd.DataFrame([save_dict])], ignore_index=True)

    # Safe save (Fixes race conditions during high traffic)
    for _ in range(3):
        try:
            new_df.to_csv(DB_FILE, index=False)
            break
        except:
            time.sleep(0.5)

    st.cache_data.clear()

def generate_qr(email, mobile):
    safe_id = hash_pin(email)[:8]
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(f"PC26|{mobile}|{safe_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==========================================
# 3. STATE INITIALIZATION
# ==========================================
defaults = {"step": 0, "verified": False, "form": {"game_rules": {}}, "q_idx": 0}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ==========================================
# 4. SECURE AUTHENTICATION GATE (Legacy Compatible)
# ==========================================
if not st.session_state.verified:
    st.title("🏆 PIPECARE Noida Sports Portal")
    
    st.markdown('<div class="clean-card">', unsafe_allow_html=True)
    st.write("### Identity Verification")
    st.info("💡 **First Time?** Create a 4-digit PIN. | **Returning?** Use your PIN to edit.")
    
    col1, col2 = st.columns(2)
    email_in = col1.text_input("Official Email (@pipecaregroup.com)").lower().strip()
    pin_in = col2.text_input("Your 4-Digit PIN", type="password", placeholder="e.g. 1234")
    
    if st.button("Login / Register 🔓"):
        if not email_in.endswith("@pipecaregroup.com"):
            st.error("Access Denied: Please use a valid @pipecaregroup.com email address.")
        elif len(pin_in) != 4 or not pin_in.isdigit():
            st.error("Security Check: PIN must be exactly 4 numeric digits.")
        else:
            df = load_data()
            if not df.empty and 'email' in df.columns and (df['email'] == email_in).any():
                user_record = df[df['email'] == email_in].iloc[-1]
                
                # HYBRID CHECK: Allows hashed PINs (new) OR plain-text PINs (legacy users)
                stored_pin = str(user_record['pin'])
                if stored_pin == hash_pin(pin_in) or stored_pin == str(pin_in):
                    rec = user_record.to_dict()
                    rec['selected_list'] = safe_parse(rec.get('selected_list', '[]'))
                    rec['game_rules'] = safe_parse(rec.get('game_rules', '{}'))
                    
                    st.session_state.form = rec
                    # Crucial: Keep raw PIN in state so save_or_update can hash it later
                    st.session_state.form['pin'] = pin_in 
                    st.session_state.verified = True
                    st.session_state.step = 100 
                    st.rerun()
                else: 
                    st.error("Incorrect PIN for this email.")
            else:
                # NEW USER
                st.session_state.form = {'email': email_in, 'pin': pin_in, 'game_rules': {}}
                st.session_state.verified = True
                st.session_state.step = 1
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. DYNAMIC REGISTRATION FLOW
# ==========================================
elif st.session_state.step < 100:
    
    progress_val = min(st.session_state.step / 5, 1.0) if st.session_state.step < 10 else 0.8
    st.progress(progress_val)

    # --- STEP 1 ---
    if st.session_state.step == 1:
        st.markdown(f'<div class="step-header">01. Profile: {st.session_state.form["email"]}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        st.session_state.form['name'] = c1.text_input("Full Official Name", value=st.session_state.form.get('name', ''))
        st.session_state.form['mobile'] = c2.text_input("Mobile / WhatsApp Number", value=st.session_state.form.get('mobile', ''))
        st.session_state.form['unit'] = st.radio("Primary Work Unit", ["Noida Office", "Noida Workshop"], index=0 if st.session_state.form.get('unit') != "Noida Workshop" else 1, horizontal=True)
        
        st.write("")
        c_back, c_next = st.columns(2)
        if c_next.button("Next: Participation Role ➡️"):
            if not str(st.session_state.form['mobile']).isdigit() or len(str(st.session_state.form['mobile'])) < 10:
                st.error("Please enter a valid mobile number.")
            elif st.session_state.form['name']:
                st.session_state.step = 2; st.rerun()
            else: st.error("Name is required.")

    # --- STEP 2 ---
    elif st.session_state.step == 2:
        st.markdown('<div class="step-header">02. Participation & Logistics</div>', unsafe_allow_html=True)
        role_opts = ["Athlete (Playing)", "Audience/Support", "Not Participating"]
        curr_role = st.session_state.form.get('role', role_opts[0])
        role = st.selectbox("I am joining as:", role_opts, index=role_opts.index(curr_role) if curr_role in role_opts else 0)
        st.session_state.form['role'] = role

        if role != "Not Participating":
            st.write("### Event Logistics")
            day_opts = ["Friday (Last working day of week)", "Saturday", "Sunday"]
            curr_day = st.session_state.form.get('day', day_opts[1])
            st.session_state.form['day'] = st.selectbox("Preferred Event Day", day_opts, index=day_opts.index(curr_day) if curr_day in day_opts else 1)
            
            dist_opts = ["10 kms", "20 kms", "30 kms"]
            curr_dist = st.session_state.form.get('distance', dist_opts[0])
            st.session_state.form['distance'] = st.selectbox("Willing to travel (from Office/Workshop)", dist_opts, index=dist_opts.index(curr_dist) if curr_dist in dist_opts else 0)

        st.write("")
        c_back, c_next = st.columns(2)
        if c_back.button("⬅️ Back"): st.session_state.step = 1; st.rerun()
        if c_next.button("Next Step ➡️"):
            st.session_state.step = 3 if role == "Athlete (Playing)" else 99 
            st.rerun()

    # --- STEP 3 ---
    elif st.session_state.step == 3:
        st.markdown('<div class="step-header">03. Sports Selection</div>', unsafe_allow_html=True)
        sports_opts = ["Cricket", "Badminton", "Table Tennis", "Chess", "Carrom", "Snooker", "Other"]
        sports = st.multiselect("Select your events:", sports_opts, default=st.session_state.form.get('selected_list', []))
        
        st.write("")
        c_back, c_next = st.columns(2)
        if c_back.button("⬅️ Back"): st.session_state.step = 2; st.rerun()
        if c_next.button("Configure Games ➡️"):
            if sports:
                st.session_state.form['selected_list'] = sports
                st.session_state.form['game_queue'] = sports
                st.session_state.form['game_rules'] = {k: v for k, v in st.session_state.form.get('game_rules', {}).items() if k in sports}
                st.session_state.q_idx = 0
                st.session_state.step = 10; st.rerun()
            else: st.error("Please select at least one sport.")

    # --- STEP 10 (DYNAMIC GAME CONFIG ENGINE) ---
    elif st.session_state.step == 10:
        game = st.session_state.form['game_queue'][st.session_state.q_idx]
        st.markdown(f'<div class="step-header">Configuring: {game}</div>', unsafe_allow_html=True)
        
        rules = st.session_state.form['game_rules'].get(game, {})
        new_rules = {}

        with st.container():
            if game == "Cricket":
                c_fmts = st.multiselect("Select Cricket Formats", ["Proper Ground", "Box Cricket"], default=rules.get('Formats', ["Proper Ground"]))
                new_rules['Formats'] = c_fmts
                new_rules['Ball'] = st.selectbox("Preferred Ball Type", ["Hard Tennis", "Soft Tennis", "Leather"], index=["Hard Tennis", "Soft Tennis", "Leather"].index(rules.get('Ball', 'Hard Tennis')) if rules.get('Ball') in ["Hard Tennis", "Soft Tennis", "Leather"] else 0)
                
                if "Proper Ground" in c_fmts:
                    st.write("🏟️ **Proper Ground Settings**")
                    col1, col2 = st.columns(2)
                    new_rules['Ground_Overs'] = col1.selectbox("Overs per Innings", ["10 Overs", "15 Overs", "20 Overs"], index=1)
                    new_rules['Ground_Team'] = col2.selectbox("Squad Size", ["11 Playing + 4 Subs", "11 Playing + 2 Subs"], index=0)
                    
                if "Box Cricket" in c_fmts:
                    st.write("📦 **Box Cricket Settings**")
                    col1, col2 = st.columns(2)
                    new_rules['Box_Overs'] = col1.selectbox("Box Overs", ["6 Overs", "8 Overs", "10 Overs"], index=1)
                    new_rules['Box_Team'] = col2.selectbox("Team Size", ["6 v 6", "8 v 8"], index=1)

            elif game == "Badminton":
                b_cats = st.multiselect("Entry Categories", ["Men's Singles", "Women's Singles", "Men's Doubles", "Mixed Doubles"], default=rules.get('Categories', ["Men's Singles"]))
                new_rules['Categories'] = b_cats
                
                if any("Singles" in cat for cat in b_cats):
                    c1, c2 = st.columns(2)
                    new_rules['s_pts'] = c1.selectbox("Singles Points per Set", ["11 Pts", "15 Pts", "21 Pts"], index=2, key="bs1")
                    new_rules['s_set'] = c2.selectbox("Singles Match Length", ["Best of 3", "Best of 5"], key="bs2")
                    
                if any("Doubles" in cat for cat in b_cats):
                    c1, c2 = st.columns(2)
                    new_rules['d_pts'] = c1.selectbox("Doubles Points per Set", ["15 Pts", "21 Pts"], index=1, key="bd1")
                    new_rules['d_set'] = c2.selectbox("Doubles Match Length", ["Best of 3", "Best of 5"], key="bd2")

            elif game == "Table Tennis":
                new_rules['Categories'] = st.multiselect("Entry Categories", ["Singles", "Doubles", "Mixed"], default=rules.get('Categories', ["Singles"]))
                new_rules['Format'] = st.radio("Tournament Match Length", ["Best of 3 (11 Pts)", "Best of 5 (11 Pts)"], index=0, horizontal=True)

            elif game == "Chess":
                col1, col2 = st.columns(2)
                new_rules['Style'] = col1.radio("Tournament Style", ["Knockout", "Swiss League"], index=1)
                new_rules['Timer'] = col2.selectbox("Time Control", ["Blitz (5m)", "Rapid (10m)", "Rapid (15m)"], index=1)

            elif game == "Carrom":
                new_rules['Format'] = st.radio("Format", ["Singles", "Doubles"], index=0, horizontal=True)

            elif game == "Snooker":
                col1, col2 = st.columns(2)
                new_rules['Type'] = col1.radio("Game Type", ["8-Ball Pool", "Snooker (15 Reds)"], index=0)
                new_rules['Frames'] = col2.selectbox("Frames", ["Best of 3", "Best of 5"], index=0)

            elif game == "Other":
                new_rules['Desc'] = st.text_input("Please specify the game:", value=rules.get('Desc', ''))

        st.session_state.form['game_rules'][game] = new_rules

        st.write("") 
        c_back, c_next = st.columns(2)
        if c_back.button("⬅️ Previous", key=f"back_{game}"):
            if st.session_state.q_idx > 0: st.session_state.q_idx -= 1
            else: st.session_state.step = 3
            st.rerun()
            
        is_last = st.session_state.q_idx >= len(st.session_state.form['game_queue']) - 1
        if c_next.button("Review & Save ✅" if is_last else "Next Sport ➡️", key=f"next_{game}"):
            if is_last: st.session_state.step = 99
            else: st.session_state.q_idx += 1
            st.rerun()

    # --- STEP 99: PRE-SUBMIT ---
    elif st.session_state.step == 99:
        st.session_state.form['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_or_update(st.session_state.form)
        st.toast("Registration Saved Successfully! ✅")
        st.session_state.step = 100
        st.rerun()

# ==========================================
# 6. DASHBOARD (3-TAB ARCHITECTURE & RENDERED QR)
# ==========================================
elif st.session_state.step == 100:
    st.balloons()
    
    tab1, tab2, tab3 = st.tabs(["🎫 My Digital Ticket", "👥 HR & Logistics", "🎯 Tournament Director"])
    
    # --- TAB 1: TICKET & QR ---
    with tab1:
        col_ticket, col_qr = st.columns([2, 1])
        with col_ticket:
            st.markdown('<div class="clean-card">', unsafe_allow_html=True)
            st.success("✅ Registration Securely Saved!")
            st.write(f"**Name:** {st.session_state.form.get('name')} | **Unit:** {st.session_state.form.get('unit')}")
            st.write(f"**Email:** {st.session_state.form.get('email')} | **Mobile:** {st.session_state.form.get('mobile')}")
            st.write(f"**Role:** {st.session_state.form.get('role')}")
            
            if st.session_state.form.get('role') != "Not Participating":
                st.write(f"**Availability:** {st.session_state.form.get('day')} | **Radius:** {st.session_state.form.get('distance')}")
            
            if st.session_state.form.get('role') == "Athlete (Playing)":
                st.write(f"**Sports:** {', '.join(st.session_state.form.get('selected_list', []))}")
                with st.expander("View My Match Configurations"):
                    st.json(st.session_state.form.get('game_rules', {}))
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_qr:
            st.markdown("### Ground Check-In")
            st.image(generate_qr(st.session_state.form.get('email'), st.session_state.form.get('mobile')), use_container_width=True)
            st.caption("Present this secure code at the arena.")
        
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("🔄 Edit / Update My Registration"):
            st.session_state.step = 1; st.rerun()
        if c2.button("Logout 🚪"):
            st.session_state.clear(); st.rerun()

    # --- TAB 2: HR ANALYTICS ---
    with tab2:
        df = load_data()
        if not df.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Registrations", len(df))
            m2.metric("Active Athletes", len(df[df['role'] == "Athlete (Playing)"]))
            m3.metric("Audience / Support", len(df[df['role'] == "Audience/Support"]))

            active_df = df[df['role'] != "Not Participating"]
            if not active_df.empty:
                st.markdown("---")
                c1, c2 = st.columns(2)
                c1.plotly_chart(px.pie(active_df, names='day', title="Preferred Day to Attend", hole=0.3, color_discrete_sequence=px.colors.sequential.Blues_r), use_container_width=True)
                c2.plotly_chart(px.histogram(active_df, x='distance', title="Travel Willingness Radius", color='unit', barmode='group', color_discrete_sequence=['#1E3A8A', '#3B82F6']), use_container_width=True)

            st.markdown("---")
            all_sports = []
            for s in df['selected_list']:
                parsed = safe_parse(s)
                if isinstance(parsed, list): all_sports.extend(parsed)
            
            if all_sports:
                sc = pd.Series(all_sports).value_counts().reset_index()
                sc.columns = ["Sport", "Registrations"]
                st.plotly_chart(px.bar(sc, x="Sport", y="Registrations", title="Overall Game Popularity", color="Sport", color_discrete_sequence=px.colors.qualitative.Prism), use_container_width=True)

    # --- TAB 3: TOURNAMENT DIRECTOR ANALYTICS ---
    with tab3:
        df = load_data()
        if not df.empty:
            df['rules'] = df['game_rules'].apply(safe_parse)
            
            r1c1, r1c2 = st.columns(2)
            
            # Cricket
            c_formats = [fmt for r in df['rules'] if isinstance(r, dict) and 'Cricket' in r for fmt in r['Cricket'].get('Formats', [])]
            if c_formats: r1c1.plotly_chart(px.pie(names=pd.Series(c_formats).value_counts().index, values=pd.Series(c_formats).value_counts().values, title="🏏 Cricket: Ground vs Box", hole=0.4, color_discrete_sequence=['#10B981', '#F59E0B']), use_container_width=True)

            # Badminton
            b_cats = [cat for r in df['rules'] if isinstance(r, dict) and 'Badminton' in r for cat in r['Badminton'].get('Categories', [])]
            if b_cats: r1c2.plotly_chart(px.bar(x=pd.Series(b_cats).value_counts().index, y=pd.Series(b_cats).value_counts().values, title="🏸 Badminton: Brackets", labels={'x': 'Category', 'y': 'Entries'}, color_discrete_sequence=['#6366F1']), use_container_width=True)

            r2c1, r2c2 = st.columns(2)
            
            # Table Tennis
            tt_cats = [cat for r in df['rules'] if isinstance(r, dict) and 'Table Tennis' in r for cat in r['Table Tennis'].get('Categories', [])]
            if tt_cats: r2c1.plotly_chart(px.pie(names=pd.Series(tt_cats).value_counts().index, values=pd.Series(tt_cats).value_counts().values, title="🏓 Table Tennis: Category Split", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2), use_container_width=True)

            # Chess
            ch_modes = [r.get('Chess', {}).get('Mode') for r in df['rules'] if isinstance(r, dict) and 'Chess' in r]
            if ch_modes: r2c2.plotly_chart(px.pie(names=pd.Series(ch_modes).value_counts().index, values=pd.Series(ch_modes).value_counts().values, title="♟️ Chess: Mode Preference", hole=0.4, color_discrete_sequence=['#8B5CF6', '#EC4899']), use_container_width=True)

            r3c1, r3c2 = st.columns(2)
            
            # Carrom
            ca_fmts = [r.get('Carrom', {}).get('Format') for r in df['rules'] if isinstance(r, dict) and 'Carrom' in r]
            if ca_fmts: r3c1.plotly_chart(px.pie(names=pd.Series(ca_fmts).value_counts().index, values=pd.Series(ca_fmts).value_counts().values, title="🎯 Carrom: Singles vs Doubles", hole=0.4), use_container_width=True)

            # Snooker
            sn_types = [r.get('Snooker', {}).get('Type') for r in df['rules'] if isinstance(r, dict) and 'Snooker' in r]
            if sn_types: r3c2.plotly_chart(px.pie(names=pd.Series(sn_types).value_counts().index, values=pd.Series(sn_types).value_counts().values, title="🎱 Snooker vs 8-Ball Pool", hole=0.4), use_container_width=True)

            # Other
            other_desc = [r.get('Other', {}).get('Desc') for r in df['rules'] if isinstance(r, dict) and 'Other' in r and r.get('Other', {}).get('Desc')]
            if other_desc:
                st.markdown("---")
                st.write("**➕ Other Games Requested by Employees:**")
                for desc in set(other_desc): st.info(f"• {desc}")

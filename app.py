import streamlit as st
import pandas as pd
import os
import json
import qrcode
from io import BytesIO
from datetime import datetime

# ==========================================
# 1. SETTINGS & STYLING
# ==========================================
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide")
DB_FILE = 'pipecare_sports_master.csv'

def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame()

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ==========================================
# 2. LOGIN / RE-ENTRY LOGIC
# ==========================================
if 'auth_user' not in st.session_state:
    st.title("🏆 PIPECARE Noida Sports 2026")
    
    tab1, tab2 = st.tabs(["New Registration", "Existing Player Login"])
    
    with tab1:
        email_new = st.text_input("Corporate Email", key="new_em").lower().strip()
        if st.button("Start Registration ➡️"):
            if email_new.endswith("@pipecaregroup.com"):
                st.session_state.auth_user = email_new
                st.session_state.step = 1
                st.session_state.form_data = {'email': email_new}
                st.rerun()
            else: st.error("Use @pipecaregroup.com only.")

    with tab2:
        st.info("To edit your form, enter your registered email.")
        email_ex = st.text_input("Registered Email", key="ex_em").lower().strip()
        if st.button("Access My Ticket 🔓"):
            df = load_data()
            if not df.empty and (df['email'] == email_ex).any():
                st.session_state.auth_user = email_ex
                st.session_state.form_data = df[df['email'] == email_ex].iloc[-1].to_dict()
                st.session_state.step = 100 # Go to Ticket/QR
                st.rerun()
            else: st.error("Email not found in database.")

# ==========================================
# 3. REGISTRATION FLOW
# ==========================================
elif st.session_state.step == 1:
    st.header(f"Profile: {st.session_state.auth_user}")
    name = st.text_input("Full Name", value=st.session_state.form_data.get('name', ''))
    mobile = st.text_input("Mobile Number", value=st.session_state.form_data.get('mobile', ''))
    sports = st.multiselect("Select Games", ["Cricket", "Badminton", "TT"], default=json.loads(st.session_state.form_data.get('selected_list', '[]')) if isinstance(st.session_state.form_data.get('selected_list'), str) else [])

    if st.button("Generate My Sports Ticket 🎫"):
        if name and mobile:
            st.session_state.form_data.update({
                'name': name, 'mobile': mobile, 
                'selected_list': json.dumps(sports),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            # Save to CSV
            df = load_data()
            if not df.empty: df = df[df['email'] != st.session_state.auth_user]
            pd.concat([df, pd.DataFrame([st.session_state.form_data])]).to_csv(DB_FILE, index=False)
            
            st.session_state.step = 100
            st.rerun()

# ==========================================
# 4. THE QR TICKET (DASHBOARD)
# ==========================================
elif st.session_state.step == 100:
    st.success("✅ Registration Active")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Your Entry QR")
        # QR contains the Email + Mobile for verification
        qr_content = f"PLAYER:{st.session_state.form_data['email']}|TEL:{st.session_state.form_data['mobile']}"
        qr_img = generate_qr(qr_content)
        st.image(qr_img, caption="Show this at the ground check-in")
        
    with col2:
        st.markdown(f"## {st.session_state.form_data['name']}")
        st.write(f"**Email:** {st.session_state.form_data['email']}")
        st.write(f"**Status:** Confirmed for Noida 2026")
        
        if st.button("🔄 Edit Registration"):
            st.session_state.step = 1
            st.rerun()
            
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

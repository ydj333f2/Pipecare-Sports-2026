import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random

# --- 1. CLEAN CORPORATE CONFIG ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

# Professional Blue & White Theme (Better for Eyes)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .receipt-box { padding: 20px; border-radius: 10px; background: #161b22; border: 1px solid #30363d; margin-top: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #238636; color: white; font-weight: 600; height: 3em; border: none; }
    .stButton>button:hover { background-color: #2ea043; border: none; }
    label { font-size: 1.1rem !important; font-weight: 600 !important; color: #c9d1d9 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA UTILS ---
DB_FILE = 'data.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Timestamp", "Name", "Unit", "Type", "Travel", "Schedule", "Details"])

if 'verified' not in st.session_state: st.session_state.verified = False
if 'otp' not in st.session_state: st.session_state.otp = None
if 'submitted_data' not in st.session_state: st.session_state.submitted_data = None

# --- 3. SIMPLE VERIFICATION GATE ---
if not st.session_state.verified:
    st.title("🏆 PIPECARE Noida Sports Portal")
    st.write("Please verify your company email to continue.")
    
    email_in = st.text_input("Company Email ID", placeholder="example@pipecaregroup.com")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if st.button("Send OTP"):
            if "@pipecaregroup.com" in email_in.lower():
                otp = str(random.randint(1000, 9999))
                st.session_state.otp = otp
                try:
                    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                    server.login(GMAIL_USER, GMAIL_PASS)
                    server.sendmail(GMAIL_USER, email_in, f"Subject: Your Sports Portal Code\n\nCode: {otp}")
                    server.quit()
                    st.success("Code sent to your inbox.")
                except Exception as e: st.error("Email failed. Check your Secrets.")
            else: st.error("Please use a @pipecaregroup.com email.")

    with col_v2:
        code_in = st.text_input("Enter 4-Digit Code", placeholder="0000")
        if st.button("Verify & Login"):
            if code_in == st.session_state.otp and st.session_state.otp is not None:
                st.session_state.verified = True
                st.rerun()
            else: st.error("Invalid code.")

# --- 4. THE REGISTRATION HUB ---
else:
    st.title("🏆 Registration & Consensus")
    st.divider()
    
    if st.session_state.submitted_data is None:
        with st.form("main_form"):
            st.subheader("1. Employee Details")
            c1, c2 = st.columns(2)
            name = c1.text_input("Full Name*")
            unit = c1.radio("Your Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
            p_role = c2.selectbox("Will you participate?", 
                                 ["Athlete (Player)", "Audience / Support Staff", "Will not attend"], 
                                 index=None)

            details, travel, schedule = "", "N/A", "N/A"

            if p_role in ["Athlete (Player)", "Audience / Support Staff"]:
                st.subheader("2. Travel & Timing")
                t_col, s_col = st.columns(2)
                travel = t_col.select_slider("Travel willingness", options=["10 km", "20 km", "30 km"])
                schedule = s_col.selectbox("Preferred Day", ["Friday", "Saturday", "Sunday", "Holidays"])

            if p_role == "Athlete (Player)":
                st.subheader("3. Sports Preferences")
                sport = st.selectbox("Which Sport?", ["Cricket", "Badminton", "Both", "Other Games"])
                
                if "Cricket" in sport:
                    st.info("🏏 Cricket Configuration")
                    c_fmt = st.selectbox("Ground Format", ["Proper Ground", "Box Cricket"])
                    c_ball = st.radio("Ball", ["Tennis", "Leather"], horizontal=True)
                    if c_fmt == "Box Cricket":
                        details += f"Cricket: {c_fmt}, {c_ball}, {st.selectbox('Overs', [10, 15, 20])} Overs, {st.selectbox('Team Size', [6, 8, 10])} Players. "
                    else: details += f"Cricket: {c_fmt}, {c_ball}. "

                if "Badminton" in sport:
                    st.info("🏸 Badminton Configuration")
                    b_mode = st.multiselect("Format", ["Singles", "Doubles"])
                    details += f"Badminton: {b_mode}. "
                
                if sport == "Other Games":
                    details += f"Games: {st.multiselect('Interests', ['TT', 'Snooker', 'Tug of War', '7 Stones', 'Chess', 'Carrom'])} "

                details += f" | Custom: {st.text_area('Additional Suggestions')}"

            if st.form_submit_button("Submit Registration"):
                if name and p_role:
                    entry = {"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Name": name, "Unit": unit, "Type": p_role, "Travel": travel, "Schedule": schedule, "Details": details}
                    pd.concat([load_data(), pd.DataFrame([entry])], ignore_index=True).to_csv(DB_FILE, index=False)
                    st.session_state.submitted_data = entry
                    st.balloons()
                    st.rerun()
                else: st.error("Name and Participation are required.")

    else:
        # POST-SUBMISSION VIEW
        st.success(f"Thank you, {st.session_state.submitted_data['Name']}! Your response is saved.")
        res_col1, res_col2 = st.columns([1, 1.2], gap="large")
        
        with res_col1:
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.subheader("Your Selection")
            st.write(f"**Unit:** {st.session_state.submitted_data['Unit']}")
            st.write(f"**Role:** {st.session_state.submitted_data['Type']}")
            st.write(f"**Preferred Day:** {st.session_state.submitted_data['Schedule']}")
            st.info(f"**Details:** {st.session_state.submitted_data['Details']}")
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("Edit Response"):
                st.session_state.submitted_data = None
                st.rerun()

        with res_col2:
            st.subheader("Live Poll Results")
            df = load_data()
            if not df.empty:
                t1, t2 = st.tabs(["Attendance", "Timing"])
                t1.plotly_chart(px.pie(df, names='Type', hole=0.4, template="plotly_dark"), use_container_width=True)
                t2.plotly_chart(px.histogram(df[df['Type']!='Will not attend'], x='Schedule', color='Unit', barmode='group', template="plotly_dark"), use_container_width=True)
            st.download_button("Download Report", df.to_csv(index=False).encode('utf-8'), "Sports_Data.csv", "text/csv")

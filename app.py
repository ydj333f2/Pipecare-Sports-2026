import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random

# --- 1. PRO-LEVEL CONFIG & STYLING ---
st.set_page_config(page_title="PIPECARE Sports 2026", layout="wide", page_icon="🏆")

# Stadium Professional Theme
st.markdown("""
    <style>
    .stApp { background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url('https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?q=80&w=2000'); background-size: cover; color: #e0e0e0; }
    .receipt-box { padding: 25px; border-radius: 15px; background: rgba(0,120,212,0.15); border: 2px solid #0078d4; margin-top: 10px; }
    .stButton>button { width: 100%; border-radius: 12px; background: linear-gradient(45deg, #0078d4, #00bcf2); color: white; font-weight: 700; height: 3.5em; border: none; }
    .stButton>button:hover { transform: scale(1.02); transition: 0.3s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INFRASTRUCTURE ---
DB_FILE = 'data.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "")

def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Timestamp", "Name", "Unit", "Type", "Travel", "Schedule", "Details"])

if 'verified' not in st.session_state: st.session_state.verified = False
if 'otp' not in st.session_state: st.session_state.otp = None
if 'submitted_data' not in st.session_state: st.session_state.submitted_data = None

# --- 3. THE SECURITY GATE ---
if not st.session_state.verified:
    st.title("🛡️ PIPECARE NOIDA ARENA ACCESS")
    st.info("Identity verification required for the Sports Consensus Portal.")
    email_in = st.text_input("Enter Company Email (@pipecaregroup.com)")
    
    col_v1, col_v2 = st.columns(2)
    if col_v1.button("📩 DISPATCH CODE"):
        if "@pipecaregroup.com" in email_in.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp = otp
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email_in, f"Subject: Sports Hub OTP\n\nYour Access Code: {otp}")
                server.quit()
                st.success("Verification code dispatched to Outlook.")
            except Exception as e: st.error(f"Error: {e}")
        else: st.error("Please use your @pipecaregroup.com email.")

    code_in = st.text_input("Enter 4-Digit Code", placeholder="XXXX")
    if col_v2.button("🔓 UNLOCK HUB"):
        if code_in == st.session_state.otp:
            st.session_state.verified = True
            st.rerun()
        else: st.error("Invalid Code.")

# --- 4. THE SPORTS HUB ARENA ---
else:
    st.title("🏆 NOIDA SPORTS HUB 2026")
    st.markdown("---")
    
    # PHASE 1: THE REGISTRATION FORM
    if st.session_state.submitted_data is None:
        with st.form("master_consensus_vFinal"):
            st.subheader("👤 1. Identity & Role")
            c_id1, c_id2 = st.columns(2)
            name = c_id1.text_input("Full Name*")
            unit = c_id1.radio("Home Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
            p_role = c_id2.selectbox("Participation Type", 
                                    ["Athlete (Competing Player)", "Supporter (Audience/Organizing)", "Will not come at all"], 
                                    index=None, placeholder="Choose your role...")

            # VARIABLES FOR LOGIC
            details = ""
            travel = "N/A"
            schedule = "N/A"

            # PHASE 2: LOGISTICS (For all attendees)
            if p_role in ["Athlete (Competing Player)", "Supporter (Audience/Organizing)"]:
                st.write("---")
                st.subheader("🗺️ 2. Logistics & Timing")
                c_log1, c_log2 = st.columns(2)
                travel = c_log1.select_slider("Travel Radius from Office", options=["10 km", "20 km", "30 km"])
                schedule = c_log2.selectbox("Preferred Schedule Window", 
                                           ["Friday (Last Working Day)", "Saturday", "Sunday", "Public Holidays / Festivals"])

            # PHASE 3: GAME SPECIFICS (For Athletes only)
            if p_role == "Athlete (Competing Player)":
                st.write("---")
                st.subheader("🎯 3. Arena Selection & Rules")
                sport_main = st.selectbox("Choose Primary Interest", ["Cricket", "Badminton", "Dual-Sport (Both)", "Multi-Game Zone"])
                
                # Cricket Deep Logic
                if "Cricket" in sport_main or sport_main == "Dual-Sport (Both)":
                    st.info("🏏 CRICKET TECHNICAL SPECS")
                    c_fmt = st.selectbox("Ground Format", ["Big Round (Proper Ground)", "Box Cricket Arena"])
                    c_ball = st.radio("Ball Specification", ["Tennis Ball", "Leather Ball"], horizontal=True)
                    if c_fmt == "Box Cricket Arena":
                        c_ovr = st.selectbox("Match Duration", [10, 15, 20])
                        c_sqd = st.selectbox("Squad Size", [6, 8, 10])
                        details += f"CRICKET: {c_fmt}, {c_ball}, {c_ovr} Overs, {c_sqd} Players. "
                    else: details += f"CRICKET: {c_fmt}, {c_ball}. "
                    st.caption("👟 Required: Proper cricket shoes and sports uniform.")

                # Badminton Deep Logic
                if "Badminton" in sport_main or sport_main == "Dual-Sport (Both)":
                    st.info("🏸 BADMINTON TECHNICAL SPECS")
                    b_fmt = st.multiselect("Format Interest", ["Singles", "Doubles"])
                    if "Singles" in b_fmt:
                        b_s = st.selectbox("Singles Point System", ["11 (Best of 3)", "15 (Best of 3)", "21 (1 Set)", "21 (Best of 3)"])
                        details += f"BADMINTON SINGLES: {b_s}. "
                    if "Doubles" in b_fmt:
                        b_d = st.selectbox("Doubles Point System", ["15 (Best of 3)", "21 (Best of 3)"])
                        details += f"BADMINTON DOUBLES: {b_d}. "
                    st.warning("🏸 Required: Non-marking shoes, personal racquet, and proper costume.")

                # Multi-Game Zone
                if sport_main == "Multi-Game Zone":
                    st.info("🎯 SELECT YOUR GAMES")
                    multi = st.multiselect("Select Interests", ["Table Tennis", "Snooker", "Tug of War", "7 Stones", "Chess", "Carroms"])
                    details += f"ZONE GAMES: {multi}. "

                custom = st.text_area("Blank Space: Suggest anything else or specific preferences")
                details += f" | NOTES: {custom}"
                st.caption("ℹ️ Note: Final game selection depends on aggregate interest and HR approval.")

            if st.form_submit_button("🔥 LOCK IN RESPONSE"):
                if name and p_role:
                    entry = {
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Name": name, "Unit": unit, "Type": p_role,
                        "Travel": travel, "Schedule": schedule, "Details": details
                    }
                    pd.concat([load_data(), pd.DataFrame([entry])], ignore_index=True).to_csv(DB_FILE, index=False)
                    st.session_state.submitted_data = entry
                    st.balloons()
                    st.rerun()
                else: st.error("Missing required fields: Name and Participation Role.")

    # PHASE 4: POST-SUBMISSION RECEIPT & LIVE POLLS
    else:
        st.success(f"Response Secured! Welcome to the Roster, {st.session_state.submitted_data['Name']}!")
        
        col_res1, col_res2 = st.columns([1, 1.2], gap="large")
        
        with col_res1:
            st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
            st.subheader("📋 Your Selection Receipt")
            st.write(f"**Unit:** {st.session_state.submitted_data['Unit']}")
            st.write(f"**Participation:** {st.session_state.submitted_data['Type']}")
            st.write(f"**Travel Radius:** {st.session_state.submitted_data['Travel']}")
            st.write(f"**Preferred Day:** {st.session_state.submitted_data['Schedule']}")
            st.info(f"**Game Specs:**\n{st.session_state.submitted_data['Details']}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button("🔄 Change My Selection"):
                st.session_state.submitted_data = None
                st.rerun()

        with col_res2:
            st.subheader("📊 Live Tournament Consensus")
            df_final = load_data()
            if not df_final.empty:
                tab1, tab2 = st.tabs(["Arena Mix", "Timing Polls"])
                with tab1:
                    st.plotly_chart(px.pie(df_final, names='Type', hole=0.5, template="plotly_dark", title="Global Attendance Mix"), use_container_width=True)
                with tab2:
                    st.plotly_chart(px.histogram(df_final[df_final['Type'] != 'Will not come at all'], x='Schedule', color='Unit', barmode='group', template="plotly_dark"), use_container_width=True)
            
            st.divider()
            st.download_button("📥 Download Master Roster (Admin)", df_final.to_csv(index=False).encode('utf-8'), "Pipecare_Master_Roster.csv", "text/csv")

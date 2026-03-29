import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import smtplib
import random

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="PIPECARE Sports Portal", layout="wide")

# Custom CSS for the "Sports Hub" feel
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { background-color: #0078d4; color: white; border-radius: 8px; }
    .stTextInput>div>div>input { background-color: #262730; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA & SECRETS ---
DB_FILE = 'data.csv'
GMAIL_USER = st.secrets.get("GMAIL_USER", "your-email@gmail.com")
GMAIL_PASS = st.secrets.get("GMAIL_PASS", "your-app-password")

if 'verified' not in st.session_state: st.session_state.verified = False
if 'otp' not in st.session_state: st.session_state.otp = None

def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame()

# --- 3. APP HEADER ---
st.title("🏆 PIPECARE Noida Sports Event 2026")
st.markdown("### Office & Workshop Collaboration Portal")
st.divider()

# --- 4. STEP 1: OTP VERIFICATION ---
if not st.session_state.verified:
    st.subheader("🔒 Employee Verification")
    email_col, btn_col = st.columns([3, 1])
    email_in = email_col.text_input("Enter Company Email ID (@pipecaregroup.com)")
    
    if btn_col.button("Send OTP"):
        if "@pipecaregroup.com" in email_in.lower():
            otp = str(random.randint(1000, 9999))
            st.session_state.otp = otp
            # Send Email Logic
            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.login(GMAIL_USER, GMAIL_PASS)
                server.sendmail(GMAIL_USER, email_in, f"Subject: PIPECARE Sports OTP\n\nYour code is: {otp}")
                server.quit()
                st.success("OTP sent to your Outlook!")
            except Exception as e: st.error(f"Error: {e}")
        else: st.error("Please use your official company email.")

    code_in = st.text_input("Enter 4-Digit Code")
    if st.button("Verify & Start"):
        if code_in == st.session_state.otp:
            st.session_state.verified = True
            st.rerun()

# --- 5. STEP 2: FULL REGISTRATION FORM ---
else:
    col_f, col_s = st.columns([1.5, 1], gap="large")
    
    with col_f:
        with st.form("master_form", clear_on_submit=True):
            st.subheader("📝 Personal & Consensus Details")
            name = st.text_input("Full Name*")
            loc = st.radio("Unit", ["Noida Office", "Noida Workshop"], horizontal=True)
            
            # --- CONSENSUS LOGIC ---
            interest = st.radio("Participation Level", 
                                ["Athlete (Player)", "Audience / Support Staff", "Will not come at all"], 
                                index=None)

            details = ""
            
            if interest == "Athlete (Player)":
                # TRAVEL LOGIC
                st.write("---")
                travel = st.select_slider("How far are you willing to travel for the game?", 
                                         options=["10 km", "20 km", "30 km"])
                
                # TIMING LOGIC
                timing = st.selectbox("Preferred Schedule", ["Weekends (Sat/Sun)", "Public Holidays / Festivals"])
                
                # SPORT SELECTION
                sport_main = st.selectbox("Select Sport", ["Cricket", "Badminton", "Both", "Other Games"])
                
                # --- CRICKET LOGIC ---
                if sport_main in ["Cricket", "Both"]:
                    st.info("🏏 Cricket Configuration")
                    c_type = st.selectbox("Ground Format", ["Big Round (Proper Ground)", "Box Cricket"])
                    c_ball = st.radio("Ball Preference", ["Tennis Ball", "Leather Ball"], horizontal=True)
                    
                    if c_type == "Box Cricket":
                        c_overs = st.selectbox("Overs", [10, 15, 20])
                        c_team = st.selectbox("Team Size", [6, 8, 10])
                        details += f"Cricket: {c_type}, {c_ball}, {c_overs} Overs, {c_team} Players. "
                    else:
                        details += f"Cricket: {c_type}, {c_ball}. "
                    st.caption("👟 Required: Proper cricket shoes and sports attire.")

                # --- BADMINTON LOGIC ---
                if sport_main in ["Badminton", "Both"]:
                    st.info("🏸 Badminton Configuration")
                    b_mode = st.multiselect("Format", ["Singles", "Doubles"])
                    if "Singles" in b_mode:
                        b_s = st.selectbox("Singles Scoring", ["11 pts (Best of 3)", "15 pts (Best of 3)", "21 pts (1 set)", "21 pts (Best of 3)"])
                        details += f"Badminton Singles: {b_s}. "
                    if "Doubles" in b_mode:
                        b_d = st.selectbox("Doubles Scoring", ["15 pts (Best of 3)", "21 pts (Best of 3)"])
                        details += f"Badminton Doubles: {b_d}. "
                    st.warning("🏸 Required: Court shoes, racquets, and proper costume.")

                # --- OTHER GAMES ---
                if sport_main == "Other Games":
                    others = st.multiselect("Select Games", ["Table Tennis", "Snooker", "Tug of War", "7 Stones", "Chess", "Carroms"])
                    details += f"Others: {others}. "

                custom = st.text_area("Custom Suggestion / Blank Space Interest", placeholder="Anything else you'd like to suggest?")
                st.caption("ℹ️ Note: These games depend on overall interest and HR approval.")

            elif interest == "Audience / Support Staff":
                timing = st.selectbox("Availability", ["Weekends", "Public Holidays / Festivals"])
                details = "Audience/Support Role"
            else:
                timing = "N/A"
                details = "Absent"

            if st.form_submit_button("Submit Final Response"):
                if name and interest:
                    new_data = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Name": name, "Location": loc, "Interest": interest,
                        "Travel": travel if interest=="Athlete (Player)" else "N/A",
                        "Timing": timing, "Details": details + custom if interest=="Athlete (Player)" else details
                    }])
                    new_data.to_csv(DB_FILE, mode='a', index=False, header=not os.path.exists(DB_FILE))
                    st.balloons()
                    st.success("Registration successfully recorded!")

    # --- 6. STATS DASHBOARD ---
    with col_s:
        st.subheader("📊 Live Consensus Trends")
        df = load_data()
        if not df.empty:
            fig1 = px.pie(df, names='Interest', hole=0.4, title="Attendance Mix")
            st.plotly_chart(fig1, use_container_width=True)
            
            fig2 = px.histogram(df[df['Interest']!='Will not come at all'], x='Timing', color='Location', barmode='group', title="Schedule Preference")
            st.plotly_chart(fig2, use_container_width=True)
            
            # Admin Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Excel Report for HR", csv, "Pipecare_Consensus_Master.csv", "text/csv")

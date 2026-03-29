import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="PIPECARE Sports 2026", page_icon="🏆")

# --- DATA STORAGE ---
DB_FILE = 'data.csv'
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame()

# --- UI FRONT END ---
st.title("🏆 PIPECARE Noida Sports Event")
st.markdown("### Office & Workshop Registration Portal")

# --- THE FORM ---
with st.form("main_form", clear_on_submit=True):
    st.subheader("1. Personal Details")
    name = st.text_input("Full Name*")
    email = st.text_input("Company Email ID*")
    whatsapp = st.text_input("WhatsApp Number*")
    location = st.radio("Primary Work Location", ["Noida Office", "Noida Workshop"])
    
    st.divider()
    
    st.subheader("2. Choose Your Sport")
    sport = st.selectbox("What would you like to play?", ["Cricket", "Badminton", "Both", "Other Games"])
    
    # --- DYNAMIC LOGIC ---
    if sport in ["Cricket", "Both"]:
        st.info("🏏 Cricket Configuration")
        c_format = st.selectbox("Cricket Format", ["Proper Cricket Ground", "Box Cricket", "Both/Any"])
        ball = st.radio("Ball Preference", ["Tennis Ball", "Leather Ball"])
        overs = st.select_slider("Match Duration (Overs)", options=[10, 20])
        
        if c_format == "Box Cricket":
            st.selectbox("Box Team Size", [6, 8, 11])
            st.selectbox("Box Overs", [6, 8, 10])

    if sport in ["Badminton", "Both"]:
        st.info("🏸 Badminton Configuration")
        b_cat = st.radio("Category", ["Singles", "Doubles", "Both"])
        
        if b_cat == "Singles":
            st.selectbox("Singles Scoring Format", [
                "11 points (Best of 3 sets)", 
                "15 points (Best of 3 sets)", 
                "21 points (1 set knockout)", 
                "21 points (Best of 3 sets)"
            ])
        else:
            st.selectbox("Doubles Scoring Format", ["15 points (Best of 3)", "21 points (Best of 3)"])
        
        st.warning("⚠️ Note: Proper court shoes and racquets must be brought by the participant.")

    if sport == "Other Games":
        st.info("🕹️ Other Games (Noida Game Zone)")
        st.multiselect("Select Interests", ["Table Tennis", "Snooker/Billiards", "Chess", "Carroms", "Tug of War", "7 Stones"])
        st.text_input("Any other game suggestion?")

    st.divider()
    st.subheader("3. Logistics")
    day = st.selectbox("Preferred Day", ["Saturday", "Sunday", "Any"])
    travel = st.select_slider("How far can you travel from office?", options=["Within 10 kms", "Within 20 kms", "Within 30 kms"])
    suggest = st.text_area("Final Suggestions for HR/Admin")

    submit = st.form_submit_button("Submit Registration")

# --- SAVE DATA ---
if submit:
    if name and email and whatsapp:
        entry = {
            "Name": name, "Email": email, "WhatsApp": whatsapp, "Location": location,
            "Sport": sport, "Day": day, "Travel": travel, "Timestamp": datetime.now()
        }
        df = load_data()
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("✅ Registered Successfully!")
    else:
        st.error("Please fill Name, Email, and WhatsApp.")

# --- LIVE DASHBOARD (THE CHARTS) ---
st.divider()
st.subheader("📊 Live Event Trends")
df_stats = load_data()

if not df_stats.empty:
    fig1 = px.pie(df_stats, names='Sport', title="Sport Popularity Breakdown")
    st.plotly_chart(fig1)
    
    fig2 = px.bar(df_stats, x='Location', color='Sport', title="Office vs Workshop Participation")
    st.plotly_chart(fig2)
else:
    st.write("Results will appear here once the first person registers.")

# --- WHATSAPP SHARE ---
st.write("---")
whatsapp_msg = "https://wa.me/?text=Join%20the%20PIPECARE%20Sports%20Event%202026%20here!"
st.markdown(f"[📲 Share via WhatsApp]({whatsapp_msg})")

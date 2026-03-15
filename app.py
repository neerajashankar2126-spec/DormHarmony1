import streamlit as st
import pandas as pd
from st_gsheets_connection import GSheetsConnection

# --- PAGE CONFIG ---
st.set_page_config(page_title="DormHarmony AI", page_icon="🏠", layout="centered")

# --- CSS FOR 90s RETRO VIBE ---
st.markdown("""
    <style>
    .main { background-color: #f0ebe3; }
    h1 { color: #2e4053; font-family: 'Courier New', Courier, monospace; text-shadow: 2px 2px #d5d8dc; }
    .stButton>button { background-color: #2e4053; color: white; border-radius: 5px; width: 100%; }
    .stProgress > div > div > div > div { background-color: #2e4053; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch Live Data from Google Sheets
try:
    df = conn.read(spreadsheet=st.secrets["gsheets_url"], ttl=0)
    candidates = df.to_dict(orient='records')
except Exception as e:
    st.error("⚠️ Connection Error: Check your Google Sheet URL in Streamlit Secrets.")
    candidates = []

# --- AI LOGIC (Manhattan Distance Heuristic) ---
def get_match_score(user_list, person_dict):
    # Hard Constraint: Smoke (Last item in list)
    if user_list[-1] != person_dict['Smoke']:
        return 0
    
    # Soft Constraints: Mapping headers to indices
    # We skip 'Name' and 'Smoke' for the math
    keys = ["Sleep", "Cleanliness", "Noise", "Social", "AC", "Share", "Lights"]
    total_diff = 0
    for i, key in enumerate(keys):
        total_diff += abs(user_list[i] - person_dict[key])
    
    # Max difference (7 traits * 4 max diff per trait)
    max_diff = len(keys) * 4
    score = (1 - (total_diff / max_diff)) * 100
    return round(score, 1)

# --- UI HEADER ---
st.title("📟 DormHarmony AI")
st.caption("SRM KTR | Solo AI Project by Neeraja | March 2026")
st.write("---")

# --- MATCHING SECTION ---
st.subheader("🔍 Find Your Roommate Match")
u_name = st.text_input("Enter your name to start matching")

col1, col2 = st.columns(2)
with col1:
    s1 = st.slider("Sleep (1: Early - 5: Late)", 1, 5, 3)
    s2 = st.slider("Cleanliness (1: Messy - 5: Neat)", 1, 5, 3)
    s3 = st.slider("Noise (1: Quiet - 5: Loud)", 1, 5, 3)
    s4 = st.slider("Social (1: Introvert - 5: Extrovert)", 1, 5, 3)
with col2:
    s5 = st.slider("AC (1: No AC - 5: Always On)", 1, 5, 3)
    s6 = st.slider("Share (1: No Guests - 5: Frequent Guests)", 1, 5, 3)
    s7 = st.slider("Lights (1: Dark - 5: Bright)", 1, 5, 3)
    s8 = st.radio("Do you smoke?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No", horizontal=True)

user_habits = [s1, s2, s3, s4, s5, s6, s7, s8]

if st.button("🚀 Run AI Matcher"):
    if not u_name:
        st.warning("Please enter your name!")
    elif not candidates:
        st.info("Database is empty. Add your profile below!")
    else:
        with st.spinner('Calculating compatibility...'):
            results = []
            for person in candidates:
                if person['Name'].lower() == u_name.lower():
                    continue
                score = get_match_score(user_habits, person)
                results.append({"name": person['Name'], "score": score})
            
            results = sorted(results, key=lambda x: x['score'], reverse=True)
            
            if not results:
                st.info("No other students in the pool yet.")
            else:
                st.success(f"Results for {u_name}:")
                for res in results:
                    if res['score'] > 0:
                        with st.container():
                            st.write(f"**{res['name']}**")
                            st.progress(int(res['score']))
                            st.caption(f"Score: {res['score']}%")
                    else:
                        st.error(f"{res['name']} - 0% Match (Smoke Preference Mismatch)")

st.write("---")

# --- REGISTRATION SECTION ---
st.subheader("📝 Join the SRM Database")
with st.expander("Register your profile for others to find you"):
    with st.form("reg_form", clear_on_submit=True):
        reg_name = st.text_input("Full Name")
        r1 = st.select_slider("Sleep Schedule", options=[1, 2, 3, 4, 5], value=3)
        r2 = st.select_slider("Cleanliness Level", options=[1, 2, 3, 4, 5], value=3)
        r3 = st.select_slider("Noise Tolerance", options=[1, 2, 3, 4, 5], value=3)
        r4 = st.select_slider("Social Energy", options=[1, 2, 3, 4, 5], value=3)
        r5 = st.select_slider("AC Usage", options=[1, 2, 3, 4, 5], value=3)
        r6 = st.select_slider("Sharing/Guest Policy", options=[1, 2, 3, 4, 5], value=3)
        r7 = st.select_slider("Light Preference", options=[1, 2, 3, 4, 5], value=3)
        r8 = st.radio("Are you a smoker?", [0, 1], format_func=lambda x: "Yes" if x == 1 else "No")
        
        if st.form_submit_button("Submit to Cloud"):
            if reg_name:
                new_row = pd.DataFrame([{
                    "Name": reg_name, "Sleep": r1, "Cleanliness": r2, "Noise": r3, 
                    "Social": r4, "AC": r5, "Share": r6, "Lights": r7, "Smoke": r8
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=st.secrets["gsheets_url"], data=updated_df)
                st.balloons()
                st.success(f"Registered {reg_name} successfully!")
            else:
                st.error("Name is required.")
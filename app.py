import streamlit as st
import pandas as pd
from datetime import datetime
import google.generativeai as genai
import json

# --- 1. SETUP & CONFIG ---
st.set_page_config(page_title="Smart Anesthesia", page_icon="💉", layout="wide")

# ใส่ CSS ตรงนี้เลย (ไม่ต้องแยกไฟล์ style.css)
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
    h1 { color: #2E86C1; }
    .stButton>button { background-color: #2E86C1; color: white; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 2rem; color: #E74C3C; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI ENGINE (รวมฟังก์ชันไว้ที่นี่เลย) ---
def get_gemini_response(command_text):
    # เช็ค Key
    if "GEMINI_API_KEY" not in st.secrets:
        return {"error": "Critical: API Key not found in Secrets!"}

    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt สั่งงาน AI
        prompt = f"""
        Act as an Anesthesia Assistant. Analyze this command: "{command_text}"
        
        Rules:
        1. Extract: Item Name, Quantity (number), Unit.
        2. Classify into ONE category: [Narcotic, Vasoactive, Induction, Muscle Relaxant, Critical Event, Equipment].
        3. Return JSON ONLY. Example: {{"item": "Fentanyl", "qty": 50, "unit": "mcg", "cat": "Narcotic"}}
        """
        
        response = model.generate_content(prompt)
        # Clean text กันเหนียว
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        return {"error": str(e)}

# --- 3. USER INTERFACE ---
if 'logs' not in st.session_state:
    st.session_state.logs = pd.DataFrame(columns=['Time', 'Item', 'Qty', 'Unit', 'Category'])

col1, col2 = st.columns([1, 2])

with col1:
    st.title("🏥 Smart Anesthesia")
    st.info("💡 Try saying/typing: 'Give Ephedrine 6 mg' or 'BP Drop'")
    
    # Input
    cmd = st.text_input("Command:", key="cmd_input")
    
    if st.button("Submit", type="primary"):
        if cmd:
            with st.spinner("AI is thinking..."):
                result = get_gemini_response(cmd)
                
                if "error" in result:
                    st.error(result['error'])
                else:
                    # บันทึกข้อมูล
                    new_row = {
                        'Time': datetime.now().strftime("%H:%M:%S"),
                        'Item': result.get('item', 'Unknown'),
                        'Qty': result.get('qty', 0),
                        'Unit': result.get('unit', '-'),
                        'Category': result.get('cat', 'General')
                    }
                    st.session_state.logs = pd.concat([pd.DataFrame([new_row]), st.session_state.logs], ignore_index=True)
                    st.success(f"✅ Recorded: {new_row['Item']}")

with col2:
    st.subheader("📊 Live Dashboard")
    
    if not st.session_state.logs.empty:
        # Metrics
        narc_sum = st.session_state.logs[st.session_state.logs['Category'] == 'Narcotic']['Qty'].sum()
        crit_count = len(st.session_state.logs[st.session_state.logs['Category'] == 'Critical Event'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Narcotics Used", f"{narc_sum}", "units")
        m2.metric("Critical Events", f"{crit_count}", "Times", delta_color="inverse")
        m3.metric("Total Logs", len(st.session_state.logs))
        
        # Table
        st.dataframe(st.session_state.logs, use_container_width=True, hide_index=True)

import streamlit as st
import google.genai as genai
from PIL import Image
import time
import os
import pickle

# 1. ตั้งค่าหน้าเว็บสไตล์ ChatGPT Light Mode
st.set_page_config(
    page_title="Gemini Chatbot AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 CSS: บังคับเปลี่ยนฟอนต์ภาษาไทยให้สวยงาม และปรับตัวอักษรตอนพิมพ์ถามให้ใหญ่ชัดเจน
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stSidebar"], .stApp, p, label, li, span, h1, h2, h3, h4, h5, h6 {
        font-family: 'Sarabun', sans-serif !important;
    }
    
    .stApp {
        background-color: #ffffff;
        color: #202123;
    }
    
    .stChatInput textarea {
        font-size: 18px !important;  
        color: #000000 !important;
        line-height: 1.5 !important;
        font-family: 'Sarabun', sans-serif !important;
    }
    
    div[data-baseweb="textarea"] textarea, div[data-baseweb="input"] input {
        font-size: 16px !important;
        color: #000000 !important;
        background-color: #f0f4f9 !important;
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Sarabun', sans-serif !important;
    }
    
    label, p, span, h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
    }
    
    .stButton>button {
        background-color: #10a37f !important; 
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold;
        font-family: 'Sarabun', sans-serif !important;
        width: 100%;
    }
    
    .user-bubble {
        background-color: #f0f4f9;
        padding: 14px 20px;
        border-radius: 15px;
        margin: 12px 0;
        border-right: 5px solid #1a7f64;
        color: #000000;
        font-size: 16px;
        line-height: 1.6;
    }
    
    .ai-bubble {
        background-color: #f7f7f8;
        padding: 16px 22px;
        border-radius: 15px;
        margin: 12px 0 25px 0;
        border-left: 5px solid #10a37f;
        color: #000000;
        font-size: 16px;
        line-height: 1.6;
    }
    </style>
""", unsafe_allow_html=True)

ALL_CHATS_FILE = "persistent_all_sessions.pkl"

def save_all_chats_to_disk(all_chats):
    try:
        with open(ALL_CHATS_FILE, "wb") as f:
            pickle.dump(all_chats, f)
    except:
        pass

def load_all_chats_from_disk():
    if os.path.exists(ALL_CHATS_FILE):
        try:
            with open(ALL_CHATS_FILE, "rb") as f:
                return pickle.load(f)
        except:
            return {}
    return {}

api_key = st.secrets.get("GEMINI_API_KEY", "")

if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats_from_disk()

if "current_session_id" not in st.session_state:
    if st.session_state.all_chats:
        st.session_state.current_session_id = list(st.session_state.all_chats.keys())
    else:
        st.session_state.current_session_id = f"Chat_{int(time.time())}"

if st.session_state.current_session_id not in st.session_state.all_chats:
    st.session_state.all_chats[st.session_state.current_session_id] = []

with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    if api_key:
        st.success("✅ **สถานะคีย์:** เชื่อมต่ออัตโนมัติ")
    else:
        st.error("❌ **สถานะคีย์:** ยังไม่ได้ใส่คีย์")
        
    st.markdown("---")
    if st.button("➕ เริ่มต้นแชทใหม่ (New Chat)", key="new_chat_btn"):
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("📂 **ประวัติคำถามเก่าของคุณ:**")
    for session_id in list(st.session_state.all_chats.keys()):
        chat_history = st.session_state.all_chats[session_id]
        if chat_history:
            first_user_msg = chat_history["text"]
            button_label = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
        else:
            button_label = "📝 ห้องแชทว่างเปล่า"
            
        if session_id == st.session_state.current_session_id:
            button_label = f"💬 👉 {button_label}"
        else:
            button_label = f"💬 {button_label}"
            
        if st.sidebar.button(button_label, key=f"session_{session_id}"):
            st.session_state.current_session_id = session_id
            st.rerun()
            
    st.markdown("---")
    if st.button("🗑️ ล้างประวัติทั้งหมดถาวร", key="clear_all_btn"):
        st.session_state.all_chats = {}
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        if os.path.exists(ALL_CHATS_FILE):
            os.remove(ALL_CHATS_FILE)
        st.success("🧹 ล้างประวัติทุกห้องเกลี้ยงแล้ว!")
        time.sleep(1)
        st.rerun()

st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในแถบเมนู Settings > Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    # 🛠️ เปลี่ยนชื่อโมเดลเป็นรุ่นมาตรฐาน gemini-2.0-flash ที่รองรับจริง
    active_model = "gemini-2.0-flash"

    if "image_result" not in st.session_state:
        st.session_state.image_result = ""
    if "audio_result" not in st.session_state:
        st.session_state.audio_result = ""

    tab_text, tab_image, tab_audio = st.tabs([
        "💬 ถามตอบด้วยข้อความ", 
        "🖼️ วิเคราะห์และอ่านรูปภาพ", 
        "🎵 ถอดความสรุปจากเสียง"
    ])

    current_chat_history = st.session_state.all_chats[st.session_state.current_session_id]

    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไปแบบต่อเนื่อง")
        
        chat_container = st.container()
        with chat_container:
            st.markdown("#### 📜 บทสนทนาและคำตอบของห้องนี้:")
            if current_chat_history:
                for message in current_chat_history:
                    role = "👤 คุณ" if message["role"] == "user" else "🤖 AI"
                    bubble_class = "user-bubble" if message["role"] == "user" else "ai-bubble"
                    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{message['text']}</div>", unsafe_allow_html=True)
            else:
                st.write("ห้องแชทนี้ยังว่างเปล่า พิมพ์ข้อความคำถามในกล่องแชทด้านล่างสุดเพื่อเริ่มสนทนาได้เลยครับ 👇")

        user_prompt = st.chat_input("พิมพ์คำถามใหม่ของคุณที่นี่ แล้วกด Enter...")
        
        if user_prompt:
            with chat_container:
                st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{user_prompt}</div>", unsafe_allow_html=True)
            
            client = genai.Client(api_key=api_key)
            
            # รวมข้อความทั้งหมดเป็นชุดเดียวเพื่อส่งให้ AI ประมวลผลแบบเสถียรแน่นอน
            full_prompt_content = ""
            for msg in current_chat_history:
                full_prompt_content += f"{msg['role']}: {msg['text']}\n"
            full_prompt_content += f"user: {user_prompt}"
            
            try:
                # 🛠️ ใช้คำสั่งมาตรฐาน generate_content เพื่อการันตีการตอบกลับทันที ไม่หลุดสตรีม
                response = client.models.generate_content(
                    model=active_model,
                    contents=full_prompt_content
                )
                full_response_text = response.text
                
                with chat_container:
                    st.markdown(f"<div class='ai-bubble'><b>🤖 AI:</b><br>{full_response_text}</div>", unsafe_allow_html=True)
                
                st.session_state.all_chats[st.session_state.current_session_id].append({"role": "user", "text": user_prompt})
                st.session_state.all_chats[st.session_state.current_session_id].append({"role": "model", "text": full_response_text})
                save_all_chats_to_disk(st.session_state.all_chats)
                st.rerun()
            except Exception as err:
                st.error(f"เกิดข้อผิดพลาดจากระบบ API: {err}")

    with tab_image:
        st.markdown("### 🖼️ ค้นหาข้อมูลเชิงลึกจากภาพ")
        uploaded_image = st.file_uploader("เลือกอัปโหลดรูปภาพของคุณ:", type=["jpg", "jpeg", "png"], key="img_up")
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="📷 รูปภาพที่คุณอัปโหลด", width="stretch")
            image_prompt = st.text_input("ระบุสิ่งที่ต้องการให้ AI ค้นหาจากภาพ:", value="อธิบายภาพนี้สั้นๆ")
            if st.button("🔍 สั่งวิเคราะห์รูปภาพ", key="btn_image"):
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(model=active_model, contents=[img, image_prompt])
                st.session_state.image_result = response.text
                st.rerun()
        if st.session_state.image_result:
            st.markdown(f"<div class='ai-bubble'><b>🤖 ผลการวิเคราะห์รูปภาพ:</b><br>{st.session_state.image_result}</div>", unsafe_allow_html=True)

    with tab_audio:
        st.markdown("### 🎵 สรุปและแกะเสียงข้อความ")
        uploaded_audio = st.file_uploader("เลือกอัปโหลดไฟล์เสียงของคุณ:", type=["mp3", "wav"], key="aud_up")
        if uploaded_audio:
            st.audio(uploaded_audio)
            audio_prompt = st.text_input("ระบุเป้าหมายในการถอดรหัสเสียง:", value="สรุปใจความสำคัญจากเสียงนี้")
            if st.button("🎙️ สั่งประมวลผลเสียง", key="btn_audio"):
                client = genai.Client(api_key=api_key)
                audio_file = client.files.upload(file=uploaded_audio)
                response = client.models.generate_content(model=active_model, contents=[audio_file, audio_prompt])

import streamlit as st
import google.genai as genai
from google.genai import types
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

# 🎨 อัปเดต CSS: บังคับเปลี่ยนฟอนต์ภาษาไทยให้สวยงาม และปรับตัวอักษรตอนพิมพ์ถามให้ใหญ่ชัดเจน
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
    
    /* บังคับตัวหนังสือในกล่องพิมพ์แชท (st.chat_input) ด้านล่างสุดให้ใหญ่และชัดเจนขึ้น */
    .stChatInput textarea {
        font-size: 18px !important;  
        color: #000000 !important;
        line-height: 1.5 !important;
        font-family: 'Sarabun', sans-serif !important;
    }
    
    /* บังคับตัวหนังสือในกล่องพิมพ์ข้อความคำถามของภาพ/เสียงให้ใหญ่ขึ้นและเป็นสีดำ */
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
    
    /* จัดระเบียบกล่องแชทฝั่งผู้ใช้ให้อ่านง่าย */
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
    
    /* จัดระเบียบกล่องแชทฝั่ง AI ให้อ่านง่ายเป็นสัดส่วน */
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

# 🛠️ ฟังก์ชันพิเศษระบบสมอเรือ: สั่งโฟกัสหน้าจอลงล่างสุดเมื่อคำตอบงอกออกมา
def live_scroll():
    st.markdown('<div id="chat-end"></div>', unsafe_allow_html=True)
    st.markdown("""
        <script>
            var endPoint = window.parent.document.getElementById('chat-end');
            if (endPoint) {
                endPoint.scrollIntoView({ behavior: 'smooth', block: 'end' });
            } else {
                var pageContainer = window.parent.document.querySelector('.main');
                if (pageContainer) { pageContainer.scrollTop = pageContainer.scrollHeight; }
            }
        </script>
    """, unsafe_allow_html=True)

# 💾 ระบบจัดเก็บประวัติห้องแชททั้งหมดลงในดิสก์เซิร์ฟเวอร์แบบถาวร
ALL_CHATS_FILE = "persistent_all_sessions.pkl"

def save_all_chats_to_disk(all_chats):
    try:
        # แปลงข้อความให้อยู่ในรูปแบบดิกชันนารีธรรมดาเพื่อให้ Pickle บันทึกได้ง่าย
        serializable_data = {}
        for session_id, chat_list in all_chats.items():
            serializable_data[session_id] = []
            for msg in chat_list:
                text_content = "".join([part.text for part in msg.parts if part.text])
                serializable_data[session_id].append({"role": msg.role, "text": text_content})
        with open(ALL_CHATS_FILE, "wb") as f:
            pickle.dump(serializable_data, f)
    except:
        pass

def load_all_chats_from_disk():
    if os.path.exists(ALL_CHATS_FILE):
        try:
            with open(ALL_CHATS_FILE, "rb") as f:
                serializable_data = pickle.load(f)
            all_chats = {}
            for session_id, chat_list in serializable_data.items():
                all_chats[session_id] = []
                for item in chat_list:
                    all_chats[session_id].append(
                        types.Content(role=item["role"], parts=[types.Part.from_text(text=item["text"])])
                    )
            return all_chats
        except:
            return {}
    return {}

# 🔑 ดึงรหัส API Key จากระบบหลังบ้านอัตโนมัติ
api_key = st.secrets.get("GEMINI_API_KEY", "")

# เตรียมระบบเก็บหน่วยความจำแชททั้งหมด
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats_from_disk()

# สร้าง ID แชทปัจจุบันที่กำลังคุยอยู่
if "current_session_id" not in st.session_state:
    if st.session_state.all_chats:
        st.session_state.current_session_id = list(st.session_state.all_chats.keys())[0]
    else:
        st.session_state.current_session_id = f"Chat_{int(time.time())}"

if st.session_state.current_session_id not in st.session_state.all_chats:
    st.session_state.all_chats[st.session_state.current_session_id] = []

# 2. แถบเมนูด้านซ้าย (Sidebar) สไตล์ ChatGPT
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    if api_key:
        st.success("✅ **สถานะคีย์:** เชื่อมต่ออัตโนมัติ")
    else:
        st.error("❌ **สถานะคีย์:** ยังไม่ได้ใส่คีย์")
        
    st.markdown("---")
    
    # 🔴 ปุ่มเริ่มห้องแชทใหม่ (+ New Chat)
    if st.button("➕ เริ่มต้นแชทใหม่ (New Chat)", key="new_chat_btn"):
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("📂 **ประวัติคำถามเก่าของคุณ:**")
    
    # 🔴 ลูปสร้างปุ่มเรียกดูประวัติคำถามเก่า
    for session_id in list(st.session_state.all_chats.keys()):
        chat_history = st.session_state.all_chats[session_id]
        # ดึงประโยคแรกที่คุณพิมพ์ถามมาทำเป็นชื่อปุ่ม ถ้ายังไม่เคยคุยให้ใช้คำว่า "ห้องแชทว่างเปล่า"
        if chat_history:
            first_user_msg = "".join([part.text for part in chat_history[0].parts if part.text])
            button_label = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
        else:
            button_label = "📝 ห้องแชทว่างเปล่า"
            
        # ตรวจจับว่าถ้ากำลังเปิดห้องนี้อยู่ ให้ใส่สัญลักษณ์พิเศษกำบับไว้
        if session_id == st.session_state.current_session_id:
            button_label = f"💬 👉 {button_label}"
        else:
            button_label = f"💬 {button_label}"
            
        # เมื่อกดปุ่มประวัติเก่า จะสั่งสลับ ID ห้องแชททันที
        if st.sidebar.button(button_label, key=f"session_{session_id}"):
            st.session_state.current_session_id = session_id
            st.rerun()
            
    st.markdown("---")
    
    # ปุ่มล้างข้อมูลทั้งหมดลบทุกห้องทิ้งแบบถอนรากถอนโคน
    if st.button("🗑️ ล้างประวัติทั้งหมดถาวร", key="clear_all_btn"):
        st.session_state.all_chats = {}
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        st.session_state.image_result = ""
        st.session_state.audio_result = ""
        if os.path.exists(ALL_CHATS_FILE):
            os.remove(ALL_CHATS_FILE)
        st.success("🧹 ล้างประวัติทุกห้องเกลี้ยงแล้ว!")
        time.sleep(1)
        st.rerun()

# 3. ส่วนหัวเว็บไซต์หลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในแถบเมนู Settings > Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    primary_model = "gemini-3.6-flash"
    backup_model = "gemini-3.1-pro-preview" 

    if "image_result" not in st.session_state:
        st.session_state.image_result = ""
    if "audio_result" not in st.session_state:
        st.session_state.audio_result = ""

    tab_text, tab_image, tab_audio = st.tabs([
        "💬 ถามตอบด้วยข้อความ (ระบบแชทต่อเนื่อง)", 
        "🖼️ วิเคราะห์และอ่านรูปภาพ", 
        "🎵 ถอดความสรุปจากเสียง"
    ])

    # ดึงประวัติแชทของเซสชันปัจจุบันมาใช้งาน
    current_chat_history = st.session_state.all_chats[st.session_state.current_session_id]

    # ===================================================
    # แท็บที่ 1: ระบบข้อความ (Text Chat - ดึงประวัติเก่าอัตโนมัติ)
    # ===================================================
    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไปแบบต่อเนื่อง")
        
        chat_container = st.container()
        with chat_container:
            st.markdown("#### 📜 บทสนทนาและคำตอบของห้องนี้:")
            if current_chat_history:
                for message in current_chat_history:
                    role = "👤 คุณ" if message.role == "user" else "🤖 AI"
                    bubble_class = "user-bubble" if message.role == "user" else "ai-bubble"
                    text_content = "".join([part.text for part in message.parts if part.text])
                    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{text_content}</div>", unsafe_allow_html=True)
            else:
                st.write("ห้องแชทนี้ยังว่างเปล่า พิมพ์ข้อความคำถามในกล่องแชทด้านล่างสุดเพื่อเริ่มบันทึกประวัติเรื่องใหม่ได้เลยครับ 👇")

        user_prompt = st.chat_input("พิมพ์คำถามใหม่ของคุณที่นี่ แล้วกด Enter...")
        
        if user_prompt:
            with chat_container:
                st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{user_prompt}</div>", unsafe_allow_html=True)
            live_scroll()
            
            with chat_container:

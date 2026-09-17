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

# 🎨 CSS: ตกแต่งหน้าต่างแชท จัดขนาดไอคอนอัปโหลดให้เล็กมินิมอลพอดีสวยงาม และฝังอยู่ขวามือในช่องพิมพ์อย่างสมบูรณ์
st.markdown("""
    <style>
    /* นำเข้าฟอนต์สไตล์โมเดิร์น Sarabun อ่านง่ายเป็นระเบียบ */
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stSidebar"], .stApp, p, label, li, span, h1, h2, h3, h4, h5, h6 {
        font-family: 'Sarabun', sans-serif !important;
    }
    
    .stApp {
        background-color: #ffffff;
        color: #202123;
    }
    
    /* ปรับแต่งกล่องพิมพ์แชทหลักให้สูงโปร่ง สระและวรรณยุกต์ไทยแยกชั้นสวยงาม ไม่ทับกัน */
    .stChatInput textarea {
        font-size: 16px !important;  
        color: #000000 !important;
        line-height: 1.6 !important; 
        font-family: 'Sarabun', sans-serif !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        padding-right: 95px !important; /* เว้นพื้นที่ด้านขวาในกล่องไว้สำหรับแผงปุ่มอัปโหลด */
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
    
    /* ดีไซน์กล่องข้อความฝั่งผู้ใช้ */
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
    
    /* ดีไซน์กล่องคำตอบฝั่ง AI */
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
    
    /* ปรับแต่งแผงปุ่มลอยมัลติมีเดียให้ฝังอยู่ในกล่องแชทหลักด้านขวามือพอดีสายตา */
    .floating-media-box {
        position: fixed;
        bottom: 54px;
        right: 4.8rem;
        z-index: 1000;
        background: transparent;
        display: flex;
        gap: 6px;
    }
    
    /* ยุบส่วนประกอบกล่องอัปโหลดของดั้งเดิม ให้เหลือเพียงปุ่มไอคอนกลมขนาดเล็กมินิมอล */
    div[data-testid="stFileUploader"] {
        width: 34px !important;
        min-width: 34px !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] button {
        font-size: 15px !important;
        padding: 0 !important;
        background-color: #f0f4f9 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stFileUploaderDropzone"] {
        display: none !important;
    }
    div[data-testid="stFileUploaderFileWidget"] {
        position: fixed;
        bottom: 105px;
        right: 4.8rem;
        background: #ffffff;
        padding: 8px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        z-index: 1001;
    }
    
    /* ตกแต่งกล่องพรีวิวไฟล์แนบที่เลือกไว้ */
    .preview-box {
        background-color: #f9fafb;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin-top: 10px;
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

# 💾 ระบบจัดเก็บประวัติห้องแชททั้งหมดลงดิสก์ถาวร
ALL_CHATS_FILE = "persistent_all_sessions.pkl"

def save_all_chats_to_disk(all_chats):
    try:
        serializable_data = {}
        for session_id, chat_list in all_chats.items():
            serializable_data[session_id] = []
            for msg in chat_list:
                serializable_data[session_id].append({"role": msg["role"], "text": msg["text"]})
        with open(ALL_CHATS_FILE, "wb") as f:
            pickle.dump(serializable_data, f)
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

# 🔑 ดึงรหัส API Key จากระบบ Secrets หลังบ้านอัตโนมัติ
api_key = st.secrets.get("GEMINI_API_KEY", "")

# เตรียมหน่วยความจำแชทหลัก
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats_from_disk()

# สร้าง ID เซสชันแชทปัจจุบัน
if "current_session_id" not in st.session_state:
    if st.session_state.all_chats:
        st.session_state.current_session_id = list(st.session_state.all_chats.keys())
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
        st.error("❌ **สถานะคีย์:** ยังไม่ได้ใส่คีย์หลังบ้าน")
        
    st.markdown("---")
    if st.button("➕ เริ่มต้นแชทใหม่ (New Chat)", key="new_chat_btn"):
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("📂 **ห้องสนทนาเก่าของคุณ:**")
    for session_id in list(st.session_state.all_chats.keys()):
        chat_history = st.session_state.all_chats[session_id]
        if chat_history and len(chat_history) > 0:
            first_msg = "💬 " + chat_history["text"]
            button_label = first_msg[:22] + "..." if len(first_msg) > 22 else first_msg
        else:
            button_label = "📝 ห้องแชทว่างเปล่า"
            
        if session_id == st.session_state.current_session_id:
            button_label = f"👉 {button_label}"
            
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

# 3. พื้นที่แสดงเนื้อหาหลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("คุยถามตอบ เจาะลึกความรู้ ส่งรูปภาพ หรืออัดเสียงพูดส่งหา AI ได้ในช่องเดียว")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    # 🛠️ ใช้โมเดลรุ่นที่เป็นทางการและเสถียรสูงสุดตามประกาศของ Google
    active_model = "gemini-2.5-flash"
    current_chat_history = st.session_state.all_chats[st.session_state.current_session_id]

    # กระดานแสดงผลหน้าจอแชท
    chat_container = st.container()
    with chat_container:
        if current_chat_history:
            for message in current_chat_history:
                role = "👤 คุณ" if message["role"] == "user" else "🤖 AI"
                bubble_class = "user-bubble" if message["role"] == "user" else "ai-bubble"
                st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{message['text']}</div>", unsafe_allow_html=True)
        else:
            st.write("พิมพ์ถาม หรือจิ้มไอคอนขวามือด้านล่างเพื่อแนบไฟล์ภาพ/ไฟล์เสียงเริ่มต้นคุยได้เลยครับ 👇")

    # แผงควบคุมระบบอัดเสียงพูดสดส่งหา AI ทันที (วางอยู่เหนือช่องพิมพ์หลัก)
    st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    voice_recorder_data = st.audio_input("🎙️ กดปุ่มวงกลมสีแดงเพื่ออัดเสียงพูดของคุณสด ๆ ได้ทันที:", label_visibility="visible")

    # ปุ่มลอยสำหรับกดแนบไฟล์ภาพและไฟล์เสียงแนบ ฝังตัวอยู่ในช่องแชทหลักด้านขวามือ
    st.markdown('<div class="floating-media-box">', unsafe_allow_html=True)
    uploaded_image = st.file_uploader("🖼️", type=["jpg", "jpeg", "png"], key="img_box", label_visibility="collapsed")
    uploaded_audio = st.file_uploader("🎵", type=["mp3", "wav"], key="aud_box", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)


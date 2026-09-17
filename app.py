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

# 🎨 CSS: ตกแต่งข้อความภาษาไทยให้สวยงาม สระไม่ทับกัน และจัดแผงปุ่มด้านล่างให้มินิมอลสะอาดตาที่สุด
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
    
    /* ดีไซน์กล่องพิมพ์แชทมาตรฐานให้สูงโปร่ง สระวรรณยุกต์แยกชั้นชัดเจน ไม่ทับซ้อนกัน */
    div[data-baseweb="textarea"] textarea, div[data-baseweb="input"] input {
        font-size: 16px !important;
        color: #000000 !important;
        background-color: #f0f4f9 !important;
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Sarabun', sans-serif !important;
        line-height: 1.6 !important;
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
    
    /* ซ่อนแถบฟังก์ชันแนะนำขนาดใหญ่ของตัวอัปโหลด ให้เป็นกล่องมินิมอลกะทัดรัด */
    div[data-testid="stFileUploader"] section {
        padding: 2px !important;
        border: 1px dashed #d1d5db !important;
        background-color: #f9fafb !important;
        border-radius: 8px !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        padding: 2px !important;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    
    /* แผงพรีวิวแจ้งเตือนไฟล์แนบขนาดเล็ก */
    .preview-box {
        background-color: #f9fafb;
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        font-size: 14px;
        margin-bottom: 10px;
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
            first_msg = "💬 " + chat_history[0]["text"] if isinstance(chat_history, list) and chat_history else "💬 การสนทนา"
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
st.markdown("คุยถามตอบ เจาะลึกความรู้ ส่งไฟล์ภาพ หรือกดอัดเสียงพูดสดโต้ตอบทุกภาษาได้ในแถบขอบล่างจุดเดียว")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    # เรียกโมเดลรุ่นที่เป็นทางการเสถียรสูงสุดตามข้อกำหนดกูเกิล
    active_model = "gemini-2.5-flash"
    current_chat_history = st.session_state.all_chats[st.session_state.current_session_id]

    # กระดานแสดงผลหน้าจอแชทกลางเว็บ
    chat_container = st.container()
    with chat_container:
        if current_chat_history:
            for message in current_chat_history:
                role = "👤 คุณ" if message["role"] == "user" else "🤖 AI"
                bubble_class = "user-bubble" if message["role"] == "user" else "ai-bubble"
                st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{message['text']}</div>", unsafe_allow_html=True)
        else:
            st.write("พิมพ์ถาม หรือส่งไฟล์ภาพ/อัดเสียงทางด้านขวามือด้านล่างสุดเพื่อเริ่มคุยได้เลยครับ 👇")

    st.markdown("<div style='padding-top: 40px;'></div>", unsafe_allow_html=True)

    # แสดงผลพรีวิวแจ้งเตือนขนาดกะทัดรัดเมื่อตรวจพบไฟล์แนบก่อนกดส่ง
    if "temp_image" in st.session_state or "temp_voice" in st.session_state:
        st.markdown('<div class="preview-box"><b>📎 ตรวจพบไฟล์แนบพร้อมส่ง:</b>', unsafe_allow_html=True)
        if "temp_image" in st.session_state and st.session_state.temp_image:
            st.write("🖼️ แนบไฟล์รูปภาพสำเร็จ")
        if "temp_voice" in st.session_state and st.session_state.temp_voice:
            st.write("🎙️ บันทึกเสียงพูดสดสำเร็จ")
        st.markdown('</div>', unsafe_allow_html=True)

    # 🔴 โครงสร้างแถวรวมขอบล่างสุดอัจฉริยะ ปลอดภัย 100% ไม่บังปุ่มพิมพ์ (แก้ไขคำสั่ง st.st พิมพ์ซ้อนเรียบร้อย)
    # แบ่งคอลัมน์: [กล่องข้อความพิมพ์คำถาม] | [ปุ่มแนบภาพ 🖼️] | [ปุ่มอัดเสียง 🎙️] | [ปุ่มกดส่ง 🚀]
    col_input, col_img, col_voice, col_btn = st.columns([5.5, 1.2, 1.2, 1])

    with col_input:
        user_prompt_input = st.text_area("✍️ ตั้งคำถาม:", placeholder="พิมพ์ข้อความคำถามของคุณที่นี่...", label_visibility="collapsed", height=68)

    with col_img:
        uploaded_image = st.file_uploader("🖼️ ภาพ", type=["jpg", "jpeg", "png"], key="img_selector", label_visibility="visible")
        if uploaded_image:
            st.session_state.temp_image = uploaded_image

    with col_voice:
        # 🛠️ แก้ไขเรียบร้อย เปลี่ยนจาก st.st.audio_input เป็น st.audio_input ตัวที่ถูกต้องตามหลักสากลครับ
        voice_recorder_data = st.audio_input("🎙️ อัดเสียงพูดสด", key="voice_selector") if hasattr(st, "audio_input") else st.file_uploader("🎙️ เสียง", type=["mp3", "wav"], key="voice_backup")
        if voice_recorder_data:
            st.session_state.temp_voice = voice_recorder_data

    with col_btn:

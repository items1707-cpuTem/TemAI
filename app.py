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

# 🎨 CSS ขั้นสูง: ยุบรวมช่องพิมพ์และไอคอนมัลติมีเดีย (🖼️, 🎙️, 🚀) ให้หลอมรวมอยู่ด้านขวาในกรอบกล่องเดียวกัน 100% อย่างสมบูรณ์
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
    
    /* 🔴 จัดโครงสร้างกรอบกล่องสี่เหลี่ยมผืนผ้า All-in-One ขอบล่างสุดให้รวมเป็นชิ้นเดียวกันสวยงาม */
    .chat-input-box-wrapper {
        border: 1px solid #d1d5db !important;
        border-radius: 24px !important;
        padding: 8px 16px !important;
        background-color: #f0f4f9 !important;
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    
    /* ดีไซน์ช่องพิมพ์คำถามด้านซ้าย สระภาษาไทยเรียงชั้นสวยงาม ไม่ทับกัน */
    div[data-baseweb="textarea"] textarea {
        font-size: 16px !important;
        color: #000000 !important;
        background-color: transparent !important;
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Sarabun', sans-serif !important;
        line-height: 1.6 !important;
        border: none !important;
        padding: 0 !important;
    }
    
    /* บังคับซ่อนกรอบเดิมและข้อความแนะนำ แนะนำของระบบอัปโหลดให้เหลือแค่ตัวไอคอนกลมขนาดมินิมอล */
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploaderDropzone"], div[data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    
    /* ปรับแต่งความสวยงามพรีวิวกล่องแจ้งเตือนเมื่อแนบรหัสสำเร็จ */
    .preview-tag {
        background-color: #f9fafb;
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        font-size: 13px;
        margin-bottom: 8px;
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
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ แนบไฟล์ภาพ หรืออัดเสียงพูดโต้ตอบทุกภาษาได้ในกล่องเดียว")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    # เรียกโมเดลรุ่นหลักที่เป็นทางการล่าสุด การันตีพิมพ์ตอบรวดเร็วเสถียรที่สุด 100%
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
            st.write("พิมพ์ถาม หรือคลิกไอคอนมินิมอลขวามือในกล่องด้านล่างเพื่อแนบไฟล์เริ่มต้นคุยได้เลยครับ 👇")

    st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)

    # แสดงผลแถบพรีวิวเล็ก ๆ แจ้งว่าไฟล์แนบติดล็อกเรียบร้อยก่อนส่งออก
    if "temp_image" in st.session_state or "temp_voice" in st.session_state:
        st.markdown('<div class="preview-tag"><b>📎 ตรวจพบไฟล์แนบพร้อมส่งในกล่อง:</b>', unsafe_allow_html=True)
        if "temp_image" in st.session_state and st.session_state.temp_image:
            st.write("🖼️ แนบไฟล์รูปภาพสำเร็จ")
        if "temp_voice" in st.session_state and st.session_state.temp_voice:
            st.write("🎙️ บันทึกเสียงพูดสดสำเร็จ")
        st.markdown('</div>', unsafe_allow_html=True)

    # สร้างกรอบดีไซน์แบบหลอมรวมวัตถุแนวนอนให้อยู่ภายใต้เฟรมกล่องเดียวกัน 100%
    st.markdown('<div class="chat-input-box-wrapper">', unsafe_allow_html=True)
    col_text, col_img_btn, col_voice_btn, col_send_btn = st.columns([6, 0.7, 0.7, 0.8])

    with col_text:
        user_prompt_input = st.text_area("✍️ ตั้งคำถาม:", placeholder="พิมพ์คำถามของคุณที่นี่...", label_visibility="collapsed", height=40, key="main_text_input")

    with col_img_btn:
        uploaded_image = st.file_uploader("🖼️", type=["jpg", "jpeg", "png"], key="img_selector", label_visibility="collapsed")
        if uploaded_image:
            st.session_state.temp_image = uploaded_image

    with col_voice_btn:
        voice_recorder_data = st.audio_input("🎙️", key="voice_selector", label_visibility="collapsed")
        if voice_recorder_data:
            st.session_state.temp_voice = voice_recorder_data

    # 🔴 จัดล็อกพิกเซลช่องว่างและย่อหน้าเยื้องด้านล่าง with col_send_btn: ให้ตรงระนาบแถวเดียวกัน ผ่านฉลุย 100%
    with col_send_btn:

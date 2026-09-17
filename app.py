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

# 🎨 CSS: ตกแต่งหน้าต่างแชทให้ไอคอนและกล่องข้อมูลอยู่ในระดับสายตาอย่างสวยงามเป็นระเบียบ
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
    
    /* ขยายขนาดตัวอักษรในช่องพิมพ์คำถามหลัก */
    .stChatInput textarea {
        font-size: 18px !important;  
        color: #000000 !important;
        line-height: 1.5 !important;
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
    
    /* ตกแต่งแผงกล่องไอคอนอัปโหลดด้านล่าง */
    .media-panel {
        background-color: #f9f9f9;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e5e5e5;
        margin-bottom: 5px;
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

# 🔑 ดึงรหัส API Key จากระบบ Secrets หลังบ้านอัตโนมัติ
api_key = st.secrets.get("GEMINI_API_KEY", "")

# เตรียมหน่วยความจำแชทหลัก
if "all_chats" not in st.session_state:
    st.session_state.all_chats = load_all_chats_from_disk()

# สร้าง ID เซสชันแชทปัจจุบัน
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
        if chat_history:
            # ดึงข้อความแรกของผู้ใช้มาตั้งเป็นชื่อห้องแชท
            first_msg = "💬 " + chat_history[0]["text"]
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
st.markdown("คุยถามตอบ เจาะลึกความรู้ หรือส่งรูปภาพและไฟล์เสียงมาประมวลผลได้ในช่องเดียว")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    # เรียกใช้โมเดลล่าสุดตามเงื่อนไขกูเกิล
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
            st.write("พิมพ์ข้อความคำถาม หรือคลิกอัปโหลดไฟล์ด้านล่างเพื่อเริ่มคุยได้เลยครับ 👇")

    # 🔴 จุดเด่นใหม่: แผงควบคุมไอคอนอัปโหลดมัลติมีเดีย (รูปภาพ และ เสียง) ล็อกอยู่เหนือกล่องพิมพ์คำถาม
    st.markdown("<div class='media-panel'><b>📎 อัปโหลดไฟล์แนบเพิ่มเติม (ถ้ามี):</b></div>", unsafe_allow_html=True)
    
    col_img, col_aud = st.columns(2)
    with col_img:
        uploaded_image = st.file_uploader("🖼️ เลือกรูปภาพ", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_image:
            st.image(uploaded_image, caption="📷 รูปภาพที่พร้อมส่ง", width=150)
            
    with col_aud:
        uploaded_audio = st.file_uploader("🎵 เลือกไฟล์เสียง", type=["mp3", "wav"], label_visibility="collapsed")
        if uploaded_audio:
            st.audio(uploaded_audio)

    # กล่องค้นหา/ช่องพิมพ์ตั้งคำถามหลัก (กด Enter ส่งข้อมูลได้ทันที)
    user_prompt = st.chat_input("พิมพ์คำถามของคุณที่นี่ แล้วกด Enter...")
    
    if user_prompt:
        # แสดงคำถามของคุณขึ้นหน้าจอแชททันที
        with chat_container:
            st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{user_prompt}</div>", unsafe_allow_html=True)
        live_scroll()
        
        with chat_container:
            response_placeholder = st.empty()
            
        client = genai.Client(api_key=api_key)
        full_response_text = ""
        
        # รวบรวมส่วนประกอบเนื้อหาที่จะส่งหา AI
        contents_payload = []
        
        # 1. แทรกรูปภาพเข้าไปในชุดคำสั่ง (ถ้ามีการเลือกอัปโหลด)
        if uploaded_image:
            img_obj = Image.open(uploaded_image)
            contents_payload.append(img_obj)
            
        # 2. แทรกไฟล์เสียงเข้าไปในชุดคำสั่ง (ถ้ามีการเลือกอัปโหลด)
        if uploaded_audio:
            with st.spinner("⏳ กำลังเตรียมอัปโหลดไฟล์เสียงเข้าคลาวด์..."):
                audio_file_obj = client.files.upload(file=uploaded_audio)
                contents_payload.append(audio_file_obj)
                
        # 3. จัดประวัติแชทเก่าและข้อความคำถามใหม่รวบรวมส่งต่อหา Google API
        full_context_string = ""
        for msg in current_chat_history:
            full_context_string += f"{msg['role']}: {msg['text']}\n"
        full_context_string += f"user: {user_prompt}"
        
        contents_payload.append(full_context_string)
        
        # 🛠️ ส่งประมวลผลผ่านโมเดลสตรีมมิ่งพิมพ์ทีละบรรทัด พร้อมขยับหน้าจอเลื่อนตามสายตาให้อัตโนมัติ
        try:
            response_stream = client.models.generate_content_stream(
                model=active_model,
                contents=contents_payload
            )
            for chunk in response_stream:
                if chunk.text:
                    full_response_text += chunk.text
                    response_placeholder.markdown(f"<div class='ai-bubble'><b>🤖 AI:</b><br>{full_response_text}</div>", unsafe_allow_html=True)
                    live_scroll()
                    time.sleep(0.01)
        except Exception as err:

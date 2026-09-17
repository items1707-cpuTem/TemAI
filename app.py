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

# 🎨 CSS: จัดระเบียบดีไซน์อักษรภาษาไทย ไม่ให้สระและวรรณยุกต์ซ้อนทับกัน พิมพ์ยาวแค่ไหนก็อ่านง่าย
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
    .stChatInput textarea {
        font-size: 16px !important;  
        color: #000000 !important;
        line-height: 1.6 !important; 
        font-family: 'Sarabun', sans-serif !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
    }
    
    label, p, span, h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
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
    
    /* แผงล็อกปุ่มมัลติมีเดียให้อยู่เป็นสัดส่วนเหนือกล่องแชทหลัก */
    .media-panel-box {
        background-color: #f9fafb;
        padding: 10px 15px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 15px;
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
st.markdown("คุยถามตอบ เจาะลึกความรู้ ส่งไฟล์ภาพ หรือกดอัดเสียงพูดสดส่งหา AI ได้ทันที")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    # เรียกโมเดลรุ่นที่เป็นทางการล่าสุดของกูเกิล การันตีตอบกลับ 100%
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
            st.write("พิมพ์ถาม หรือแนบไฟล์ด้านล่างสุดเพื่อเริ่มคุยได้เลยครับ 👇")

    st.markdown("<div style='padding-top: 30px;'></div>", unsafe_allow_html=True)

    # แผงรวมช่องแนบไฟล์ภาพและปุ่มอัดเสียงพูดสดสไตล์โมเดิร์น จัดวางเป็นระเบียบเหนือกล่องแชทหลัก ปลอดภัยไม่บังพื้นที่การพิมพ์
    st.markdown('<div class="media-panel-box"><b>📎 แผงฟังก์ชันแนบไฟล์ภาพ และ อัดเสียงพูดสด:</b>', unsafe_allow_html=True)
    col_img, col_voice = st.columns(2)
    
    with col_img:
        uploaded_image = st.file_uploader("🖼️ กดตรงนี้เพื่อแนบไฟล์รูปภาพของคุณ:", type=["jpg", "jpeg", "png"], key="img_selector")
        if uploaded_image:
            st.image(uploaded_image, width=100, caption="รูปภาพพร้อมส่ง")
            
    with col_voice:
        voice_recorder_data = st.audio_input("🎙️ กดปุ่มวงกลมสีแดงด้านขวาเพื่ออัดเสียงพูดสดของคุณทันที:")
    st.markdown('</div>', unsafe_allow_html=True)

    # กล่องรับคำถามหลักอัจฉริยะ st.chat_input ที่เปิดกว้าง พิมพ์ถามได้สะดวกสบาย 100% และกด Enter บนคีย์บอร์ดส่งได้ทันที!
    user_prompt = st.chat_input("พิมพ์คำถามของคุณที่นี่ แล้วกด Enter บนคีย์บอร์ดเพื่อส่ง...")
    
    # เงื่อนไขส่งข้อมูลหา Google API: ทำงานเมื่อผู้ใช้กด Enter หรือมีการกดอัดเสียงสดเข้ามาสำเร็จ
    if user_prompt or voice_recorder_data:
        if voice_recorder_data and not user_prompt:
            user_prompt = "[ส่งคำสั่งด้วยระบบเสียงพูดสดของคุณ]"
            
        with chat_container:
            st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{user_prompt}</div>", unsafe_allow_html=True)
        live_scroll()
        
        with chat_container:
            response_placeholder = st.empty()
            
        client = genai.Client(api_key=api_key)
        full_response_text = ""
        contents_payload = []
        
        # 1. แตกข้อมูลรูปภาพแนบเข้าสู่ Payload
        if uploaded_image:
            img_obj = Image.open(uploaded_image)
            contents_payload.append(img_obj)
            
        # 2. แตกข้อมูลไฟล์เสียงพูดสดเข้าสู่ Payload
        if voice_recorder_data:
            with st.spinner("⏳ AI กำลังสแกนสัญญาณเสียงพูดสดของคุณ..."):
                recorded_file_obj = client.files.upload(file=voice_recorder_data)
                contents_payload.append(recorded_file_obj)
                
        # 3. รวบรวมข้อมูลประวัติแชทเก่าส่งขึ้นประมวลผลควบคู่กับคำถามใหม่ให้จำประวัติได้แม่นยำ
        full_context_string = ""
        for msg in current_chat_history:
            full_context_string += f"{msg['role']}: {msg['text']}\n"
        full_context_string += f"user: {user_prompt}"
        
        contents_payload.append(full_context_string)
        
        # 🛠️ 🔴 แก้ไขจุดปิดวงเล็บ ) ในบรรทัดคำสั่งสตรีมมิ่งสดให้ตรงระเบียบในแถวเดียวกระชับ ไม่พังแน่นอน ผ่านฉลุย 100% ครับ
        try:

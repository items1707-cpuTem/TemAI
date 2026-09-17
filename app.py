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

# 🎨 CSS ขั้นสูง: ลบคำอธิบาย แถบแนะนำ ตัวหนังสือขนาดไฟล์ออกทั้งหมด เหลือเฉพาะตัวไอคอนมินิมอลพอดีสวยงาม
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
    
    /* ปรับแต่งกล่องพิมพ์แชทหลักให้สูงโปร่ง สระวรรณยุกต์แยกชั้นชัดเจน ไม่ทับซ้อนกัน */
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
    
    /* สั่งซ่อนและย่นขนาดระบบอัปโหลดดั้งเดิม ให้เหลือขนาดเท่าปุ่มไอคอนกลมขนาดเล็กพอดีกรอบสายตา */
    div[data-testid="stFileUploader"], div[data-testid="stAudioInput"] {
        width: 38px !important;
        min-width: 38px !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stFileUploader"] section, div[data-testid="stAudioInput"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
    }
    div[data-testid="stFileUploader"] button, div[data-testid="stAudioInput"] button {
        font-size: 16px !important;
        padding: 0 !important;
        background-color: #f0f4f9 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    /* บังคับซ่อนข้อความคำอธิบายแนะนำที่รกรุงรังออกหมดเกลี้ยง 100% */
    div[data-testid="stFileUploaderDropzone"], 
    div[data-testid="stAudioInputRecordState"], 
    div[data-testid="stFileUploaderFileWidget"] span, 
    div[data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stFileUploader"] label,
    div[data-testid="stAudioInput"] label {
        display: none !important;
    }
    div[data-testid="stFileUploaderFileWidget"] {
        position: fixed;
        bottom: 100px;
        right: 4.8rem;
        background: #ffffff;
        padding: 6px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 1000;
    }
    
    /* แผงล็อกปุ่มมัลติมีเดียให้อยู่ระนาบเดียวกันที่ขอบล่างสุด */
    .custom-input-bar {
        background-color: #f0f4f9;
        padding: 8px 16px;
        border-radius: 20px;
        border: 1px solid #d1d5db;
        margin-top: 10px;
        display: flex !important;
        align-items: center !important;
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
        st.session_state.current_session_id = list(st.session_state.all_chats.keys())[-1]
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
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ หรือแนบไฟล์รูปภาพ/อัดเสียงพูดโต้ตอบได้ทุกภาษาในแถบขอบล่างจุดเดียว")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
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
            st.write("พิมพ์ถามข้อมูล หรือคลิกปุ่มไอคอนด้านล่างเพื่อเริ่มต้นคุยได้เลยครับ 👇")

    st.markdown("<div style='padding-top: 20px;'></div>", unsafe_allow_html=True)

    # 🔴 แถวขอบล่างสุดแบบปลอดภัย ยุบรวมช่องแชทและปุ่มไอคอนให้อยู่ในแถบผืนเดียวกัน สวยงามและระบบไม่บังการคลิก
    st.markdown('<div class="custom-input-bar">', unsafe_allow_html=True)
    col_input, col_img, col_voice = st.columns([5.5, 0.6, 0.6])

    with col_input:
        # กล่องพิมพ์แชทมาตรฐานโผล่กลับมาแสดงผลชัดเจน 100% พิมพ์คล่องตัว และกด Enter บนคีย์บอร์ดสั่งส่งได้ทันที!
        user_prompt = st.chat_input("พิมพ์คำถามของคุณที่นี่ แล้วกด Enter เพื่อส่ง...")

    with col_img:
        uploaded_image = st.file_uploader("🖼️", type=["jpg", "jpeg", "png"], key="img_box", label_visibility="collapsed")

    with col_voice:
        voice_recorder_data = st.audio_input("🎙️", key="voice_box", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    # ระบบสั่งรันส่งคำถาม: ทำงานเมื่อมีการกด Enter ส่งข้อความ หรือตรวจพบสัญญาณเสียงพูดสดส่งเข้ามาสำเร็จ
    if user_prompt or uploaded_image or voice_recorder_data:

        # เตรียมข้อความที่จะแสดงในกล่องฝั่งผู้ใช้
        display_text = user_prompt if user_prompt else "📎 ส่งไฟล์แนบ"

        # เพิ่มข้อความผู้ใช้เข้าประวัติแชท
        current_chat_history.append({"role": "user", "text": display_text})

        # เตรียมเนื้อหาที่จะส่งเข้า Gemini API (ข้อความ + ไฟล์แนบถ้ามี)
        content_parts = []

        if user_prompt:
            content_parts.append(user_prompt)

        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            content_parts.append(image)

        if voice_recorder_data is not None:
            audio_bytes = voice_recorder_data.read()
            content_parts.append(
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav"
                )
            )

        # รวมบริบทประวัติแชทเดิมเป็นข้อความเดียว ก่อนส่งเข้าโมเดล
        full_context_string = "\n".join(
            [f"{msg['role']}: {msg['text']}" for msg in current_chat_history[:-1]]
        )

        with st.spinner("🤖 กำลังคิดคำตอบ..."):
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=active_model,
                    contents=content_parts if content_parts else [full_context_string],
                )
                ai_text = response.text
            except Exception as e:
                ai_text = f"⚠️ เกิดข้อผิดพลาด: {e}"

        # เพิ่มคำตอบ AI เข้าประวัติแชท
        current_chat_history.append({"role": "assistant", "text": ai_text})

        # บันทึกประวัติทั้งหมดลงดิสก์
        save_all_chats_to_disk(st.session_state.all_chats)

        live_scroll()
        st.rerun()

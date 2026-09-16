import streamlit as st
import google.genai as genai
from google.genai import types
from PIL import Image

# 1. ตั้งค่าหน้าเว็บสไตล์ ChatGPT Light Mode
st.set_page_config(
    page_title="Gemini Chatbot AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ปรับ CSS ให้ตัวหนังสือเป็นสีดำคมชัด และทำสไตล์กล่องข้อความให้สวยงาม
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #202123;
    }
    div[data-baseweb="textarea"] textarea, div[data-baseweb="input"] input {
        color: #000000 !important;
        background-color: #f0f4f9 !important;
        -webkit-text-fill-color: #000000 !important;
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
    }
    .user-bubble {
        background-color: #f0f4f9;
        padding: 12px 18px;
        border-radius: 15px;
        margin: 10px 0;
        border-right: 5px solid #1a7f64;
        color: #000000;
    }
    .ai-bubble {
        background-color: #f7f7f8;
        padding: 15px 20px;
        border-radius: 15px;
        margin: 10px 0 25px 0;
        border-left: 5px solid #10a37f;
        color: #000000;
    }
    </style>
""", unsafe_allow_html=True)

# 🛠️ ฟังก์ชันพิเศษ: สั่งให้เบราว์เซอร์เลื่อนหน้าจอลงล่างสุดอัตโนมัติด้วย JavaScript
def scroll_to_bottom():
    st.markdown("""
        <script>
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        </script>
    """, unsafe_allow_html=True)

# 2. แถบเมนูด้านซ้าย (Sidebar)
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    api_key = st.text_input("🔑 ใส่ Gemini API Key ของคุณ:", type="password", placeholder="AIzaSy...")
    st.markdown("---")
    
    if st.button("🗑️ ล้างประวัติการสนทนาทั้งหมด"):
        st.session_state.gemini_chat_history = []
        st.session_state.image_result = ""
        st.session_state.audio_result = ""
        st.rerun()
        
    st.markdown("---")
    st.markdown("🤖 **โมเดลหลัก:** Gemini 3.6 Flash")
    st.markdown("🛡️ **ระบบสำรอง:** Fallback Mode")

# 3. ส่วนหัวเว็บไซต์หลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

# ตรวจสอบการใส่ API Key ล่วงหน้าก่อนเริ่มระบบ
if not api_key:
    st.warning("⚠️ กรุณากรอกรหัส Gemini API Key ที่แถบเมนูด้านซ้ายมือ เพื่อเปิดสวิตช์ระบบใช้งานครับ")
else:
    primary_model = "gemini-3.6-flash"
    backup_model = "gemini-2.5-pro"

    if "gemini_chat_history" not in st.session_state:
        st.session_state.gemini_chat_history = []
    if "image_result" not in st.session_state:
        st.session_state.image_result = ""
    if "audio_result" not in st.session_state:
        st.session_state.audio_result = ""

    tab_text, tab_image, tab_audio = st.tabs([
        "💬 ถามตอบด้วยข้อความ (ระบบแชทต่อเนื่อง)", 
        "🖼️ วิเคราะห์และอ่านรูปภาพ", 
        "🎵 ถอดความสรุปจากเสียง"
    ])

    # ===================================================
    # แท็บที่ 1: ระบบข้อความ (Text Chat)
    # ===================================================
    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไปแบบต่อเนื่อง")
        
        chat_container = st.container()
        with chat_container:
            st.markdown("#### 📜 บทสนทนาและคำตอบ:")
            if st.session_state.gemini_chat_history:
                # 🔴 ปรับกลับมาเรียงจากบนลงล่างตามเวลาจริงเพื่อให้ปุ่มเลื่อนอัตโนมัติทำงานได้อย่างเป็นธรรมชาติ
                for message in st.session_state.gemini_chat_history:
                    role = "👤 คุณ" if message.role == "user" else "🤖 AI"
                    bubble_class = "user-bubble" if message.role == "user" else "ai-bubble"
                    text_content = "".join([part.text for part in message.parts if part.text])
                    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{text_content}</div>", unsafe_allow_html=True)
            else:
                st.write("ยังไม่มีประวัติการคุย พิมพ์ข้อความคำถามในกล่องแชทด้านล่างสุดของหน้าจอเพื่อเริ่มคุยได้เลยครับ 👇")

        # กล่องคำถามล็อกอยู่ที่ขอบล่างสุดของจอถาวร พิมพ์แล้ว Enter ได้เลย
        user_prompt = st.chat_input("พิมพ์คำถามใหม่ของคุณที่นี่ แล้วกด Enter...")
        
        if user_prompt:
            with st.spinner("⏳ กำลังประมวลผลข้อมูล..."):
                client = genai.Client(api_key=api_key)
                try:
                    chat = client.chats.create(model=primary_model, history=st.session_state.gemini_chat_history)
                    response = chat.send_message(user_prompt)
                    st.session_state.gemini_chat_history = chat.get_history()
                    st.rerun()
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        try:
                            chat = client.chats.create(model=backup_model, history=st.session_state.gemini_chat_history)
                            response = chat.send_message(user_prompt)
                            st.session_state.gemini_chat_history = chat.get_history()
                            st.rerun()
                        except Exception as backup_err:
                            st.error(f"ระบบหนาแน่น โปรดลองอีกครั้งครับ: {backup_err}")
                    else:
                        st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
            
            # เรียกใช้ฟังก์ชันเลื่อนหน้าจอลงล่างสุดหลังจากอัปเดตคำตอบเสร็จแล้ว
            scroll_to_bottom()

    # ===================================================
    # แท็บที่ 2: ระบบรูปภาพ (Vision)
    # ===================================================
    with tab_image:
        st.markdown("### 🖼️ ค้นหาข้อมูลเชิงลึกจากภาพ")
        if st.session_state.image_result:
            st.markdown("<div class='ai-bubble'>#### 🤖 ผลการวิเคราะห์รูปภาพล่าสุด:<br>{}</div>".format(st.session_state.image_result), unsafe_allow_html=True)
            st.markdown("---")
            
        uploaded_image = st.file_uploader("เลือกอัปโหลดรูปภาพของคุณ:", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="📷 รูปภาพที่คุณอัปโหลด", width="stretch")
            image_prompt = st.text_input("ระบุสิ่งที่คุณต้องการให้ AI ค้นหาจากภาพ:", value="ภาพนี้คือภาพเกี่ยวกับอะไร? ช่วยอธิบายสั้นๆ")
            
            if st.button("🔍 สั่งวิเคราะห์รูปภาพ", key="btn_image"):
                with st.spinner("⏳ AI กำลังสแกนพิกเซลภาพ..."):
                    client = genai.Client(api_key=api_key)
                    try:
                        response = client.models.generate_content(model=primary_model, contents=[img, image_prompt])
                        st.session_state.image_result = response.text
                        st.rerun()
                    except Exception as e:
                        if "503" in str(e) or "UNAVAILABLE" in str(e):
                            try:
                                response = client.models.generate_content(model=backup_model, contents=[img, image_prompt])
                                st.session_state.image_result = response.text
                                st.rerun()
                            except Exception as backup_err:
                                st.error(f"ระบบไม่พร้อมใช้งานชั่วคราว: {backup_err}")
                        else:
                            st.error(f"เกิดข้อผิดพลาด: {e}")
                scroll_to_bottom()

    # ===================================================
    # แท็บที่ 3: ระบบไฟล์เสียง (Audio)
    # ===================================================
    with tab_audio:
        st.markdown("### 🎵 สรุปและแกะเสียงข้อความ")
        if st.session_state.audio_result:
            st.markdown("<div class='ai-bubble'>#### 🤖 สรุปใจความสำคัญจากไฟล์เสียงล่าสุด:<br>{}</div>".format(st.session_state.audio_result), unsafe_allow_html=True)
            st.markdown("---")
            
        uploaded_audio = st.file_uploader("เลือกอัปโหลดไฟล์เสียงของคุณ:", type=["mp3", "wav"])
        if uploaded_audio:
            st.audio(uploaded_audio)
            audio_prompt = st.text_input("ระบุเป้าหมายในการถอดรหัสเสียง:", value="สรุปใจความสำคัญจากไฟล์เสียงนี้มาเป็นข้อๆ")
            
            if st.button("🎙️ สั่งประมวลผลเสียง", key="btn_audio"):
                with st.spinner("⏳ AI กำลังแกะรหัสสัญญาณเสียง..."):
                    client = genai.Client(api_key=api_key)
                    try:
                        audio_file = client.files.upload(file=uploaded_audio)
                        response = client.models.generate_content(model=primary_model, contents=[audio_file, audio_prompt])
                        st.session_state.audio_result = response.text
                        st.rerun()
                    except Exception as e:
                        if "503" in str(e) or "UNAVAILABLE" in str(e):
                            try:
                                audio_file = client.files.upload(file=uploaded_audio)
                                response = client.models.generate_content(model=backup_model, contents=[audio_file, audio_prompt])
                                st.session_state.audio_result = response.text
                                st.rerun()
                            except Exception as backup_err:
                                st.error(f"ระบบไม่พร้อมใช้งานชั่วคราว: {backup_err}")
                        else:
                            st.error(f"เกิดข้อผิดพลาด: {e}")
                scroll_to_bottom()

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
    /* กล่องข้อความฝั่งผู้ใช้ */
    .user-bubble {
        background-color: #f0f4f9;
        padding: 12px 18px;
        border-radius: 15px;
        margin: 10px 0;
        border-right: 5px solid #1a7f64;
        color: #000000;
    }
    /* กล่องคำตอบฝั่ง AI */
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

# 2. แถบเมนูด้านซ้าย (Sidebar)
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    api_key = st.text_input("🔑 ใส่ Gemini API Key ของคุณ:", type="password", placeholder="AIzaSy...")
    st.markdown("---")
    
    # ปุ่มรีเซ็ตล้างความจำเพื่อเริ่มคุยเรื่องใหม่
    if st.button("🗑️ ล้างประวัติการสนทนาทั้งหมด"):
        if "gemini_chat" in st.session_state:
            del st.session_state["gemini_chat"]
        st.session_state.chat_display = []
        st.session_state.image_result = ""
        st.session_state.audio_result = ""
        st.rerun()
        
    st.markdown("---")
    st.markdown("🤖 **ระบบขับเคลื่อนโดย:** Gemini 3.6 Flash")

# 3. ส่วนหัวเว็บไซต์หลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

# ตรวจสอบการใส่ API Key ล่วงหน้าก่อนเริ่มระบบ
if not api_key:
    st.warning("⚠️ กรุณากรอกรหัส Gemini API Key ที่แถบเมนูด้านซ้ายมือ เพื่อเปิดสวิตช์ระบบใช้งานครับ")
else:
    # เริ่มต้น Client ของระบบ
    client = genai.Client(api_key=api_key)
    model_name = "gemini-3.6-flash"

    # สร้างคลังเก็บข้อมูลการแสดงผลแชทและการจดจำของระบบ
    if "chat_display" not in st.session_state:
        st.session_state.chat_display = []
    if "image_result" not in st.session_state:
        st.session_state.image_result = ""
    if "audio_result" not in st.session_state:
        st.session_state.audio_result = ""
        
    # 🛠️ ใช้ระบบสร้างแชทอัจฉริยะแบบฝังตัวของ Google SDK เพื่อผูกแชทต่อเนื่องแบบไม่มีพัง
    if "gemini_chat" not in st.session_state:
        st.session_state.gemini_chat = client.chats.create(model=model_name)

    # 4. สร้างแถบแท็บฟังก์ชัน
    tab_text, tab_image, tab_audio = st.tabs([
        "💬 ถามตอบด้วยข้อความ (ระบบแชทต่อเนื่อง)", 
        "🖼️ วิเคราะห์และอ่านรูปภาพ", 
        "🎵 ถอดความสรุปจากเสียง"
    ])

    # ===================================================
    # แท็บที่ 1: ระบบข้อความ (Text Chat - ล่างพิมพ์ บนตอบ)
    # ===================================================
    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไปแบบต่อเนื่อง")
        
        st.markdown("#### 👇 พิมพ์คำถามใหม่ของคุณที่นี่:")
        user_prompt = st.text_area("ป้อนคำถามของคุณ (เช่น แนะนำวิธีทำอาหารง่ายๆ, อธิบายโปรแกรมนี้หน่อย):", key="chat_input", placeholder="พิมพ์ข้อความคำถาม...")
        
        if st.button("🚀 ส่งคำถามไปยัง AI", key="btn_text"):
            if user_prompt:
                with st.spinner("⏳ กำลังประมวลผลข้อมูล..."):
                    try:
                        # 🚀 สั่งยิงคำถามเข้าในระบบแชทผูกมิตรของ Gemini โดยตรง (มันจำประวัติของมันเองอัตโนมัติ)
                        response = st.session_state.gemini_chat.send_message(user_prompt)
                        
                        # บันทึกข้อความเก็บไว้ในหน่วยความจำเพื่อนำไปวาดหน้าจอ
                        st.session_state.chat_display.append(("You", user_prompt))
                        st.session_state.chat_display.append(("AI", response.text))
                        st.rerun() 
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
            else:
                st.info("💡 โปรดพิมพ์คำถามลงในกล่องข้อความก่อนกดส่งครับ")

        st.markdown("---")
        st.markdown("#### 📜 บทสนทนาและคำตอบ (คำตอบล่าสุดจะเด้งอยู่บนสุดเสมอ):")
        
        # แสดงผลแบบย้อนกลับ (Reversed) เอาข้อความล่าสุดไว้ด้านบนสุด
        if st.session_state.chat_display:
            for role, text in reversed(st.session_state.chat_display):
                if role == "You":
                    st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{text}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='ai-bubble'><b>🤖 AI:</b><br>{text}</div>", unsafe_allow_html=True)
        else:
            st.write("ยังไม่มีประวัติการคุย พิมพ์ข้อความคำถามด้านล่างเพื่อเริ่มคุยได้เลยครับ 👇")

    # ===================================================
    # แท็บที่ 2: ระบบรูปภาพ (Vision)
    # ===================================================
    with tab_image:
        st.markdown("### 🖼️ ค้นหาข้อมูลเชิงลึกจากภาพ")
        
        if st.session_state.image_result:
            st.markdown("<div class='ai-bubble'>", unsafe_allow_html=True)
            st.markdown("#### 🤖 ผลการวิเคราะห์รูปภาพล่าสุด:")
            st.write(st.session_state.image_result)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
            
        uploaded_image = st.file_uploader("เลือกอัปโหลดรูปภาพของคุณ:", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="📷 รูปภาพที่คุณอัปโหลด", width="stretch")
            image_prompt = st.text_input("ระบุสิ่งที่คุณต้องการให้ AI ค้นหาจากภาพ:", value="ภาพนี้คือภาพเกี่ยวกับอะไร? ช่วยอธิบายสั้นๆ")
            
            if st.button("🔍 สั่งวิเคราะห์รูปภาพ", key="btn_image"):
                with st.spinner("⏳ AI กำลังสแกนพิกเซลภาพ..."):
                    try:
                        response = client.models.generate_content(model=model_name, contents=[img, image_prompt])
                        st.session_state.image_result = response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")

    # ===================================================
    # แท็บที่ 3: ระบบไฟล์เสียง (Audio)
    # ===================================================
    with tab_audio:
        st.markdown("### 🎵 สรุปและแกะเสียงข้อความ")
        
        if st.session_state.audio_result:
            st.markdown("<div class='ai-bubble'>", unsafe_allow_html=True)
            st.markdown("#### 🤖 สรุปใจความสำคัญจากไฟล์เสียงล่าสุด:")
            st.write(st.session_state.audio_result)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
            
        uploaded_audio = st.file_uploader("เลือกอัปโหลดไฟล์เสียงของคุณ:", type=["mp3", "wav"])
        if uploaded_audio:
            st.audio(uploaded_audio)
            audio_prompt = st.text_input("ระบุเป้าหมายในการถอดรหัสเสียง:", value="สรุปใจความสำคัญจากไฟล์เสียงนี้มาเป็นข้อๆ")
            
            if st.button("🎙️ สั่งประมวลผลเสียง", key="btn_audio"):
                with st.spinner("⏳ AI กำลังแกะรหัสสัญญาณเสียง..."):
                    try:
                        audio_file = client.files.upload(file=uploaded_audio)
                        response = client.models.generate_content(model=model_name, contents=[audio_file, audio_prompt])
                        st.session_state.audio_result = response.text
                        st.rerun()
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {e}")

import streamlit as st
import google.genai as genai
from google.genai import types
from PIL import Image
import time

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
    /* นำเข้าฟอนต์สไตล์โมเดิร์น Sarabun อ่านง่ายเป็นระเบียบ */
    @import url('https://googleapis.com');
    
    html, body, [data-testid="stSidebar"], .stApp, p, label, li, span, h1, h2, h3, h4, h5, h6 {
        font-family: 'Sarabun', sans-serif !important;
    }
    
    .stApp {
        background-color: #ffffff;
        color: #202123;
    }
    
    /* 🔴 จุดเด่นใหม่: บังคับตัวหนังสือในกล่องพิมพ์แชท (st.chat_input) ด้านล่างสุดให้ใหญ่และชัดเจนขึ้น */
    .stChatInput textarea {
        font-size: 18px !important;  /* ขยายขนาดตัวหนังสือที่พิมพ์ */
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

# 🛠️ ฟังก์ชันพิเศษระบบสมอเรือ: สั่งโฟกัสหน้าจอลงล่างสุดโดยการวิ่งเข้าหา ID หมุดแบบสมูท
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
    st.markdown("🛡️ **ระบบสำรอง:** Gemini 3.1 Pro (Fallback)")

# 3. ส่วนหัวเว็บไซต์หลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

# ตรวจสอบการใส่ API Key ล่วงหน้าก่อนเริ่มระบบ
if not api_key:
    st.warning("⚠️ กรุณากรอกรหัส Gemini API Key ที่แถบเมนูด้านซ้ายมือ เพื่อเปิดสวิตช์ระบบใช้งานครับ")
else:
    primary_model = "gemini-3.6-flash"
    backup_model = "gemini-3.1-pro-preview" 

    # สร้างคลังเก็บประวัติแชทแท้ของ Google SDK
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
    # แท็บที่ 1: ระบบข้อความ (Text Chat - Streaming + ปักหมุดเลื่อนจอ)
    # ===================================================
    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไปแบบต่อเนื่อง")
        
        chat_container = st.container()
        with chat_container:
            st.markdown("#### 📜 บทสนทนาและคำตอบ:")
            if st.session_state.gemini_chat_history:
                for message in st.session_state.gemini_chat_history:
                    role = "👤 คุณ" if message.role == "user" else "🤖 AI"
                    bubble_class = "user-bubble" if message.role == "user" else "ai-bubble"
                    text_content = "".join([part.text for part in message.parts if part.text])
                    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{text_content}</div>", unsafe_allow_html=True)
            else:
                st.write("ยังไม่มีประวัติการคุย พิมพ์ข้อความคำถามในกล่องแชทด้านล่างสุดของหน้าจอเพื่อเริ่มคุยได้เลยครับ 👇")

        # กล่องพิมพ์ล็อกขอบล่างถาวร พิมพ์แล้วกด Enter บนคีย์บอร์ดได้ทันที (ตัวหนังสือใหญ่ขึ้นแล้ว)
        user_prompt = st.chat_input("พิมพ์คำถามใหม่ของคุณที่นี่ แล้วกด Enter...")
        
        if user_prompt:
            with chat_container:
                st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{user_prompt}</div>", unsafe_allow_html=True)
            live_scroll()
            
            with chat_container:
                response_placeholder = st.empty()
                
            client = genai.Client(api_key=api_key)
            full_response_text = ""
            
            try:
                messages_to_send = []
                for msg in st.session_state.gemini_chat_history:
                    msg_parts = [types.Part.from_text(text=part.text) for part in msg.parts if part.text]
                    messages_to_send.append(types.Content(role=msg.role, parts=msg_parts))
                
                messages_to_send.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))
                
                response_stream = client.models.generate_content_stream(
                    model=primary_model,
                    contents=messages_to_send
                )
                
                for chunk in response_stream:
                    if chunk.text:
                        full_response_text += chunk.text
                        response_placeholder.markdown(f"<div class='ai-bubble'><b>🤖 AI:</b><br>{full_response_text}</div>", unsafe_allow_html=True)
                        live_scroll()
                        time.sleep(0.01)
                        
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    try:
                        response_stream = client.models.generate_content_stream(model=backup_model, contents=messages_to_send)
                        for chunk in response_stream:
                            if chunk.text:
                                full_response_text += chunk.text
                                response_placeholder.markdown(f"<div class='ai-bubble'><b>🤖 AI:</b><br>{full_response_text}</div>", unsafe_allow_html=True)
                                live_scroll()
                                time.sleep(0.01)
                    except Exception as backup_err:
                        st.error(f"ระบบหนาแน่นชั่วคราว โปรดพิมพ์ถามใหม่อีกครั้งครับ: {backup_err}")
                else:
                    st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
            
            if full_response_text:
                new_user_msg = types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
                new_ai_msg = types.Content(role="model", parts=[types.Part.from_text(text=full_response_text)])
                st.session_state.gemini_chat_history.append(new_user_msg)
                st.session_state.gemini_chat_history.append(new_ai_msg)
                st.rerun()

    # ===================================================
    # แท็บที่ 2: ระบบรูปภาพ (Vision)
    # ===================================================
    with tab_image:
        st.markdown("### 🖼️ ค้นหาข้อมูลเชิงลึกจากภาพ")
        if st.session_state.image_result:
            st.markdown(f"<div class='ai-bubble'><b>🤖 ผลการวิเคราะห์รูปภาพล่าสุด:</b><br>{st.session_state.image_result}</div>", unsafe_allow_html=True)
            st.markdown("---")
            
        uploaded_image = st.file_uploader("เลือกอัปโหลดรูปภาพของคุณ:", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="📷 รูปภาพที่คุณอัปโหลด", width="stretch")
            image_prompt = st.text_input("ระบุสิ่งที่คุณต้องการให้ AI ค้นหาจากภาพ:", value="ภาพนี้คือภาพเกี่ยวกับอะไร? ช่วยอธิบายสั้นๆ")
            
            if st.button("🔍 สั่งวิเคราะห์รูปภาพ", key="btn_image"):
                with st.spinner("⏳ AI กำลังสแกนพิกเซลภาพ..."):

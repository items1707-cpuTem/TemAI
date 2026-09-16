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

# 🛠️ ฟังก์ชันพิเศษ: บังคับให้หน้าต่างเบราว์เซอร์เด้งลงล่างสุดหน้าจอตลอดเวลาขณะ AI พิมพ์คำตอบ
def live_scroll():
    st.markdown("""
        <script>
            var pageContainer = window.parent.document.querySelector('.main');
            if (pageContainer) {
                pageContainer.scrollTop = pageContainer.scrollHeight;
            } else {
                window.scrollTo(0, document.body.scrollHeight);
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
    st.markdown("🛡️ **ระบบสำรอง:** Fallback Mode")

# 3. ส่วนหัวเว็บไซต์หลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

# ตรวจสอบการใส่ API Key ล่วงหน้าก่อนเริ่มระบบ
if not api_key:
    st.warning("⚠️ กรุณากรอกรหัส Gemini API Key ที่แถบเมน้านซ้ายมือ เพื่อเปิดสวิตช์ระบบใช้งานครับ")
else:
    primary_model = "gemini-3.6-flash"
    backup_model = "gemini-2.5-pro"

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
    # แท็บที่ 1: ระบบข้อความ (Text Chat - Streaming + Live Scroll)
    # ===================================================
    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไปแบบต่อเนื่อง")
        
        chat_container = st.container()
        with chat_container:
            st.markdown("#### 📜 บทสนทนาและคำตอบ:")
            if st.session_state.gemini_chat_history:
                # วนลูปอ่านประวัติเกรดการแสดงผลจากบนลงล่างตามเวลาจริง
                for message in st.session_state.gemini_chat_history:
                    role = "👤 คุณ" if message.role == "user" else "🤖 AI"
                    bubble_class = "user-bubble" if message.role == "user" else "ai-bubble"
                    text_content = "".join([part.text for part in message.parts if part.text])
                    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{text_content}</div>", unsafe_allow_html=True)
            else:
                st.write("ยังไม่มีประวัติการคุย พิมพ์ข้อความคำถามในกล่องแชทด้านล่างสุดของหน้าจอเพื่อเริ่มคุยได้เลยครับ 👇")

        # กล่องพิมพ์ล็อกขอบล่างถาวร พิมพ์แล้วกด Enter บนคีย์บอร์ดได้ทันที
        user_prompt = st.chat_input("พิมพ์คำถามใหม่ของคุณที่นี่ แล้วกด Enter...")
        
        if user_prompt:
            # 1. แสดงคำถามใหม่ของผู้ใช้ขึ้นหน้าต่างแชททันที
            with chat_container:
                st.markdown(f"<div class='user-bubble'><b>👤 คุณ:</b><br>{user_prompt}</div>", unsafe_allow_html=True)
            live_scroll()
            
            # 2. จองพื้นที่บนหน้าจอเตรียมพ่นคำตอบแบบขยับเลื่อนตามข้อความสด
            with chat_container:
                response_placeholder = st.empty()
                
            client = genai.Client(api_key=api_key)
            full_response_text = ""
            
            try:
                # แปลงประวัติเก่าให้เป็นคลาสออบเจกต์ที่สตรีมมิ่งยอมรับเพื่อผูกแชทต่อเนื่อง
                messages_to_send = []
                for msg in st.session_state.gemini_chat_history:
                    msg_parts = [types.Part.from_text(text=part.text) for part in msg.parts if part.text]
                    messages_to_send.append(types.Content(role=msg.role, parts=msg_parts))
                
                # แนบคำถามล่าสุดต่อท้ายลิสต์
                messages_to_send.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))
                
                # สั่งยิงข้อมูลแบบ Streaming
                response_stream = client.models.generate_content_stream(
                    model=primary_model,
                    contents=messages_to_send
                )
                
                # ลูปดึงตัวหนังสือที่ทยอยส่งออกมาทีละชิ้น และสั่งรีเฟรชดันขอบหน้าจอลงล่างทันที
                for chunk in response_stream:
                    if chunk.text:
                        full_response_text += chunk.text
                        response_placeholder.markdown(f"<div class='ai-bubble'><b>🤖 AI:</b><br>{full_response_text}</div>", unsafe_allow_html=True)
                        live_scroll() # 🔴 ดันแถบพิมพ์และหน้าจอขยับลงตามตัวหนังสือสดๆ
                        time.sleep(0.01)
                        
            except Exception as e:
                # ระบบสำรองกรณีกูเกิลคลาวด์แน่น (Error 503)
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
            
            # 3. บันทึกคำถามและคำตอบล่าสุดกลับเข้าสู่คลังฐานข้อมูลประวัติแท้เพื่อใช้คุยต่อเนื่องในรอบหน้า
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
                        st.error(f"เกิดข้อผิดพลาด: {e}")
                live_scroll()

    # ===================================================
    # แท็บที่ 3: ระบบไฟล์เสียง (Audio)
    # ===================================================
    with tab_audio:
        st.markdown("### 🎵 สรุปและแกะเสียงข้อความ")
        if st.session_state.audio_result:

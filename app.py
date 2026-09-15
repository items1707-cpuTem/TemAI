import streamlit as st
import google.genai as genai
from google.genai import types
from PIL import Image

# 🎨 1. ตั้งค่าหน้าเว็บและการตกแต่งสไตล์ ChatGPT โมเดิร์น
st.set_page_config(
    page_title="Gemini Multimodal AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ใช้ CSS เพื่อเปลี่ยนสีธีม ส่วนโค้ง และกรอบข้อความให้ดูคล้าย ChatGPT
st.markdown("""
    <style>
    .stApp {
        background-color: #212121;
        color: #eceecf;
    }
    .stButton>button {
        background-color: #10a37f !important; /* สีเขียวสัญลักษณ์ ChatGPT */
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1a7f64 !important;
        box-shadow: 0 4px 12px rgba(16,163,127,0.3);
    }
    .ai-response {
        background-color: #2f2f2f;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #10a37f;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 🔑 2. แถบเมนูด้านซ้าย (Sidebar) สำหรับจัดการสิทธิ์
with st.sidebar:
    st.markdown("### ⚙️ แผงควบคุมระบบ")
    api_key = st.text_input("🔑 ใส่ Gemini API Key ของคุณ:", type="password", placeholder="AIzaSy...")
    st.markdown("---")
    st.markdown("🤖 **ระบบขับเคลื่อนโดย:** Gemini 3.6 Flash")
    st.markdown("💡 *โมเดลรุ่นใหม่ล่าสุด รองรับไฟล์มัลติมีเดียความเร็วสูง*")

# 🏠 3. ส่วนหัวเว็บไซต์หลัก
st.markdown("# 🧠 สมองกล AI ส่วนตัวของคุณ")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ ดึงข้อมูลจาก**ข้อความ รูปภาพ และเสียง** ได้ในที่เดียวแบบฟรีๆ")
st.markdown("---")

# 🚨 ตรวจสอบการใส่ API Key ล่วงหน้าก่อนเริ่มระบบ
if not api_key:
    st.warning("⚠️ กรุณากรอกรหัส Gemini API Key ที่แถบเมนูด้านซ้ายมือ เพื่อเปิดสวิตช์ระบบใช้งานครับ")
else:
    # เริ่มต้นเชื่อมต่อกับเซิร์ฟเวอร์ Google AI
    client = genai.Client(api_key=api_key)
    model_name = "gemini-3.6-flash"

    # 📑 4. สร้างแถบแท็บฟังก์ชันสไตล์ไอคอนสวยงามใช้งานง่าย
    tab_text, tab_image, tab_audio = st.tabs([
        "💬 ถามตอบด้วยข้อความ", 
        "🖼️ วิเคราะห์และอ่านรูปภาพ", 
        "🎵 ถอดความสรุปจากเสียง"
    ])

    # ===================================================
    # แท็บที่ 1: ระบบข้อความ (Text)
    # ===================================================
    with tab_text:
        st.markdown("### 💬 พูดคุยถามข้อมูลทั่วไป")
        user_prompt = st.text_area("ป้อนข้อความคำถาม หรือเรื่องที่อยากรวบรวมข้อมูล:", placeholder="พิมพ์คำถามของคุณตรงนี้ เช่น แนะนำวิธีประหยัดไฟมา 3 ข้อ...")
        
        if st.button("🚀 ส่งคำถามไปยัง AI", key="btn_text"):
            if user_prompt:
                with st.spinner("⏳ กำลังค้นหาและประมวลผลข้อมูล..."):
                    try:
                        response = client.models.generate_content(model=model_name, contents=user_prompt)
                        st.markdown("<div class='ai-response'>", unsafe_allow_html=True)
                        st.markdown("#### 🤖 คำตอบจาก AI:")
                        st.write(response.text)
                        st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
            else:
                st.info("💡 โปรดพิมพ์คำถามลงในกล่องข้อความก่อนกดส่งครับ")

    # ===================================================
    # แท็บที่ 2: ระบบรูปภาพ (Vision)
    # ===================================================
    with tab_image:
        st.markdown("### 🖼️ ค้นหาข้อมูลเชิงลึกจากภาพ")
        uploaded_image = st.file_uploader("เลือกอัปโหลดรูปภาพของคุณ (รองรับ .jpg, .jpeg, .png):", type=["jpg", "jpeg", "png"])
        
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="📷 รูปภาพที่คุณอัปโหลด", width="stretch")
            
            image_prompt = st.text_input("ระบุสิ่งที่คุณต้องการให้ AI ค้นหาหรือแกะข้อมูลจากภาพนี้:", value="ภาพนี้คือภาพเกี่ยวกับอะไร? อธิบายรายละเอียดของสิ่งของและองค์ประกอบในภาพมาสั้นๆ")
            
            if st.button("🔍 สั่งวิเคราะห์รูปภาพ", key="btn_image"):
                with st.spinner("⏳ AI กำลังสแกนและตรวจสอบพิกเซลภาพ..."):
                    try:
                        response = client.models.generate_content(model=model_name, contents=[img, image_prompt])
                        st.markdown("<div class='ai-response'>", unsafe_allow_html=True)
                        st.markdown("#### 🤖 ผลการวิเคราะห์รูปภาพ:")
                        st.write(response.text)
                        st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดทางเทคนิค: {e}")

    # ===================================================
    # แท็บที่ 3: ระบบไฟล์เสียง (Audio)
    # ===================================================
    with tab_audio:
        st.markdown("### 🎵 สรุปและแกะเสียงข้อความ")
        uploaded_audio = st.file_uploader("เลือกอัปโหลดไฟล์เสียงของคุณ (รองรับ .mp3, .wav):", type=["mp3", "wav"])
        
        if uploaded_audio:
            st.audio(uploaded_audio)
            audio_prompt = st.text_input("ระบุเป้าหมายในการถอดรหัสเสียง:", value="สรุปใจความสำคัญจากไฟล์เสียงนี้อย่างละเอียด แยกมาเป็นข้อๆ พร้อมถอดรหัสคำพูดข้อความออกมาถ้ามี")
            
            if st.button("🎙️ สั่งประมวลผลเสียง", key="btn_audio"):
                with st.spinner("⏳ AI กำลังฟังและถอดรหัสคลื่นความถี่เสียง..."):
                    try:
                        # อัปโหลดไฟล์เสียงไปยัง Cloud File API ของ Google
                        audio_file = client.files.upload(file=uploaded_audio)
                        response = client.models.generate_content(model=model_name, contents=[audio_file, audio_prompt])
                        st.markdown("<div class='ai-response'>", unsafe_allow_html=True)
                        st.markdown("#### 🤖 สรุปใจความสำคัญจากไฟล์เสียง:")
                        st.write(response.text)
                        st.markdown("</div>", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์เสียง: {e}")

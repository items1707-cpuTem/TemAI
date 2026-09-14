import streamlit as st
import google.genai as genai
from google.genai import types
from PIL import Image  # 👈 เพิ่มบรรทัดนี้เข้าไปเพื่อแก้บั๊ก NameError ครับ
import io

# 1. ตั้งค่าหน้าเว็บหน้าตาแอปพลิเคชัน
st.set_page_config(
    page_title="Multimodal AI Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Multimodal AI Assistant")
st.write("แอปพลิเคชันหาข้อมูลอัจฉริยะ รองรับ **ข้อความ, รูปภาพ และเสียง** พัฒนาด้วย Gemini 3.6-flash")

# 2. ฟังก์ชันตรวจสอบและดึงโครงสร้าง Client จาก API Key
def get_gemini_client(api_key):
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อระบบ: {str(e)}")
        return None

# 3. จัดเตรียมกล่องสำหรับระบุ API Key (ให้ผู้ใช้ระบุเองเพื่อความปลอดภัย หรือดึงจาก Secrets ได้)
# เพื่อความสะดวกในการเทสจะเปิดช่องป้อนข้อมูลหน้าเว็บไว้
api_key_input = st.sidebar.text_input("🔑 ใส่ Gemini API Key ของคุณ:", type="password")

if not api_key_input:
    st.info("💡 กรุณาใส่ Gemini API Key ที่แถบเมนูด้านซ้ายเพื่อเริ่มต้นใช้งาน (สมัครฟรีที่ Google AI Studio)")
else:
    client = genai.Client(api_key=api_key_input)
    model_name = "gemini-3.6-flash"
    
    # สร้างเมนูแท็บให้เลือกใช้งานตามรูปแบบข้อมูล
    tab1, tab2, tab3 = st.tabs(["📝 ค้นหาด้วยข้อความ", "📸 ค้นหาด้วยรูปภาพ", "🎵 ค้นหาด้วยไฟล์เสียง"])
    
    # ---------------------------------------------------
    # แท็บที่ 1: ข้อความอย่างเดียว
    # ---------------------------------------------------
    with tab1:
        st.subheader("ถาม-ตอบ ด้วยข้อความทั่วไป")
        text_prompt = st.text_area("ป้อนคำถามหรือหัวข้อที่ต้องการค้นหาข้อมูล:", placeholder="เช่น แนะนำวิธีประหยัดไฟในบ้านมา 3 ข้อ...")
        if st.button("🚀 ส่งคำถาม (ข้อความ)", key="btn_text"):
            if text_prompt:
                with st.spinner("AI กำลังประมวลผลข้อมูล..."):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=text_prompt,
                        )
                        st.success("🤖 คำตอบจาก AI:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {str(e)}")
            else:
                st.warning("กรุณากรอกข้อความก่อนกดส่งครับ")

    # ---------------------------------------------------
    # แท็บที่ 2: รูปภาพ + ข้อความ
    # ---------------------------------------------------
    with tab2:
        st.subheader("วิเคราะห์ข้อมูลจากรูปภาพ")
        uploaded_image = st.file_uploader("อัปโหลดไฟล์ภาพ (PNG, JPG, JPEG):", type=["png", "jpg", "jpeg"])
        image_prompt = st.text_input("คุณต้องการสั่งให้ AI ทำอะไรกับภาพนี้?", value="อธิบายสิ่งที่คุณเห็นในภาพนี้อย่างละเอียด")
        
        if uploaded_image is not None:
            # แสดงรูปภาพที่อัปโหลดบนหน้าเว็บ
            img = Image.open(uploaded_image)
            st.image(img, caption="รูปภาพที่อัปโหลดสำเร็จ", width="stretch")

            
            if st.button("📸 วิเคราะห์รูปภาพ", key="btn_img"):
                with st.spinner("AI กำลังเพ่งมองและวิเคราะห์รูปภาพสักครู่..."):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[img, image_prompt],
                        )
                        st.success("🤖 ผลการวิเคราะห์รูปภาพ:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {str(e)}")

    # ---------------------------------------------------
    # แท็บที่ 3: ไฟล์เสียง + ข้อความ
    # ---------------------------------------------------
    with tab3:
        st.subheader("ถอดความหรือถอดรหัสจากเสียง")
        uploaded_audio = st.file_uploader("อัปโหลดไฟล์เสียง (MP3, WAV):", type=["mp3", "wav"])
        audio_prompt = st.text_input("คุณต้องการให้ AI จัดการอย่างไรกับเสียงนี้?", value="สรุปใจความสำคัญจากไฟล์เสียงนี้ และถอดสคริปต์ข้อความออกมา")
        
        if uploaded_audio is not None:
            st.audio(uploaded_audio)
            
            if st.button("🎵 ประมวลผลไฟล์เสียง", key="btn_audio"):
                with st.spinner("AI กำลังฟังและสรุปเนื้อหาจากเสียง..."):
                    try:
                        # สร้างไบนารีข้อมูลชั่วคราวเพื่อส่งผ่าน API โดยไม่ต้องบันทึกลงดิสก์ระบบตรงๆ
                        audio_bytes = uploaded_audio.read()
                        
                        # กำหนดค่า MimeType ให้สอดคล้องกับไฟล์
                        mime_type = "audio/mp3" if uploaded_audio.name.endswith("mp3") else "audio/wav"
                        
                        audio_part = types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type=mime_type,
                        )
                        
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[audio_part, audio_prompt],
                        )
                        st.success("🤖 ผลการประมวลผลไฟล์เสียง:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาด: {str(e)}")

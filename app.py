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
    /* เผื่อพื้นที่ขวาไว้ให้ไอคอนรูปภาพ + ไมค์ ลอยซ้อนอยู่ข้างในกล่องพอดี ไม่ทับตัวหนังสือ */
    div[data-testid="stChatInput"] textarea {
        font-size: 16px !important;  
        color: #000000 !important;
        line-height: 1.6 !important; 
        font-family: 'Sarabun', sans-serif !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        padding-right: 76px !important;
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
    
    /* ==========================================================
       ฝังไอคอนรูปภาพ + ไมค์ ไว้ "ข้างใน" กล่องพิมพ์ข้อความจริง ๆ
       โดยวางซ้อน (overlay) ทับขอบขวาของ st.chat_input ด้วย position
       ========================================================== */

    /* แถวที่รวม chat_input + ปุ่มรูปภาพ + ปุ่มไมค์ ต้องเป็นจุดอ้างอิงตำแหน่ง */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stChatInput"]) {
        position: relative !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stChatInput"]) > div[data-testid="stColumn"]:nth-of-type(1) {
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* คอลัมน์ไอคอนรูปภาพ (คอลัมน์ที่ 2) และไอคอนไมค์ (คอลัมน์ที่ 3)
       ยกไปลอยซ้อนทับอยู่ในขอบขวาของกล่องแชทเดียวกัน ไม่กินพื้นที่แถวแยกอีกต่อไป */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stChatInput"]) > div[data-testid="stColumn"]:nth-of-type(2),
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stChatInput"]) > div[data-testid="stColumn"]:nth-of-type(3) {
        position: absolute !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        width: auto !important;
        min-width: 0 !important;
        flex: none !important;
        z-index: 999 !important;
        pointer-events: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stChatInput"]) > div[data-testid="stColumn"]:nth-of-type(2) {
        right: 38px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stChatInput"]) > div[data-testid="stColumn"]:nth-of-type(3) {
        right: 4px !important;
    }
    div[data-testid="stFileUploader"], div[data-testid="stAudioInput"] {
        width: 34px !important;
        min-width: 34px !important;
        padding: 0 !important;
        margin: 0 !important;
        pointer-events: auto !important;
    }
    div[data-testid="stFileUploader"] section, div[data-testid="stAudioInput"] section {
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        min-height: 0 !important;
    }

    /* ปุ่มไอคอนทั้งสอง: วงกลมโปร่งใส ไม่มีกรอบ */
    div[data-testid="stFileUploader"] button, div[data-testid="stAudioInput"] button {
        position: relative !important;
        padding: 0 !important;
        margin: 0 !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        cursor: pointer;
        display: flex !important;
        align-items: center;
        justify-content: center;
        box-shadow: none !important;
    }
    div[data-testid="stFileUploader"] button:hover, div[data-testid="stAudioInput"] button:hover {
        background-color: #eaecef !important;
    }

    /* ปุ่มรูปภาพเท่านั้น: เดิมมีตัวหนังสือ "Browse files" ซ่อนอยู่ข้างใน ต้องซ่อนแล้วแปะอิโมจิรูปภาพแทน */
    div[data-testid="stFileUploader"] button {
        overflow: hidden !important;
    }
    div[data-testid="stFileUploader"] button > * {
        visibility: hidden !important;
        opacity: 0 !important;
    }
    div[data-testid="stFileUploader"] button::after {
        content: "🖼️";
        visibility: visible !important;
        opacity: 1 !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        font-size: 18px !important;
        line-height: 1 !important;
    }

    /* ปุ่มไมค์: ใช้ไอคอนไมค์เดิมของ Streamlit ตามธรรมชาติ (ไม่มีตัวหนังสือซ้อนอยู่แล้ว)
       ไม่แตะต้อง/ไม่ซ่อนอะไรข้างในปุ่ม เพื่อให้กดอัดเสียง/หยุดอัดใช้งานได้ปกติ 100% */

    /* บังคับซ่อนเฉพาะข้อความคำแนะนำ/ป้ายกำกับของ "ปุ่มรูปภาพ" ที่รกรุงรัง (ไม่ยุ่งกับสถานะการอัดเสียง) */
    div[data-testid="stFileUploaderDropzone"] small,
    div[data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stFileUploader"] label,
    div[data-testid="stAudioInput"] label,
    div[data-testid="stFileUploaderDropzone"] svg {
        display: none !important;
    }
    /* กล่องแสดงชื่อไฟล์ที่อัปโหลดแล้ว ให้ลอยเป็นการ์ดเล็ก ๆ เหนือกล่องแชท ไม่บังปุ่มไอคอน */
    div[data-testid="stFileUploaderFileWidget"] {
        position: fixed;
        bottom: 88px;
        right: 4.8rem;
        background: #ffffff;
        padding: 6px 10px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        max-width: 220px;
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
st.markdown("# 🧠 ฉันคือผู้ช่วยของคุน")
st.markdown("ค้นหาข้อมูล เจาะลึกความรู้ หรือแนบไฟล์รูปภาพ/อัดเสียงพูดโต้ตอบได้ทุกภาษาในแถบขอบล่างจุดเดียว")
st.markdown("---")

if not api_key:
    st.error("⚠️ ไม่พบรหัสผ่านระบบหลังบ้าน! กรุณาเพิ่มข้อมูล GEMINI_API_KEY ในหน้า Secrets ของเว็บ Streamlit Cloud ก่อนใช้งานครับ")
else:
    active_model = "gemini-3.6-flash"
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

    # 🔴 ไอคอนรูปภาพและไมค์ลอยซ้อนอยู่ข้างในกล่องพิมพ์ข้อความเดียวกัน (ควบคุมตำแหน่งด้วย CSS ด้านบน)
    col_input, col_img, col_voice = st.columns([5.5, 0.6, 0.6])

    with col_input:
        # กล่องพิมพ์แชทมาตรฐานโผล่กลับมาแสดงผลชัดเจน 100% พิมพ์คล่องตัว และกด Enter บนคีย์บอร์ดสั่งส่งได้ทันที!
        user_prompt = st.chat_input("พิมพ์คำถามของคุณที่นี่ แล้วกด Enter เพื่อส่ง...")

    with col_img:
        uploaded_image = st.file_uploader("🖼️", type=["jpg", "jpeg", "png"], key="img_box", label_visibility="collapsed")

    with col_voice:
        voice_recorder_data = st.audio_input("🎙️", key="voice_box", label_visibility="collapsed")

    # 🕒 สคริปต์คอยตรวจจับว่ากำลังอัดเสียงอยู่หรือไม่ แล้วโชว์จำนวนวินาทีที่อัดไปแล้ว
    # เป็นข้อความ placeholder ในช่องพิมพ์ข้อความ (เมื่ออัดเสร็จ/หยุด จะคืนข้อความเดิมอัตโนมัติ)
    st.markdown("""
        <script>
        (function() {
            if (window.__micTimerInitialized) { return; }
            window.__micTimerInitialized = true;

            function getDoc() { return window.parent.document; }

            var recordStartTime = null;
            var originalPlaceholder = null;
            var wasRecording = false;

            function isRecording(doc) {
                var el = doc.querySelector(
                    'div[data-testid="stAudioInputWaveSurfer"], div[data-testid="stAudioInputRecordState"]'
                );
                if (!el) return false;
                var rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }

            function tick() {
                var doc = getDoc();
                var textarea = doc.querySelector('div[data-testid="stChatInput"] textarea');
                if (!textarea) return;

                var recording = isRecording(doc);

                if (recording && !wasRecording) {
                    // เพิ่งเริ่มอัดเสียง: จำข้อความเดิมไว้ก่อน แล้วเริ่มจับเวลา
                    recordStartTime = Date.now();
                    if (originalPlaceholder === null) {
                        originalPlaceholder = textarea.getAttribute('placeholder') || '';
                    }
                }

                if (recording) {
                    var elapsedSec = Math.floor((Date.now() - recordStartTime) / 1000);
                    var mm = Math.floor(elapsedSec / 60);
                    var ss = String(elapsedSec % 60).padStart(2, '0');
                    textarea.setAttribute('placeholder', '🎙️ กำลังอัดเสียง ' + mm + ':' + ss + ' ...');
                } else if (wasRecording) {
                    // อัดเสียงเสร็จ/ยกเลิก: คืนข้อความเดิมกลับไป
                    if (originalPlaceholder !== null) {
                        textarea.setAttribute('placeholder', originalPlaceholder);
                    }
                }

                wasRecording = recording;
            }

            setInterval(tick, 400);
        })();
        </script>
    """, unsafe_allow_html=True)

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
            client = genai.Client(api_key=api_key)
            ai_text = None
            max_retries = 4
            last_error = None

            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=active_model,
                        contents=content_parts if content_parts else [full_context_string],
                    )
                    ai_text = response.text
                    break  # สำเร็จแล้ว ออกจากลูปทันที
                except Exception as e:
                    last_error = e
                    error_text = str(e)
                    # เช็กว่าเป็น error ชั่วคราว (503 โมเดลคนใช้เยอะ / 429 คำขอถี่เกินไป) หรือไม่
                    is_temporary = ("503" in error_text) or ("UNAVAILABLE" in error_text) or ("429" in error_text) or ("RESOURCE_EXHAUSTED" in error_text)

                    if is_temporary and attempt < max_retries - 1:
                        wait_seconds = 2 ** attempt  # รอเพิ่มขึ้นเรื่อย ๆ: 1, 2, 4, 8 วินาที
                        st.toast(f"⏳ เซิร์ฟเวอร์มีผู้ใช้งานเยอะ กำลังลองใหม่อีกครั้ง ({attempt + 1}/{max_retries - 1})...")
                        time.sleep(wait_seconds)
                        continue
                    else:
                        break

            if ai_text is None:
                error_text = str(last_error)
                if ("503" in error_text) or ("UNAVAILABLE" in error_text):
                    ai_text = "⚠️ ขออภัยครับ ตอนนี้เซิร์ฟเวอร์ AI มีผู้ใช้งานหนาแน่นมาก ลองพิมพ์คำถามส่งใหม่อีกครั้งในอีกสักครู่นะครับ"
                elif ("429" in error_text) or ("RESOURCE_EXHAUSTED" in error_text):
                    ai_text = "⚠️ ส่งคำขอถี่เกินไป กรุณารอสักครู่แล้วลองใหม่อีกครั้งครับ"
                else:
                    ai_text = f"⚠️ เกิดข้อผิดพลาด: {last_error}"

        # เพิ่มคำตอบ AI เข้าประวัติแชท
        current_chat_history.append({"role": "assistant", "text": ai_text})

        # บันทึกประวัติทั้งหมดลงดิสก์
        save_all_chats_to_disk(st.session_state.all_chats)

        live_scroll()
        st.rerun()

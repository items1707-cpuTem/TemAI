import streamlit as st
import streamlit.components.v1 as components
import google.genai as genai
from google.genai import types
from PIL import Image
import time
import os
import pickle
import io
import re
import html
from datetime import datetime, timezone, timedelta

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
    /* เผื่อพื้นที่ซ้ายไว้ให้ปุ่ม "+" แนบไฟล์ ลอยซ้อนอยู่ข้างในกล่องพอดี ไม่ทับตัวหนังสือ */
    div[data-testid="stChatInput"] textarea {
        font-size: 16px !important;  
        color: #000000 !important;
        line-height: 1.6 !important; 
        font-family: 'Sarabun', sans-serif !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        padding-left: 44px !important;
        padding-right: 104px !important;
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
       ปุ่ม "+" แนบไฟล์ ถูกย้ายด้วยสคริปต์ (ด้านล่าง) ให้เข้าไปอยู่
       "ข้างใน" กรอบกล่องพิมพ์ข้อความจริง ๆ (ไม่ใช่แค่ลอยซ้อนด้วย CSS เฉย ๆ)
       กดแล้วเด้งเมนูเล็ก ๆ ให้เลือก แนบไฟล์ / แนบรูปภาพ / อัดเสียง
       ========================================================== */

    /* คอลัมน์เดิมที่เคยเป็นที่อยู่ของปุ่ม + ไม่ต้องกินพื้นที่แถวอีกต่อไป เพราะปุ่มถูกย้ายเข้ากรอบแชทแล้ว */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] > .chat-input-row-marker) {
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] > .chat-input-row-marker) > div[data-testid="stColumn"]:nth-of-type(1) {
        display: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="stColumn"] > .chat-input-row-marker) > div[data-testid="stColumn"]:nth-of-type(2) {
        width: 100% !important;
        flex: 1 1 auto !important;
    }

    /* กล่องพิมพ์ข้อความ: ให้เป็นจุดอ้างอิงตำแหน่ง เพื่อให้ปุ่ม + ที่ถูกย้ายเข้ามาเกาะอยู่ข้างในขอบซ้ายพอดี */
    div[data-testid="stChatInput"] {
        position: relative !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stPopover"] {
        width: 36px !important;
        height: 36px !important;
        min-width: 0 !important;
        pointer-events: none !important;
        position: absolute !important;
        left: 6px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 999 !important;
    }

    /* ปุ่มไมค์อัดเสียง: ถูกย้ายมาอยู่ข้างในกรอบช่องพิมพ์ข้อความ ทางขวาสุด (ติดกับปุ่มส่ง) แสดงเป็นไอคอนไมค์อย่างเดียว */
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] {
        position: absolute !important;
        right: 50px !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        width: 40px !important;
        min-width: 40px !important;
        height: 40px !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        z-index: 999 !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] * {
        background-color: transparent !important;
        border-color: transparent !important;
        box-shadow: none !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] > div {
        padding: 0 !important;
        margin: 0 !important;
        height: 40px !important;
        min-height: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] button {
        width: 40px !important;
        height: 40px !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex: none !important;
        cursor: pointer !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] button:hover {
        background-color: #e4e7ec !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] button svg {
        width: 26px !important;
        height: 26px !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] button [data-testid="stIconMaterial"] {
        font-size: 26px !important;
        width: 26px !important;
        height: 26px !important;
    }
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] label,
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] small {
        display: none !important;
    }

    /* กล่องที่ย้ายเข้ามาในช่องพิมพ์ต้องไม่บังช่องพิมพ์: ให้คลิกทะลุได้ ยกเว้นตัวปุ่มเอง */
    div[data-testid="stChatInput"] div[data-testid="stPopover"] button,
    div[data-testid="stChatInput"] div[data-testid="stAudioInput"] button {
        pointer-events: auto !important;
    }
    div[data-testid="stChatInput"] textarea {
        cursor: text !important;
    }

    /* ปุ่ม "+" วงกลมโปร่งใส ไม่มีกรอบ */
    div[data-testid="stPopover"] > div > button {
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
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #3c3f44 !important;
    }
    div[data-testid="stPopover"] > div > button:hover {
        background-color: #eaecef !important;
    }
    /* ซ่อนลูกศร/คำว่า "expand more" ที่ Streamlit แปะมากับปุ่มเปิดเมนู (เป็นตัวหนังสือชื่อไอคอนที่หลุดออกมา) */
    div[data-testid="stPopover"] button svg,
    div[data-testid="stPopover"] button [data-testid="stIconMaterial"],
    div[data-testid="stPopover"] button span[translate="no"] {
        display: none !important;
    }

    /* แผงเมนูที่เด้งขึ้นมาหลังกดปุ่ม +: เหลือแต่ไอคอนล้วน ๆ ไม่มีตัวหนังสือภาษาไหนเลย */
    div[data-testid="stPopoverBody"] {
        padding: 6px !important;
        min-width: 0 !important;
        width: auto !important;
    }
    /* ซ่อนข้อความทั้งหมดในเมนู: คำอธิบายลากวาง, ป้ายกำกับ, ตัวเลขเวลา, ชื่อไอคอนที่หลุดมาเป็นตัวหนังสือ */
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploaderDropzoneInstructions"],
    div[data-testid="stPopoverBody"] label,
    div[data-testid="stPopoverBody"] small,
    div[data-testid="stPopoverBody"] [data-testid="stIconMaterial"],
    div[data-testid="stPopoverBody"] svg {
        display: none !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] section,
    div[data-testid="stPopoverBody"] div[data-testid="stAudioInput"] section {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        min-height: 0 !important;
    }
    /* ปุ่มอัพโหลดในเมนู (เดิมเป็นปุ่มขอบขาวเขียนว่า "Upload"): ซ่อนตัวหนังสือ/ขอบเดิมทั้งหมด
       แล้วสร้างเป็นแถวเมนูสวย ๆ = ไอคอนเส้นบาง + ข้อความภาษาไทย (ไอคอน/ข้อความใส่ด้วย CSS ตามลำดับปุ่ม) */
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] > *:not(:has(button)):not(button):not([data-testid="stFileUploaderFile"]) {
        display: none !important;
    }
    div[data-testid="stPopoverBody"] {
        min-width: 190px !important;
    }
    /* ระยะห่างระหว่างแถวในเมนูให้แคบและเท่ากัน ไม่ห่างเกินไป */
    div[data-testid="stPopoverBody"] div[data-testid="stVerticalBlock"] {
        gap: 2px !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stElementContainer"],
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] {
        margin: 0 !important;
        padding: 0 !important;
        min-height: 0 !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] button:not([data-testid="stFileUploaderDeleteBtn"] button) {
        width: 100% !important;
        height: 40px !important;
        min-height: 0 !important;
        padding: 0 14px !important;
        margin: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 10px !important;
        font-size: 0 !important;
        color: transparent !important;
        cursor: pointer !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] button:not([data-testid="stFileUploaderDeleteBtn"] button):hover {
        background-color: #f0f4f9 !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] button:not([data-testid="stFileUploaderDeleteBtn"] button) * {
        display: none !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] button:not([data-testid="stFileUploaderDeleteBtn"] button)::before {
        content: "" !important;
        display: block !important;
        flex: none !important;
        width: 20px !important;
        height: 20px !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
        background-size: contain !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"] button:not([data-testid="stFileUploaderDeleteBtn"] button)::after {
        display: block !important;
        font-family: 'Sarabun', sans-serif !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        line-height: 1 !important;
        color: #1f2937 !important;
        white-space: nowrap !important;
        letter-spacing: 0.01em !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"][data-attach="file"] button:not([data-testid="stFileUploaderDeleteBtn"] button)::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23374151' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48'/></svg>") !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"][data-attach="file"] button:not([data-testid="stFileUploaderDeleteBtn"] button)::after {
        content: "อัพโหลดไฟล์" !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"][data-attach="image"] button:not([data-testid="stFileUploaderDeleteBtn"] button)::before {
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23374151' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='18' height='18' rx='3'/><circle cx='8.5' cy='8.5' r='1.5'/><path d='M21 15l-5-5L5 21'/></svg>") !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"][data-attach="image"] button:not([data-testid="stFileUploaderDeleteBtn"] button)::after {
        content: "อัพโหลดรูปภาพ" !important;
    }

    /* ไฟล์ที่แนบแล้ว: ซ่อนชื่อ/ขนาดไฟล์ทั้งหมด แสดงแค่เครื่องหมายถูก ✅ และปุ่ม ✕ สำหรับลบ */
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploaderFile"] {
        font-size: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        padding: 2px 0 !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploaderFile"] > *:not(button):not(:has(button)) {
        display: none !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploaderFile"]::before {
        content: "✅";
        font-size: 18px !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploaderFile"] button {
        display: inline-flex !important;
        width: 24px !important;
        height: 24px !important;
        min-height: 0 !important;
        padding: 0 !important;
        font-size: 14px !important;
        color: #6b7280 !important;
        background: transparent !important;
        border: none !important;
    }
    div[data-testid="stPopoverBody"] div[data-testid="stFileUploaderFile"] button::after {
        content: "✕";
    }
    /* ==========================================================
       แถบซ้าย: ปุ่มเริ่มใหม่ + ประวัติการค้นหา
       ไม่มีกล่อง/กรอบ ไม่มีไอคอนกวนใจ ตัวหนังสือเล็กกระชับ อยู่ติดกัน
       ========================================================== */
    div[data-testid="stHorizontalBlock"]:has(.history-panel-marker) > div[data-testid="stColumn"]:nth-of-type(1) button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 5px 6px !important;
        margin: 0 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
        min-height: 0 !important;
        height: auto !important;
        width: 100% !important;
        color: #3c3f44 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.history-panel-marker) button p {
        font-size: 15px !important;
        text-align: left !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.history-panel-marker) button:hover {
        background-color: #f0f4f9 !important;
        border-radius: 6px !important;
    }
    /* ให้ปุ่มแต่ละรายการอยู่ติดกันหน่อย ไม่เว้นช่องว่างห่างแบบเดิม */
    div[data-testid="stHorizontalBlock"]:has(.history-panel-marker) div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    .history-header {
        font-size: 12px !important;
        font-weight: 600;
        color: #9aa0a8;
        letter-spacing: 0.02em;
        margin: 2px 0 8px 4px;
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

# 🕒 บอกโมเดลว่า "ตอนนี้" คือวันเวลาไหน (โมเดลไม่รู้วันที่จริงเอง จึงเคยตอบวันที่ผิด)
THAI_DAYS = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
THAI_MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
               "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]

def build_system_instruction():
    now = datetime.now(timezone(timedelta(hours=7)))  # เวลาประเทศไทย
    date_text = (
        f"วัน{THAI_DAYS[now.weekday()]}ที่ {now.day} {THAI_MONTHS[now.month - 1]} "
        f"พ.ศ. {now.year + 543} (ค.ศ. {now.year}) เวลา {now.strftime('%H:%M')} น. (เวลาประเทศไทย)"
    )
    return (
        "คุณเป็นผู้ช่วย AI ที่ฉลาด รอบคอบ และเป็นมิตร\n"
        f"ข้อมูลปัจจุบัน: ตอนนี้คือ{date_text} ใช้ข้อมูลนี้เป็นความจริงเสมอเมื่อถูกถามเรื่องวัน เวลา วันที่ หรือปี "
        "ห้ามเดาวันที่เอง\n"
        "หลักการตอบ:\n"
        "1) ตอบให้ตรงกับสิ่งที่ผู้ใช้ถาม ตรงประเด็นก่อน แล้วค่อยเสริมรายละเอียดที่จำเป็น\n"
        "2) ตอบเป็นภาษาเดียวกับที่ผู้ใช้ใช้ถาม (ถ้าถามไทยให้ตอบไทย)\n"
        "3) ใช้บทสนทนาก่อนหน้าเป็นบริบทต่อเนื่อง ถ้าผู้ใช้ถามต่อหรืออ้างถึงสิ่งที่คุยกันไปแล้ว\n"
        "4) ถ้าข้อมูลเปลี่ยนตามเวลา (ข่าว ราคา ผลกีฬา ฯลฯ) ให้ค้นหาข้อมูลล่าสุดก่อนตอบ\n"
        "5) ถ้าไม่แน่ใจหรือไม่ทราบ ให้บอกตรง ๆ อย่าแต่งข้อมูล\n"
        "6) ถ้าคำถามกำกวมจริง ๆ ให้ถามกลับสั้น ๆ หนึ่งข้อ\n"
        "7) กระชับ ชัดเจน อ่านง่าย"
    )

def format_bubble_text(text):
    """แปลงข้อความ (มาร์กดาวน์แบบง่าย) เป็น HTML สำหรับแสดงในกล่องแชท เช่น **ตัวหนา** ไม่ให้โชว์เป็นดอกจัน"""
    t = html.escape(text)
    t = re.sub(r"^\s*#{1,6}\s*(.+)$", r"<b>\1</b>", t, flags=re.M)
    t = re.sub(r"^\s*[\*\-]\s+", "• ", t, flags=re.M)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"(?<![\*\w])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", t)
    t = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", t)
    return t.replace("\n", "<br>")

def build_contents(history_before, content_parts):
    """ส่งประวัติการคุยก่อนหน้าไปด้วย (เดิมส่งแค่ข้อความล่าสุด โมเดลเลยไม่จำบริบทและตอบไม่ตรง)"""
    contents = []
    for msg in history_before[-20:]:
        text = msg.get("text", "")
        if not text or text.startswith("⚠️"):
            continue
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

    parts = []
    for item in content_parts:
        if isinstance(item, str):
            parts.append(types.Part.from_text(text=item))
        elif isinstance(item, Image.Image):
            buf = io.BytesIO()
            item.convert("RGB").save(buf, format="JPEG")
            parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))
        else:
            parts.append(item)
    if not any(isinstance(p.text, str) and p.text for p in parts if hasattr(p, "text")):
        parts.append(types.Part.from_text(text="โปรดตอบหรือช่วยเหลือตามไฟล์/เสียง/รูปภาพที่แนบมา"))
    contents.append(types.Content(role="user", parts=parts))
    return contents

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

# 2. แถบซ้าย: ปุ่มเริ่มใหม่ + ประวัติการค้นหา (ไม่มีกล่อง ไม่มีไอคอนกวนใจ ตัวหนังสือเล็กกระชับ)
col_history, col_main = st.columns([1.15, 5])

with col_history:
    st.markdown('<div class="history-panel-marker"></div>', unsafe_allow_html=True)
    st.markdown('<div class="history-header">ประวัติการค้นหา</div>', unsafe_allow_html=True)

    if st.button("เริ่มใหม่", key="new_chat_btn"):
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        st.rerun()

    for session_id in list(st.session_state.all_chats.keys()):
        chat_history = st.session_state.all_chats[session_id]
        if not chat_history or len(chat_history) == 0:
            continue  # ห้องแชทว่างเปล่า ไม่ต้องแสดงในรายการ

        first_msg = chat_history[0]["text"]
        button_label = first_msg[:18] + "..." if len(first_msg) > 18 else first_msg

        if session_id == st.session_state.current_session_id:
            button_label = f"• {button_label}"

        if st.button(button_label, key=f"session_{session_id}"):
            st.session_state.current_session_id = session_id
            st.rerun()

    st.markdown('<div style="margin-top: 10px;"></div>', unsafe_allow_html=True)
    if st.button("ล้างประวัติทั้งหมด", key="clear_all_btn"):
        st.session_state.all_chats = {}
        st.session_state.current_session_id = f"Chat_{int(time.time())}"
        st.session_state.all_chats[st.session_state.current_session_id] = []
        if os.path.exists(ALL_CHATS_FILE):
            os.remove(ALL_CHATS_FILE)
        st.success("🧹 ล้างประวัติทุกห้องเกลี้ยงแล้ว!")
        time.sleep(1)
        st.rerun()

with col_main:
    # 3. พื้นที่แสดงเนื้อหาหลัก

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
                    st.markdown(f"<div class='{bubble_class}'><b>{role}:</b><br>{format_bubble_text(message['text'])}</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    """
                    <div style="
                        display: flex;
                        align-items: flex-end;
                        justify-content: center;
                        text-align: center;
                        min-height: 38vh;
                    ">
                        <div>
                            <div style="font-size: 32px; font-weight: 600; color: #202123; margin-bottom: 0;">
                                สวัสดีครับ คุณมีอะไรให้ผมช่วยไหม
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # ระยะห่างระหว่างข้อความทักทาย/ประวัติแชท กับกล่องพิมพ์ข้อความ
        # ให้แคบลงเมื่อยังไม่มีการสนทนา เพื่อให้ "สวัสดีครับ" กับกล่องพิมพ์ดูใกล้ชิดเป็นกลุ่มเดียวกัน
        gap_size = "14px" if not current_chat_history else "20px"
        st.markdown(f"<div style='padding-top: {gap_size};'></div>", unsafe_allow_html=True)

        # 🔴 ปุ่ม "+" ลอยซ้อนอยู่ข้างในขอบซ้ายสุดของกล่องพิมพ์ข้อความ กดแล้วเด้งเมนูแนบไฟล์ทั้งหมด
        col_plus, col_input = st.columns([0.6, 6.1])

        with col_plus:
            with st.popover("➕", use_container_width=False):
                # แต่ละรายการมีเครื่องหมายกำกับเฉพาะตัว (marker) ให้ CSS จำได้แม่นยำว่าเป็นปุ่มไหน
                # แล้วแทนที่ข้อความเริ่มต้นของ Streamlit (Browse files / Drag and drop...) ด้วยคำสั้น ๆ บอกแค่ว่าเป็นปุ่มอะไร
                with st.container():
                    st.markdown('<div class="attach-file-marker"></div>', unsafe_allow_html=True)
                    uploaded_file = st.file_uploader(
                        "แนบไฟล์", key="file_box", label_visibility="collapsed"
                    )

                with st.container():
                    st.markdown('<div class="attach-image-marker"></div>', unsafe_allow_html=True)
                    uploaded_image = st.file_uploader(
                        "แนบรูปภาพ", type=["jpg", "jpeg", "png"], key="img_box", label_visibility="collapsed"
                    )

            # ปุ่มไมค์อัดเสียง (ถูกสคริปต์ย้ายไปอยู่ข้างในช่องพิมพ์ข้อความ ทางขวาสุด)
            voice_recorder_data = st.audio_input(
                "อัดเสียง", key="voice_box", label_visibility="collapsed"
            )

        with col_input:
            # เครื่องหมายกำกับแถวนี้ไว้ ให้ CSS ด้านบนจำแถวได้แม่นยำ ไม่ไปชนกับคอลัมน์แถบประวัติด้านนอก
            st.markdown('<div class="chat-input-row-marker"></div>', unsafe_allow_html=True)
            # กล่องพิมพ์แชทมาตรฐานโผล่กลับมาแสดงผลชัดเจน 100% พิมพ์คล่องตัว และกด Enter บนคีย์บอร์ดสั่งส่งได้ทันที!
            user_prompt = st.chat_input("พิมพ์คำถามของคุณที่นี่ แล้วกด Enter เพื่อส่ง...")

        # 🕒 สคริปต์คอยตรวจจับว่ากำลังอัดเสียงอยู่หรือไม่ แล้วโชว์จำนวนวินาทีที่อัดไปแล้ว
        # เป็นข้อความ placeholder ในช่องพิมพ์ข้อความ (เมื่ออัดเสร็จ/หยุด จะคืนข้อความเดิมอัตโนมัติ)
        components.html("""
            <script>
            (function() {
                var P = window.parent;
                if (!P) { return; }
                var doc = P.document;

                // ---- 1) ย้ายปุ่ม "+" เข้าไปอยู่ข้างในกรอบกล่องพิมพ์ข้อความจริง ๆ ----
                function movePlus() {
                    var chat = doc.querySelector('div[data-testid="stChatInput"]');
                    var pop = doc.querySelector('div[data-testid="stPopover"]');
                    if (chat && pop && !chat.contains(pop)) {
                        chat.appendChild(pop);
                    }
                    var mic = doc.querySelector('div[data-testid="stAudioInput"]');
                    if (chat && mic && !chat.contains(mic)) {
                        chat.appendChild(mic);
                    }
                }

                // ---- 2) โชว์วินาทีที่อัดเสียงในช่องพิมพ์ข้อความ ----
                var startTime = null, originalPh = null, was = false;
                function isRecording() {
                    var el = doc.querySelector(
                        'div[data-testid="stAudioInputWaveSurfer"], div[data-testid="stAudioInputRecordState"]'
                    );
                    if (!el) { return false; }
                    var r = el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0;
                }
                function tick() {
                    movePlus();
                    // ติดป้ายให้ปุ่มอัพโหลดในเมนู + ตามลำดับ: อันแรก = ไฟล์, อันที่สอง = รูปภาพ
                    var ups = doc.querySelectorAll('div[data-testid="stPopoverBody"] div[data-testid="stFileUploader"]');
                    for (var i = 0; i < ups.length; i++) {
                        var want = (i === 0) ? 'file' : 'image';
                        if (ups[i].getAttribute('data-attach') !== want) { ups[i].setAttribute('data-attach', want); }
                    }
                    var ta = doc.querySelector('div[data-testid="stChatInput"] textarea');
                    if (!ta) { return; }
                    // ซ่อมตัวเอง: ถ้ามีอะไรบังกลางช่องพิมพ์ ให้คลิกทะลุไปถึงช่องพิมพ์
                    var tr = ta.getBoundingClientRect();
                    if (tr.width > 0 && tr.height > 0) {
                        var hit = doc.elementFromPoint(tr.left + tr.width / 2, tr.top + tr.height / 2);
                        if (hit && hit !== ta && !hit.contains(ta)) {
                            hit.style.setProperty('pointer-events', 'none', 'important');
                        }
                    }
                    var rec = isRecording();
                    if (rec && !was) {
                        startTime = Date.now();
                        if (originalPh === null) { originalPh = ta.getAttribute('placeholder') || ''; }
                    }
                    if (rec) {
                        var s = Math.floor((Date.now() - startTime) / 1000);
                        var mm = Math.floor(s / 60);
                        var ss = String(s % 60).padStart(2, '0');
                        ta.setAttribute('placeholder', '🎙️ กำลังอัดเสียง ' + mm + ':' + ss + ' ...');
                    } else if (was && originalPh !== null) {
                        ta.setAttribute('placeholder', originalPh);
                    }
                    was = rec;
                }
                // ตั้งตัวจับเวลาไว้ที่หน้าหลัก (parent) เพื่อให้ทำงานต่อแม้ iframe นี้ถูกสร้างใหม่ตอน Streamlit รันซ้ำ
                if (P.__chatUiTimer) { P.clearInterval(P.__chatUiTimer); }
                P.__chatUiTimer = P.setInterval(tick, 300);
            })();
            </script>
        """, height=0)

        # ระบบสั่งรันส่งคำถาม: ทำงานเมื่อมีการกด Enter ส่งข้อความ หรือตรวจพบสัญญาณเสียงพูดสดส่งเข้ามาสำเร็จ
        # ไฟล์/รูป/เสียงที่ส่งไปแล้ว จะไม่ถูกส่งซ้ำตอน Streamlit รันหน้าใหม่ (กันวนลูปส่งซ้ำไม่รู้จบ)
        consumed_ids = st.session_state.setdefault("consumed_ids", set())

        def _file_id(f):
            return getattr(f, "file_id", None) or (f.name, f.size)

        def _is_new(f):
            return f is not None and _file_id(f) not in consumed_ids

        uploaded_file = uploaded_file if _is_new(uploaded_file) else None
        uploaded_image = uploaded_image if _is_new(uploaded_image) else None
        voice_recorder_data = voice_recorder_data if _is_new(voice_recorder_data) else None

        # ส่งเมื่อกด Enter (พร้อมไฟล์/รูปที่แนบไว้) หรือเมื่ออัดเสียงเสร็จ
        if user_prompt or voice_recorder_data:

            # เตรียมข้อความที่จะแสดงในกล่องฝั่งผู้ใช้
            if user_prompt:
                display_text = user_prompt
            elif uploaded_image is not None:
                display_text = f"📎 ส่งรูปภาพ: {uploaded_image.name}"
            elif uploaded_file is not None:
                display_text = f"📎 ส่งไฟล์แนบ: {uploaded_file.name}"
            else:
                display_text = "📎 ส่งข้อความเสียง"

            # เพิ่มข้อความผู้ใช้เข้าประวัติแชท
            current_chat_history.append({"role": "user", "text": display_text})

            # เตรียมเนื้อหาที่จะส่งเข้า Gemini API (ข้อความ + ไฟล์แนบถ้ามี)
            content_parts = []

            if user_prompt:
                content_parts.append(user_prompt)

            if uploaded_image is not None:
                image = Image.open(uploaded_image)
                content_parts.append(image)

            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                file_mime = uploaded_file.type or "application/octet-stream"
                content_parts.append(
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=file_mime
                    )
                )

            if voice_recorder_data is not None:
                audio_bytes = voice_recorder_data.read()
                content_parts.append(
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/wav"
                    )
                )

            for _f in (uploaded_file, uploaded_image, voice_recorder_data):
                if _f is not None:
                    consumed_ids.add(_file_id(_f))

            # รวมบริบทประวัติแชทเดิมเป็นข้อความเดียว ก่อนส่งเข้าโมเดล
            full_context_string = "\n".join(
                [f"{msg['role']}: {msg['text']}" for msg in current_chat_history[:-1]]
            )

            with st.spinner("🤖 กำลังคิดคำตอบ..."):
                client = genai.Client(api_key=api_key)
                ai_text = None
                max_retries = 4
                last_error = None
                use_search = True  # เปิดการค้นหาข้อมูลล่าสุดจาก Google ถ้าใช้ไม่ได้จะปิดแล้วลองใหม่เอง

                for attempt in range(max_retries):
                    try:
                        config_kwargs = dict(
                            system_instruction=build_system_instruction(),
                            temperature=0.6,
                        )
                        if use_search:
                            config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
                        response = client.models.generate_content(
                            model=active_model,
                            contents=build_contents(current_chat_history[:-1], content_parts),
                            config=types.GenerateContentConfig(**config_kwargs),
                        )
                        ai_text = response.text
                        if not ai_text:
                            ai_text = "ขออภัยครับ ผมยังไม่สามารถตอบคำถามนี้ได้ ลองถามใหม่อีกครั้งด้วยคำอื่นดูนะครับ"
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
                        elif use_search and not is_temporary:
                            use_search = False  # อาจเป็นเพราะเครื่องมือค้นหาใช้ไม่ได้ ลองใหม่แบบไม่ค้นหา
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

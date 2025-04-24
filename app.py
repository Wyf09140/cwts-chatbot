from openai import OpenAI
import datetime
import gspread
import uuid
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
import json



openai_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=openai_key)

st.set_page_config(page_title="Seminary Admissions Chat Assistant", layout="centered")

# ✅ 多语言内容
translations = {
    "en": {
        "title": "📖 Seminary Admissions Chat Assistant",
        "form_tip": "Please fill out the information below so we can better assist you:",
        "name": "Your Name",
        "phone": "Phone (optional)",
        "contact": "Email or WeChat",
        "country": "Your Country",
        "interest": "Area of Interest (e.g. Online, Missions, Part-time)",
        "submit": "Submit and Start Chatting",
        "missing": "Please complete name, contact, country, and interest before continuing.",
        "success": "Submitted successfully! You may now ask your questions.",
        "input_placeholder": "Enter your question about the program (English supported)",
        "no_answer": "I'm sorry, I couldn't find that information in our official documentation."
    },
    "zh-CN": {
        "title": "📖 神学院招生问答助手",
        "form_tip": "请填写以下信息，我们将更好地为你服务：",
        "name": "你的名字",
        "phone": "联系电话（可选）：",
        "contact": "联系邮箱或微信号：",
        "country": "你所在的国家",
        "interest": "你感兴趣的方向（如远程课程、宣教、在职读研等）：",
        "submit": "✅ 提交并开始聊天",
        "missing": "请填写 *姓名、联系方式、所在国家 和 兴趣方向* 后再继续。",
        "success": "信息提交成功，你可以开始提问了！",
        "input_placeholder": "请输入你关于项目的问题（支持中文）",
        "no_answer": "抱歉，我无法在我们的官方文档中找到相关信息。"
    },
    "zh-TW": {
        "title": "📖 神學院招生問答助手",
        "form_tip": "請填写以下資訊，我們將更好地為您服務：",
        "name": "您的名字",
        "phone": "聯繫電話（可選）：",
        "contact": "聯繫郵箱或 WeChat：",
        "country": "您所在的國家",
        "interest": "您感興趣的領域（如遠距課程、宣教、職場進修等）：",
        "submit": "✅ 提交並開始聊天",
        "missing": "請填写 *姓名、聯繫資訊、所在國家與興趣領域* 之後繼續。",
        "success": "資訊提交成功，您現在可以開始提問了！",
        "input_placeholder": "請輸入您對該課程的問題（支援中文）",
        "no_answer": "尊敬的您，我無法從官方資料中找到相關資訊。"
    }
}

# ✅ Step 1: 语言选择
language_options = ["Please select a language / 请选择语言", "English", "中文（简体）", "中文（繁體）"]
selected_lang = st.selectbox("🌐 Language", language_options, index=0)
if selected_lang == language_options[0]:
    st.stop()

# ✅ Step 2: 设置语言状态
lang_code_map = {"English": "en", "中文（简体）": "zh-CN", "中文（繁體）": "zh-TW"}
lang_code = lang_code_map[selected_lang]
t = translations[lang_code]

# ✅ Step 3: 初始化状态
if "user_info_collected" not in st.session_state:
    st.session_state.user_info_collected = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# ✅ Step 4: 初始化 API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEET_CREDS"])
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(
    creds_dict,
    ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
)
gc = gspread.authorize(CREDS)
worksheet = gc.open("CWTS_Chatbot").sheet1

# ✅ Step 5: 显示表单
st.title(t["title"])
st.markdown(t["form_tip"])

if not st.session_state.user_info_collected:
    with st.form("user_info_form", clear_on_submit=False):
        name = st.text_input(t["name"])
        phone = st.text_input(t["phone"])
        contact = st.text_input(t["contact"])
        country = st.text_input(t["country"])
        interest = st.text_input(t["interest"])
        submitted = st.form_submit_button(t["submit"])

        if submitted:
            if not name or not contact or not interest or not country:
                st.warning(t["missing"])
            else:
                session_id = str(uuid.uuid4())[:8]
                st.session_state.user_info = {
                    "name": name,
                    "phone": phone,
                    "contact": contact,
                    "country": country,
                    "interest": interest,
                    "session_id": session_id
                }
                st.session_state.user_info_collected = True
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                worksheet.append_row([
                    timestamp, name, phone, contact, country, interest,
                    "info", "User Info Submitted", session_id
                ])
                st.success(t["success"])
                st.rerun()

# ✅ Step 6: 聊天界面
if st.session_state.user_info_collected:
    st.markdown("---")
    st.markdown("💬 " + t["input_placeholder"])

    for msg in st.session_state.messages:
        role = "👤 你" if msg["role"] == "user" else "🤖 招生助手"
        st.markdown(f"**{role}**：{msg['content']}")

    user_input = st.chat_input(t["input_placeholder"])

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ui = st.session_state.user_info
        worksheet.append_row([
            ts, ui["name"], ui["phone"], ui["contact"], ui["country"], ui["interest"],
            "user", user_input, ui["session_id"]
        ])

        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)

        vectordb = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        retriever = vectordb.as_retriever(search_kwargs={"k": 5})
        docs = retriever.get_relevant_documents(user_input)
        context = "\n".join([doc.page_content for doc in docs])

        messages = [
            {
                "role": "system",
                "content": f"""
                            You are a knowledgeable and trustworthy admissions assistant at a Christian Witness Theological Seminary.
                            
                            You must strictly answer ONLY based on the following provided document content.
                            
                            Use the user's input language when replying:
                            - If they speak English, reply in English.
                            - If they use Chinese (simplified or traditional), reply in Chinese.
                            - Do not mix Chinese and English unless necessary.
                            
                            Please format your response with:
                            - Bullet points
                            - Line breaks
                            - Short paragraphs for easier reading
                            
                            If the answer is not found, say: "{t['no_answer']}"
                            You are helping the Admission and Marketing team, so you are allowed to use marketing language when appropriate.
                            
                            Do NOT use outside knowledge.

                            Document:
                            {context}
                            """
                                          }
                                     ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]


        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        worksheet.append_row([
            ts, ui["name"], ui["phone"], ui["contact"], ui["country"], ui["interest"],
            "assistant", reply, ui["session_id"]
        ])
        st.rerun()

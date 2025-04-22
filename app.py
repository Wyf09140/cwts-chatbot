# 📌 Updated app.py with fuzzy search & recommendation
from openai import OpenAI
import datetime
import gspread
import uuid
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from fuzzywuzzy import process
import json

# ✅ API keys
openai_key = st.secrets["OPENAI_API_KEY"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEET_CREDS"])

client = OpenAI(api_key=openai_key)

st.set_page_config(page_title="Seminary Admissions Chat Assistant", layout="centered")

# ✅ Translations
translations = {
    "en": {
        "title": "\ud83d\udcd6 Seminary Admissions Chat Assistant",
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
        "title": "\ud83d\udcd6 \u795e\u5b66\u9662\u62db\u751f\u95ee\u7b54\u52a9\u624b",
        "form_tip": "\u8bf7\u586b\u5199\u4ee5\u4e0b\u4fe1\u606f\uff0c\u6211\u4eec\u5c06\u66f4\u597d\u5730\u4e3a\u4f60\u670d\u52a1\uff1a",
        "name": "\u4f60\u7684\u540d\u5b57",
        "phone": "\u8054\u7cfb\u7535\u8bdd\uff08\u53ef\u9009\uff09\uff1a",
        "contact": "\u8054\u7cfb\u90ae\u7bb1\u6216\u5fae\u4fe1\u53f7\uff1a",
        "country": "\u4f60\u6240\u5728\u7684\u56fd\u5bb6",
        "interest": "\u4f60\u611f\u5174\u8da3\u7684\u65b9\u5411\uff08\u5982\u8fdc\u7a0b\u8bfe\u7a0b\u3001\u5ba3\u6559\u3001\u5728\u804c\u8bfb\u7814\u7b49\uff09\uff1a",
        "submit": "\u2705 \u63d0\u4ea4\u5e76\u5f00\u59cb\u804a\u5929",
        "missing": "\u8bf7\u586b\u5199 *\u59d3\u540d\u3001\u8054\u7cfb\u65b9\u5f0f\u3001\u6240\u5728\u56fd\u5bb6 \u548c \u5174\u8da3\u65b9\u5411* \u540e\u518d\u7ee7\u7eed\u3002",
        "success": "\u4fe1\u606f\u63d0\u4ea4\u6210\u529f\uff0c\u4f60\u53ef\u4ee5\u5f00\u59cb\u63d0\u95ee\u4e86\uff01",
        "input_placeholder": "\u8bf7\u8f93\u5165\u4f60\u5173\u4e8e\u9879\u76ee\u7684\u95ee\u9898\uff08\u652f\u6301\u4e2d\u6587\uff09",
        "no_answer": "\u62b1\u6b49\uff0c\u6211\u65e0\u6cd5\u5728\u6211\u4eec\u7684\u5b98\u65b9\u6587\u6863\u4e2d\u627e\u5230\u76f8\u5173\u4fe1\u606f\u3002"
    }
}

# ✅ Language selection
lang_code_map = {"English": "en", "\u4e2d\u6587\uff08\u7b80\u4f53\uff09": "zh-CN", "\u4e2d\u6587\uff08\u7e41\u9ad4\uff09": "zh-TW"}
language_options = ["Please select a language / \u8bf7\u9009\u62e9\u8bed\u8a00", *lang_code_map.keys()]
selected_lang = st.selectbox("\ud83c\udf10 Language", language_options, index=0)
if selected_lang == language_options[0]:
    st.stop()

lang_code = lang_code_map[selected_lang]
t = translations[lang_code]

if "user_info_collected" not in st.session_state:
    st.session_state.user_info_collected = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# ✅ Google Sheet
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
gc = gspread.authorize(CREDS)
worksheet = gc.open("CWTS_Chatbot").sheet1

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

        if submitted and all([name, contact, country, interest]):
            session_id = str(uuid.uuid4())[:8]
            st.session_state.user_info = {
                "name": name, "phone": phone, "contact": contact,
                "country": country, "interest": interest, "session_id": session_id
            }
            st.session_state.user_info_collected = True
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([
                timestamp, name, phone, contact, country, interest,
                "info", "User Info Submitted", session_id
            ])
            st.success(t["success"])
            st.rerun()

if st.session_state.user_info_collected:
    st.markdown("---")
    st.markdown("\ud83d\udcac " + t["input_placeholder"])

    for msg in st.session_state.messages:
        role = "\ud83d\udc64 \u4f60" if msg["role"] == "user" else "\ud83e\udd16 \u62db\u751f\u52a9\u624b"
        st.markdown(f"**{role}**\uff1a{msg['content']}")

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

        # ✅ Fuzzy recommendation (optional)
        index_docs = vectordb.similarity_search(" ", k=50)
        questions = [doc.page_content[:80] for doc in index_docs]
        best_match, score = process.extractOne(user_input, questions)
        if score > 85:
            st.info(f"\ud83d\udd0d You might also be interested in: {best_match}")

        docs = retriever.get_relevant_documents(user_input)
        context = "\n".join([doc.page_content for doc in docs])

        messages = [
            {
                "role": "system",
                "content": f"""
You are a knowledgeable and trustworthy admissions assistant at a Christian seminary.
You must only answer based on the following document:
Use the user's input language.
Use bullet points and line breaks.
If the answer is not found, say: {t['no_answer']}
Document:
{context}
"""
            }
        ] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.6
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        worksheet.append_row([
            ts, ui["name"], ui["phone"], ui["contact"], ui["country"], ui["interest"],
            "assistant", reply, ui["session_id"]
        ])
        st.rerun()

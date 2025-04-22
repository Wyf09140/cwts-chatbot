from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import streamlit as st  # ✅ 用于读取 secrets

# 1. 加载 Word 文档
loader = Docx2txtLoader("CWTS_Info_04_2025.docx")
docs = loader.load()

# 2. 拆分成段落
text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
split_docs = text_splitter.split_documents(docs)

# 3. 创建 Embeddings（使用 Streamlit Cloud 的密钥）
embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])

# 4. 构建 FAISS 向量库
vectorstore = FAISS.from_documents(split_docs, embeddings)

# 5. 保存向量数据库
vectorstore.save_local("faiss_index")

print(f"✅ 成功构建并保存向量知识库，共处理段落数：{len(split_docs)}")

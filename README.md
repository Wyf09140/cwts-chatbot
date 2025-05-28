# 📖 Seminary Admissions Chat Assistant  

**An AI-powered chat assistant** designed for automating seminary admissions Q&A, capturing prospective applicant information, and improving admissions workflow efficiency through intelligent, accurate, and multilingual interactions.

---

## 🚀 Overview  

The **Seminary Admissions Chat Assistant** streamlines and enhances the admissions process for Christian Witness Theological Seminary by automating responses to frequently asked questions, collecting structured applicant data, and providing a user-friendly multilingual interface.

---

## ✨ Key Features  

- **Multilingual Support**: Seamlessly interacts in English, Simplified Chinese (中文简体), and Traditional Chinese (中文繁體).
- **Semantic Search & Retrieval**: Powered by OpenAI Embeddings and FAISS vector database for precise document retrieval and content matching.
- **Fuzzy Matching**: Enhances query precision and accommodates variations in user input using FuzzyWuzzy.
- **Automated Data Logging**: Automatically captures user interactions and chatbot responses into Google Sheets for easy follow-up.
- **Intelligent Chatbot**: Utilizes OpenAI GPT-3.5 Turbo to generate reliable, context-based answers strictly from provided documentation.

---

## 🛠️ Tech Stack  

| Category                | Technologies Used                                   |
|-------------------------|-----------------------------------------------------|
| **Web Framework**       | Streamlit                                           |
| **LLM Model**           | OpenAI GPT-3.5 Turbo                                |
| **Vector DB & Search**  | FAISS, OpenAI Embeddings                            |
| **Fuzzy Matching**      | FuzzyWuzzy                                          |
| **Data Management**     | Google Sheets, gspread                              |
| **Security & Secrets**  | Streamlit Secrets, dotenv                           |
| **Development & Hosting**| Python, GitHub, Streamlit Cloud                    |

---

## 📌 Getting Started  

### Prerequisites  

- Python 3.8 or above  
- API keys for OpenAI and Google Sheets  

### Installation  

```bash
git clone https://github.com/your_username/seminary-admissions-chat-assistant.git
cd seminary-admissions-chat-assistant
pip install -r requirements.txt

# 📚 DocuMind AI

DocuMind AI is an AI-powered document Q&A and exam preparation application built with **Python, Streamlit, LangChain, FAISS, spaCy, and Google Gemini**.

It allows users to upload PDF documents, ask questions about their content, receive AI-generated answers with source references, and use AI-powered study tools for exam preparation.

## ✨ Features

### 💬 AI Document Chat
- ChatGPT-style conversational interface
- Create multiple chats
- Persistent chat history using SQLite
- Ask questions about uploaded PDF documents
- AI-generated answers powered by Google Gemini
- Clean conversational question-and-answer interface
- Questions displayed on the right and AI answers on the left
- Compact document source references

### 📄 PDF Document Processing
- Upload multiple PDF documents
- Process documents within individual chats
- Extract text from PDFs using PyPDF
- Split documents into chunks using LangChain
- Generate embeddings using spaCy
- Store and search document vectors using FAISS
- Separate FAISS index for each chat
- Page/source references for document-based answers

### 📚 AI Study Tools
- **Exam Mode** – Generate AI-powered multiple-choice questions
- **MCQ Generator** – Generate MCQs based on topic, question count, and difficulty
- **Mock Test** – Take timed tests and view your score
- **Weak Topic Analysis** – Identify topics that need improvement
- **Flashcards** – Generate AI-powered study flashcards
- **Performance Dashboard** – Track study and exam performance

### 🗂️ Chat Management
- New Chat
- Recent Chat History
- Rename conversations
- Share complete conversations
- Delete conversations
- User-specific chat history
- Clean ChatGPT-style chat management interface

### 👤 Authentication
- Google Sign-In
- Streamlit OIDC authentication
- User-specific conversations and data

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Application development |
| Streamlit | Web application and UI |
| Google Gemini | Large Language Model |
| LangChain | Document processing and RAG |
| FAISS | Vector similarity search |
| spaCy | Text embeddings |
| PyPDF | PDF text extraction |
| SQLite | Chat history and application data |
| Authlib | Google OAuth/OIDC authentication |

## 🔄 Application Workflow

```text
                 ┌─────────────────┐
                 │    User Login   │
                 │   Google OAuth  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │    New Chat     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   Upload PDFs   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Extract Text   │
                 │     PyPDF       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Text Chunking  │
                 │   LangChain     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ spaCy Embeddings│
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  FAISS Vector   │
                 │      Index      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  User Question  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Similarity Search│
                 │      FAISS      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  Google Gemini  │
                 │   AI Response   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Answer + Sources│
                 └─────────────────┘

```

## 📁 Project Structure

```text
=======


📁 Project Structure
>>>>>>> 54c2eab0a656984900d49e7679284216b7b424ea
DocuMind-AI/
│
├── .streamlit/
│   └── secrets.toml.example
│
├── data/
│   └── Application data and FAISS indexes
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── venv/
```

> `venv/`, `.env`, `.streamlit/secrets.toml`, and local application data should not be committed to GitHub.

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/DURGAPRASAD1419/DocuMind-AI.git
cd DocuMind-AI
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

### 3. Activate the virtual environment

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

If the spaCy model is not installed, run:

```powershell
python -m spacy download en_core_web_sm
```

### 5. Configure Gemini API

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

Replace `YOUR_GEMINI_API_KEY` with your actual Gemini API key.

**Never commit `.env` to GitHub.**

### 6. Configure Google Login

Create:

```text
.streamlit/secrets.toml
```

Use the following configuration:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "YOUR_RANDOM_SECRET"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Replace the placeholder values with your Google OAuth credentials.

In Google Cloud Console, add the following as an authorized redirect URI:

```text
http://localhost:8501/oauth2callback
```

### 7. Run the application

```powershell
python -m streamlit run app.py
```

The application will be available at:

```text
http://localhost:8501
```

## ☁️ Deployment

DocuMind AI is deployed using **Render**.

### Render Configuration

**Service Type:**

```text
Web Service
```

**Branch:**

```text
main
```

**Root Directory:**

```text
Leave empty
```

**Build Command:**

```bash
pip install -r requirements.txt
```

**Start Command:**

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port $PORT
```

### Production URL

```text
https://documind-ai-cogn.onrender.com
```

### Google OAuth Redirect URI

For the deployed application, use:

```text
https://documind-ai-cogn.onrender.com/oauth2callback
```

Add this URL to the **Authorized redirect URIs** section of your Google OAuth client.

### Production Authentication

OAuth credentials and other sensitive information should be stored using Render's environment variables or secret files.

Do not commit production credentials to GitHub.

## 🔐 Environment Variables and Secrets

The following values should be kept private:

```text
GEMINI_API_KEY
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
COOKIE_SECRET
```

Never put these values directly into the source code.

Never commit:

```text
.env
.streamlit/secrets.toml
venv/
```

If a secret or API key is accidentally exposed, revoke and rotate it immediately.

## 💾 Data Storage

DocuMind AI currently uses:

- **SQLite** for chat history and application data
- **FAISS** for document vector indexes
- **Local storage** for application files and processed document data

Each chat can have its own FAISS index, allowing document-based conversations to remain separated.

For large-scale production deployment, the application can later be migrated to:

- PostgreSQL
- Cloud/object storage
- Managed vector databases
- Persistent cloud storage

## 🎯 Future Improvements

- Persistent cloud database
- Cloud storage for uploaded documents
- Managed vector database
- Conversation export
- PDF/document management improvements
- Additional AI study tools
- Advanced performance analytics
- Production-grade scaling
- Improved document processing
- More LLM provider support

## 👨‍💻 Project Information

**Project Name:** DocuMind AI

**Repository:** https://github.com/DURGAPRASAD1419/DocuMind-AI


**Application:** AI-powered document Q&A and exam preparation platform

DocuMind AI combines **Retrieval-Augmented Generation (RAG)** with AI-powered exam preparation tools to help users understand documents, ask questions, practice exams, revise using flashcards, and analyze their performance.

## 📄 License

=======
>>>>>>> 54c2eab0a656984900d49e7679284216b7b424ea
This project is intended for educational and project demonstration purposes.

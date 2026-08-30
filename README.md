# 📚 Exam AI

AI-powered exam preparation and PDF Q&A application built with Streamlit, LangChain, FAISS, SpaCy embeddings and Google Gemini.

## Features

1. Google Login with Streamlit OIDC
2. ChatGPT-style New Chat and persistent chat history using SQLite
3. Multiple PDFs with a separate FAISS index for each chat
4. PDF/page source citations in answers
5. Exam Mode with AI-generated MCQs
6. MCQ Generator with explanations and difficulty
7. Timed Mock Test with score and weak-topic analysis
8. AI Flashcards
9. Performance dashboard
10. Export can be added later without changing the data model

## Setup

### 1. Create and activate venv (Windows)

```powershell
python -m venv venv
.env\Scripts\Activate.ps1
```

### 2. Install packages

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Gemini API key

Create `.env` in the project root:

```text
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

### 4. Google Login

Create `.streamlit/secrets.toml` using `secrets.toml.example`.

Set:

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "YOUR_RANDOM_SECRET"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

In Google Cloud OAuth settings, add this authorized redirect URI:

`http://localhost:8501/oauth2callback`

### 5. Run

```powershell
python -m streamlit run app.py
```

## Data

The app stores SQLite chat history and per-chat FAISS indexes in `data/`. These are local files and are ignored by Git.

## Security

Never commit `.env` or `.streamlit/secrets.toml`. If an API key was previously exposed, revoke/rotate it before using the project.

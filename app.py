# ================================================================
# EXAM-AI — AI DOCUMENT Q&A + EXAM PREPARATION
# Features:
# 1. Google Login
# 2. New Chat + persistent chat history
# 3. Multiple PDFs + separate FAISS per chat
# 4. PDF/page source citations
# 5. Exam Mode
# 6. MCQ Generator
# 7. Timed Mock Test + score/weak-topic analysis
# 8. AI Flashcards
# ================================================================

import os
import re
import json
import uuid
import sqlite3
import shutil
import secrets
from pathlib import Path
from datetime import datetime

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.spacy_embeddings import SpacyEmbeddings
from langchain_community.vectorstores import FAISS

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


# ----------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------
# CHATGPT-STYLE UI
# ----------------------------------------------------------------
st.markdown(
    """
    <style>

    section[data-testid="stSidebar"] {
        background: #f7f7f8;
        border-right: 1px solid #e5e5e5;
    }

    section[data-testid="stSidebar"] button {
        border-radius: 8px;
    }

    section[data-testid="stSidebar"] button:hover {
        background: #ececec;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 20px;
        padding: 5px 5px 15px 5px;
    }

    .sidebar-brand span {
        font-size: 25px;
    }

    .sidebar-divider {
        height: 1px;
        background: #e5e5e5;
        margin: 12px 0;
    }

    .history-title,
    .section-title {
        font-size: 12px;
        font-weight: 600;
        color: #777;
        text-transform: uppercase;
        padding: 4px 8px 8px 8px;
    }

    .empty-history {
        font-size: 13px;
        color: #888;
        padding: 10px 8px;
    }

    .profile-spacer {
        min-height: 25px;
    }

    .profile-name {
        font-size: 14px;
        font-weight: 600;
        margin-top: 3px;
    }

    .profile-email {
        font-size: 11px;
        color: #777;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #555;
        color: white;
        font-weight: 600;
    }


    /* ------------------------------------------------------------
       ChatGPT-style 3-dot menu: Share / Rename / Delete
       ------------------------------------------------------------ */

    section[data-testid="stSidebar"] [data-testid="stPopover"] > button {
        width: 34px !important;
        min-width: 34px !important;
        height: 32px !important;
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        color: #202123 !important;
        box-shadow: none !important;
        border-radius: 7px !important;
        font-size: 20px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
        background: #ececec !important;
    }

    /* Remove the popover arrow/caret. */
    section[data-testid="stSidebar"] [data-testid="stPopover"] > button::after {
        display: none !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPopoverBody"] {
        background: #ffffff !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.16) !important;
        padding: 6px !important;
        min-width: 175px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPopoverBody"] button {
        color: #202123 !important;
        background: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 7px !important;
        font-size: 14px !important;
        font-weight: 400 !important;
        min-height: 38px !important;
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 7px 10px !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPopoverBody"] button:hover {
        background: #f5f5f5 !important;
        color: #202123 !important;
    }

    .menu-divider {
        height: 1px;
        background: #e5e5e5;
        margin: 5px 0;
    }

    /* Delete is the only red action. */
    section[data-testid="stSidebar"] [data-testid="stPopoverBody"] button[key*="delete_chat"] {
        color: #ff3b30 !important;
    }

    section[data-testid="stSidebar"] [data-testid="stPopoverBody"] button[key*="delete_chat"]:hover {
        background: #fff1f0 !important;
        color: #d70015 !important;
    }


    /* ------------------------------------------------------------
       Responsive rename editor
       ------------------------------------------------------------ */

    section[data-testid="stSidebar"] .rename-editor {
        width: 100%;
        margin-top: 4px;
    }

    section[data-testid="stSidebar"] .rename-editor + div {
        margin-top: 0 !important;
    }

    section[data-testid="stSidebar"] input[aria-label="Chat name"] {
        width: 100% !important;
        min-height: 40px !important;
        box-sizing: border-box !important;
        border-radius: 8px !important;
        font-size: 14px !important;
    }

    section[data-testid="stSidebar"] .rename-editor button {
        min-height: 36px !important;
        height: 36px !important;
        border-radius: 8px !important;
        font-size: 13px !important;
    }

    @media (min-width: 901px) {
        section[data-testid="stSidebar"] .rename-editor {
            max-width: 100%;
        }
    }

    @media (max-width: 600px) {
        section[data-testid="stSidebar"] .rename-editor {
            margin-bottom: 2px;
        }
    }


    /* ------------------------------------------------------------
       Desktop-friendly Rename / Share panels
       ------------------------------------------------------------ */

    .rename-panel-title,
    .share-panel-title {
        font-size: 14px;
        font-weight: 600;
        color: #202123;
        margin: 8px 0 5px 2px;
    }

    section[data-testid="stSidebar"] input[aria-label="Chat name"] {
        width: 100% !important;
        box-sizing: border-box !important;
        min-height: 40px !important;
        border-radius: 8px !important;
        font-size: 14px !important;
    }

    section[data-testid="stSidebar"] .rename-panel-title + div {
        width: 100% !important;
    }

    @media (min-width: 769px) {
        section[data-testid="stSidebar"] {
            min-width: 320px;
        }

        section[data-testid="stSidebar"] .block-container {
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
    }


    /* ------------------------------------------------------------
       Full conversation sharing
       ------------------------------------------------------------ */

    .shared-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
    }

    .shared-brand {
        font-size: 18px;
        font-weight: 600;
        color: #202123;
    }

    .shared-badge {
        font-size: 12px;
        color: #666;
        background: #f1f1f1;
        border-radius: 999px;
        padding: 4px 9px;
    }

    .share-note {
        font-size: 12px;
        color: #777;
        margin-top: 5px;
    }


    /* ------------------------------------------------------------
       Compact ChatGPT-style sources
       ------------------------------------------------------------ */

    [data-testid="stExpander"] {
        margin-top: 5px !important;
        margin-bottom: 2px !important;
        border: none !important;
        background: transparent !important;
    }

    [data-testid="stExpander"] summary {
        padding: 2px 0 !important;
        min-height: 24px !important;
        color: #6b6b6b !important;
        font-size: 12px !important;
        font-weight: 400 !important;
    }

    [data-testid="stExpander"] summary:hover {
        color: #202123 !important;
        background: transparent !important;
    }

    [data-testid="stExpanderDetails"] {
        padding: 2px 0 5px 0 !important;
        background: transparent !important;
    }

    .compact-source {
        color: #666666;
        font-size: 11px;
        line-height: 1.45;
        margin: 1px 0;
    }


    /* ------------------------------------------------------------
       CLEAR CHAT LAYOUT — user on right, AI on left
       ------------------------------------------------------------ */

    /* Every conversation turn gets comfortable spacing. */
    div[data-testid="stChatMessage"] {
        margin: 10px 0 18px 0 !important;
        gap: 10px !important;
    }

    /* USER: right aligned, light bubble, dark text. */
    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-user"]
    ) {
        flex-direction: row-reverse !important;
        justify-content: flex-start !important;
    }

    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-user"]
    ) > div:last-child {
        background: #f1f1f1 !important;
        color: #202123 !important;
        border-radius: 18px !important;
        padding: 10px 15px !important;
        max-width: min(78%, 760px) !important;
        margin-left: auto !important;
        margin-right: 0 !important;
    }

    /* ASSISTANT: left aligned, clean white area. */
    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-assistant"]
    ) {
        flex-direction: row !important;
        justify-content: flex-start !important;
    }

    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-assistant"]
    ) > div:last-child {
        background: #ffffff !important;
        color: #202123 !important;
        border-radius: 12px !important;
        padding: 4px 12px 8px 12px !important;
        max-width: min(82%, 820px) !important;
        margin-left: 0 !important;
        margin-right: auto !important;
    }

    /* Keep normal markdown typography inside both roles. */
    div[data-testid="stChatMessage"] p {
        margin-top: 2px !important;
        margin-bottom: 7px !important;
        line-height: 1.55 !important;
    }

    /* User text should not look like an AI answer. */
    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-user"]
    ) p {
        font-size: 15px !important;
    }

    /* AI answer is slightly wider/easier to read. */
    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-assistant"]
    ) p {
        font-size: 15px !important;
    }

    /* Compact source row stays attached to the AI answer. */
    div[data-testid="stChatMessage"]:has(
        [data-testid="chatAvatarIcon-assistant"]
    ) [data-testid="stExpander"] {
        max-width: 220px !important;
    }

    /* On small screens, let bubbles use almost the full width. */
    @media (max-width: 700px) {
        div[data-testid="stChatMessage"]:has(
            [data-testid="chatAvatarIcon-user"]
        ) > div:last-child,
        div[data-testid="stChatMessage"]:has(
            [data-testid="chatAvatarIcon-assistant"]
        ) > div:last-child {
            max-width: 90% !important;
        }
    }


    /* ------------------------------------------------------------
       ChatGPT-style fixed bottom composer
       ------------------------------------------------------------ */

    .documind-chat-history {
        padding-bottom: 105px !important;
    }

    /* Keep Streamlit's chat input fixed at the bottom of the viewport.
       It remains in the same location while messages grow above it. */
    div[data-testid="stChatInput"] {
        position: fixed !important;
        left: calc(50% + 140px) !important;
        transform: translateX(-50%) !important;
        bottom: 18px !important;
        width: min(720px, calc(100vw - 360px)) !important;
        z-index: 1000 !important;
        background: transparent !important;
    }

    div[data-testid="stChatInput"] > div {
        background: #ffffff !important;
        border-radius: 18px !important;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08) !important;
    }

    @media (max-width: 900px) {
        div[data-testid="stChatInput"] {
            left: 50% !important;
            width: min(720px, calc(100vw - 32px)) !important;
            bottom: 12px !important;
        }

        .documind-chat-history {
            padding-bottom: 95px !important;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)




# ----------------------------------------------------------------
# PATHS / ENVIRONMENT
# ----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FAISS_DIR = DATA_DIR / "faiss"
DB_PATH = DATA_DIR / "exam_ai.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
FAISS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-3.5-flash-lite"

if genai is None:
    st.error("Missing package: google-genai. Run: python -m pip install google-genai")
    st.stop()

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is missing. Add it to your .env file.")
    st.stop()

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ----------------------------------------------------------------
# DATABASE
# ----------------------------------------------------------------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT,
            picture TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            page_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            chat_id TEXT,
            test_type TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            weak_topics TEXT,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS share_links (
            share_id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_user(user):
    conn = db()
    conn.execute("""
        INSERT INTO users(user_id,email,name,picture,created_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET
            email=excluded.email,
            name=excluded.name,
            picture=excluded.picture
    """, (
        user["user_id"], user["email"], user["name"],
        user["picture"], datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def create_chat(user_id, title="New Chat"):
    chat_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    conn = db()
    conn.execute("""
        INSERT INTO chats(chat_id,user_id,title,created_at,updated_at)
        VALUES(?,?,?,?,?)
    """, (chat_id, user_id, title, now, now))
    conn.commit()
    conn.close()
    return chat_id


def get_chats(user_id):
    conn = db()
    rows = conn.execute("""
        SELECT * FROM chats WHERE user_id=?
        ORDER BY updated_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


def get_chat(chat_id, user_id):
    conn = db()
    row = conn.execute("""
        SELECT * FROM chats WHERE chat_id=? AND user_id=?
    """, (chat_id, user_id)).fetchone()
    conn.close()
    return row


def update_chat(chat_id, user_id, title=None):
    conn = db()
    if title is None:
        conn.execute("""
            UPDATE chats SET updated_at=?
            WHERE chat_id=? AND user_id=?
        """, (datetime.now().isoformat(), chat_id, user_id))
    else:
        conn.execute("""
            UPDATE chats SET title=?, updated_at=?
            WHERE chat_id=? AND user_id=?
        """, (title, datetime.now().isoformat(), chat_id, user_id))
    conn.commit()
    conn.close()


def delete_chat(chat_id, user_id):
    conn = db()
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM documents WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    conn.commit()
    conn.close()
    folder = FAISS_DIR / chat_id
    if folder.exists():
        shutil.rmtree(folder)


def save_message(chat_id, role, content):
    conn = db()
    conn.execute("""
        INSERT INTO messages(chat_id,role,content,created_at)
        VALUES(?,?,?,?)
    """, (chat_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_messages(chat_id):
    conn = db()
    rows = conn.execute("""
        SELECT * FROM messages WHERE chat_id=?
        ORDER BY message_id ASC
    """, (chat_id,)).fetchall()
    conn.close()
    return rows


def create_share_link(chat_id, user_id):
    """Create or reuse a secure link token for the whole conversation."""
    conn = db()

    existing = conn.execute(
        """
        SELECT share_id
        FROM share_links
        WHERE chat_id=? AND user_id=?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (chat_id, user_id),
    ).fetchone()

    if existing:
        token = existing["share_id"]
    else:
        token = secrets.token_urlsafe(32)
        conn.execute(
            """
            INSERT INTO share_links(
                share_id, chat_id, user_id, created_at
            )
            VALUES(?,?,?,?)
            """,
            (
                token,
                chat_id,
                user_id,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

    conn.close()
    return token


def get_shared_chat(token):
    """Return a shared chat and its messages for a valid share token."""
    if not token:
        return None, []

    conn = db()

    row = conn.execute(
        """
        SELECT c.*
        FROM share_links s
        JOIN chats c ON c.chat_id = s.chat_id
        WHERE s.share_id=?
        """,
        (token,),
    ).fetchone()

    if not row:
        conn.close()
        return None, []

    messages = conn.execute(
        """
        SELECT *
        FROM messages
        WHERE chat_id=?
        ORDER BY message_id ASC
        """,
        (row["chat_id"],),
    ).fetchall()

    documents = conn.execute(
        """
        SELECT *
        FROM documents
        WHERE chat_id=?
        ORDER BY document_id ASC
        """,
        (row["chat_id"],),
    ).fetchall()

    conn.close()
    return row, messages, documents


def build_share_url(token):
    """Build the current app URL with the share token."""
    try:
        headers = st.context.headers
        host = headers.get("Host", "")
        forwarded_proto = headers.get("X-Forwarded-Proto", "")
        proto = (
            forwarded_proto.split(",")[0].strip()
            if forwarded_proto
            else "http"
        )

        if host:
            return f"{proto}://{host}/?share={token}"
    except Exception:
        pass

    return f"http://localhost:8501/?share={token}"


def render_shared_conversation(token):
    """Render a read-only whole-conversation share page."""
    result = get_shared_chat(token)

    if not result or result[0] is None:
        st.error("This shared conversation does not exist or is no longer available.")
        return

    chat, messages, documents = result

    st.markdown(
        """
        <div class="shared-header">
            <div class="shared-brand">DocuMind AI</div>
            <div class="shared-badge">Shared conversation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.title(chat["title"] or "Shared conversation")

    if documents:
        unique_names = []
        for doc in documents:
            name = doc["file_name"]
            if name not in unique_names:
                unique_names.append(name)

        st.markdown(
            "**Documents:** " + ", ".join(unique_names)
        )

    st.markdown("---")

    if not messages:
        st.info("This conversation has no messages yet.")
    else:
        for message in messages:
            role = "user" if message["role"] == "user" else "assistant"

            with st.chat_message(role):
                if role == "assistant":
                    render_assistant_message(
                        message["content"],
                        message_key=f"shared_{message['message_id']}",
                    )
                else:
                    st.markdown(message["content"])

    st.markdown("---")
    st.caption(
        "This is a read-only shared conversation. "
        "The original owner can continue using the chat normally."
    )


def save_document(chat_id, file_name, page_count):
    conn = db()
    conn.execute("""
        INSERT INTO documents(chat_id,file_name,page_count,created_at)
        VALUES(?,?,?,?)
    """, (chat_id, file_name, page_count, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_documents(chat_id):
    conn = db()
    rows = conn.execute("""
        SELECT * FROM documents WHERE chat_id=?
        ORDER BY document_id DESC
    """, (chat_id,)).fetchall()
    conn.close()
    return rows


def save_test_result(user_id, chat_id, test_type, score, total, weak_topics):
    conn = db()
    conn.execute("""
        INSERT INTO test_results
        (user_id,chat_id,test_type,score,total,weak_topics,created_at)
        VALUES(?,?,?,?,?,?,?)
    """, (
        user_id, chat_id, test_type, score, total,
        json.dumps(weak_topics, ensure_ascii=False),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_test_results(user_id):
    conn = db()
    rows = conn.execute("""
        SELECT * FROM test_results
        WHERE user_id=?
        ORDER BY result_id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return rows


# ----------------------------------------------------------------
# USER / AUTH
# ----------------------------------------------------------------
def current_user():
    return {
        "user_id": str(st.user.get("sub", st.user.get("email", ""))),
        "email": str(st.user.get("email", "")),
        "name": str(st.user.get("name", "User")),
        "picture": str(st.user.get("picture", "")),
    }


def login_screen():
    st.markdown("""
        <div style="text-align:center;padding-top:120px;">
            <h1>📚 DocuMind AI</h1>
            <h3>AI-Powered Exam Preparation</h3>
            <p>Sign in with Google to save your chats and study progress.</p>
        </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("🔐 Continue with Google", use_container_width=True):
            st.login()


# ----------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------
def init_state():
    defaults = {
        "current_chat_id": None,
        "exam_questions": [],
        "exam_answers": {},
        "exam_submitted": False,
        "exam_type": "Chat",
        "active_tool": "Chat",
        "mock_started": False,
        "mock_start_time": None,
        "mock_duration": 10,
        "flashcards": [],
        "flashcard_index": 0,
        "pending_fallback": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "embeddings" not in st.session_state:
        st.session_state.embeddings = SpacyEmbeddings(model_name="en_core_web_sm")


# ----------------------------------------------------------------
# GEMINI HELPERS
# ----------------------------------------------------------------
def gemini_text(prompt, max_tokens=1200):
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=max_tokens),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()


def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end >= 0:
        text = text[start:end + 1]
    return json.loads(text)


# ----------------------------------------------------------------
# PDF / FAISS
# ----------------------------------------------------------------
def chat_faiss_path(chat_id):
    path = FAISS_DIR / chat_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def has_faiss(chat_id):
    return (chat_faiss_path(chat_id) / "index.faiss").exists()


def extract_pdf_documents(pdf_file):
    reader = PdfReader(pdf_file)
    docs = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": pdf_file.name,
                    "page": page_number,
                }
            ))
    return docs, len(reader.pages)


def process_pdfs(pdf_files, chat_id):
    raw_docs = []
    page_counts = []

    for pdf in pdf_files:
        docs, page_count = extract_pdf_documents(pdf)
        if docs:
            raw_docs.extend(docs)
            page_counts.append((pdf.name, page_count))

    if not raw_docs:
        raise ValueError("No readable text was found in the uploaded PDF(s).")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = splitter.split_documents(raw_docs)

    if not chunks:
        raise ValueError("No text chunks were created.")

    vector_store = FAISS.from_documents(
        chunks,
        embedding=st.session_state.embeddings,
    )
    vector_store.save_local(str(chat_faiss_path(chat_id)))

    for name, count in page_counts:
        save_document(chat_id, name, count)

    return len(chunks), len(raw_docs)


def retrieve_context(chat_id, question, k=5):
    if not has_faiss(chat_id):
        return []
    store = FAISS.load_local(
        str(chat_faiss_path(chat_id)),
        st.session_state.embeddings,
        allow_dangerous_deserialization=True,
    )
    retriever = store.as_retriever(search_kwargs={"k": k})
    return retriever.invoke(question)


def format_sources(docs):
    seen = set()
    sources = unique_sources([])
    for doc in docs:
        source = doc.metadata.get("source", "Unknown document")
        page = doc.metadata.get("page", "?")
        key = (source, page)
        if key not in seen:
            seen.add(key)
            sources.append(f"- **{source}**, page {page}")
    return "\n".join(sources)


# ----------------------------------------------------------------
# DOCUMENT Q&A
# ----------------------------------------------------------------
def answer_question(chat_id, question):
    docs = retrieve_context(chat_id, question, k=5)

    if not docs:
        return "NO_DOCUMENT"

    context = "\n\n".join(
        f"[{d.metadata.get('source','Document')} - page {d.metadata.get('page','?')}]\n{d.page_content}"
        for d in docs
    )

    history = get_messages(chat_id)[-6:]
    previous = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history
    )

    prompt = f"""
You are an exam-preparation RAG assistant.

DOCUMENT CONTEXT:
{context}

RECENT CONVERSATION:
{previous}

CURRENT QUESTION:
{question}

Rules:
- Answer the CURRENT question.
- Prefer the document context.
- Previous conversation may clarify the question, but do not repeat old answers unnecessarily.
- Do not invent facts.
- If the document does not contain the answer, return exactly ANSWER_NOT_FOUND.
- Give a concise, useful answer for a student.
"""
    answer = gemini_text(prompt, 1200)

    if answer == "ANSWER_NOT_FOUND":
        return answer

    source_text = format_sources(docs)
    return f"{answer}\n\n**📌 Sources**\n{source_text}"


# ----------------------------------------------------------------
# EXAM / MCQ GENERATION
# ----------------------------------------------------------------
def generate_mcqs(chat_id, count, difficulty, topic=""):
    docs = retrieve_context(
        chat_id,
        topic if topic.strip() else "important concepts and exam topics",
        k=12,
    )
    if not docs:
        raise ValueError("Process a PDF before generating exam questions.")

    context = "\n\n".join(
        f"[{d.metadata.get('source')} - page {d.metadata.get('page')}]\n{d.page_content}"
        for d in docs
    )

    prompt = f"""
Create exactly {count} multiple-choice exam questions from the document context.

Difficulty: {difficulty}
Topic: {topic if topic.strip() else "all important topics"}

Return ONLY valid JSON as an array.
Each object must have:
question
options (exactly 4 strings)
answer (0, 1, 2, or 3)
explanation
topic

Do not use information outside the context.

DOCUMENT CONTEXT:
{context}
"""
    return extract_json(gemini_text(prompt, 2500))


# ----------------------------------------------------------------
# FLASHCARDS
# ----------------------------------------------------------------
def generate_flashcards(chat_id, count, topic=""):
    docs = retrieve_context(
        chat_id,
        topic if topic.strip() else "important concepts",
        k=12,
    )
    if not docs:
        raise ValueError("Process a PDF before generating flashcards.")

    context = "\n\n".join(
        d.page_content for d in docs
    )

    prompt = f"""
Create exactly {count} study flashcards from the document context.
Topic: {topic if topic.strip() else "all important topics"}

Return ONLY valid JSON:
[
  {{"front":"question or term","back":"clear answer","topic":"topic"}}
]

DOCUMENT:
{context}
"""
    return extract_json(gemini_text(prompt, 2200))


# ----------------------------------------------------------------
# CLEAN CHAT HISTORY HELPERS
# ----------------------------------------------------------------
def reset_chat_state():
    st.session_state.exam_questions = []
    st.session_state.exam_answers = {}
    st.session_state.exam_submitted = False
    st.session_state.flashcards = []
    st.session_state.flashcard_index = 0
    st.session_state.mock_started = False
    st.session_state.mock_start_time = None
    st.session_state.pending_fallback = None


def chat_has_content(chat_id):
    conn = db()
    row = conn.execute(
        """
        SELECT
            EXISTS(SELECT 1 FROM messages WHERE chat_id = ?) AS has_messages,
            EXISTS(SELECT 1 FROM documents WHERE chat_id = ?) AS has_documents
        """,
        (chat_id, chat_id),
    ).fetchone()
    conn.close()
    return bool(row["has_messages"] or row["has_documents"])


def get_visible_chats(user_id):
    conn = db()
    rows = conn.execute(
        """
        SELECT c.*
        FROM chats c
        WHERE c.user_id = ?
          AND (
              EXISTS(
                  SELECT 1 FROM messages m
                  WHERE m.chat_id = c.chat_id
              )
              OR
              EXISTS(
                  SELECT 1 FROM documents d
                  WHERE d.chat_id = c.chat_id
              )
          )
        ORDER BY c.updated_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def remove_empty_chat(chat_id, user_id):
    if chat_id and not chat_has_content(chat_id):
        delete_chat(chat_id, user_id)


def rename_chat(chat_id, user_id, new_title):
    """Rename a chat belonging to the current user."""
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE chats SET title = ? WHERE chat_id = ? AND user_id = ?",
                (new_title, chat_id, user_id),
            )
            conn.commit()
    except Exception:
        # Fall back to the existing update_chat implementation if available.
        try:
            update_chat(chat_id, user_id, new_title)
        except Exception:
            pass


def toggle_pin_chat(chat_id, user_id):
    """Toggle pinned state when the database supports it."""
    try:
        with get_db() as conn:
            cols = [
                row[1]
                for row in conn.execute("PRAGMA table_info(chats)").fetchall()
            ]
            if "pinned" in cols:
                current = conn.execute(
                    "SELECT COALESCE(pinned, 0) FROM chats WHERE chat_id = ? AND user_id = ?",
                    (chat_id, user_id),
                ).fetchone()
                value = 0 if current and current[0] else 1
                conn.execute(
                    "UPDATE chats SET pinned = ? WHERE chat_id = ? AND user_id = ?",
                    (value, chat_id, user_id),
                )
                conn.commit()
    except Exception:
        pass


def archive_chat(chat_id, user_id):
    """Archive a chat when the database supports an archived flag."""
    try:
        with get_db() as conn:
            cols = [
                row[1]
                for row in conn.execute("PRAGMA table_info(chats)").fetchall()
            ]
            if "archived" in cols:
                conn.execute(
                    "UPDATE chats SET archived = 1 WHERE chat_id = ? AND user_id = ?",
                    (chat_id, user_id),
                )
                conn.commit()
            else:
                # Without an archived column, leave the chat intact rather
                # than deleting it.
                pass
    except Exception:
        pass



def create_share_reference(chat_id, user_id):
    """Create a stable local share reference for a chat."""
    import hashlib
    raw = f"{user_id}:{chat_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ----------------------------------------------------------------
# SIDEBAR — CLEAN CHATGPT-STYLE
# ----------------------------------------------------------------
def sidebar(user):

    with st.sidebar:

        st.markdown(
            """
            <div class="sidebar-brand">
                <span>📚</span>
                <strong>DocuMind AI</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------
        # NEW CHAT
        # ---------------------------------------------------------
        if st.button(
            "✏️  New chat",
            key="new_chat_button",
            use_container_width=True,
        ):
            current_id = st.session_state.get("current_chat_id")

            # Remove an unused empty chat instead of accumulating
            # "New Chat" records.
            if current_id:
                remove_empty_chat(
                    current_id,
                    user["user_id"],
                )

            st.session_state.current_chat_id = create_chat(
                user["user_id"],
                title="New Chat",
            )

            reset_chat_state()
            st.rerun()

        st.markdown(
            "<div class='sidebar-divider'></div>",
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------
        # CHAT HISTORY
        # ---------------------------------------------------------
        st.markdown(
            "<div class='history-title'>Recent chats</div>",
            unsafe_allow_html=True,
        )

        chats = get_visible_chats(
            user["user_id"]
        )

        if not chats:
            st.markdown(
                """
                <div class="empty-history">
                    Your conversations will appear here.
                </div>
                """,
                unsafe_allow_html=True,
            )

        for chat in chats:

            chat_id = chat["chat_id"]
            title = chat["title"] or "New Chat"

            if len(title) > 34:
                title = title[:34] + "..."

            is_current = (
                chat_id
                ==
                st.session_state.current_chat_id
            )

            col_chat, col_menu = st.columns(
                [6.5, 1],
                gap="small",
            )

            with col_chat:

                label = (
                    "●  "
                    if is_current
                    else "   "
                ) + title

                if st.button(
                    label,
                    key=f"open_chat_{chat_id}",
                    use_container_width=True,
                ):

                    st.session_state.current_chat_id = chat_id
                    reset_chat_state()
                    st.rerun()

            with col_menu:

                # Single floating menu with only Share, Rename and Delete.
                with st.popover(
                    "⋯",
                    use_container_width=True,
                ):

                    if st.button(
                        "↗  Share",
                        key=f"share_{chat_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"share_chat_{chat_id}"] = True
                        st.rerun()

                    if st.button(
                        "✎  Rename",
                        key=f"rename_{chat_id}",
                        use_container_width=True,
                    ):
                        st.session_state[f"rename_chat_{chat_id}"] = True
                        st.rerun()

                    st.markdown(
                        '<div class="menu-divider"></div>',
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "Delete",
                        key=f"delete_chat_{chat_id}",
                        use_container_width=True,
                    ):
                        delete_chat(chat_id, user["user_id"])

                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                            reset_chat_state()

                        st.rerun()

            # ---------------------------------------------------------
            # CHAT ACTION PANELS
            # These are intentionally outside the narrow 3-dot column so
            # desktop sidebar layout does not squeeze the controls.
            # ---------------------------------------------------------

            if st.session_state.get(
                f"rename_chat_{chat_id}",
                False,
            ):

                with st.container():
                    st.markdown(
                        "<div class='rename-panel-title'>Rename chat</div>",
                        unsafe_allow_html=True,
                    )

                    new_title = st.text_input(
                        "Chat name",
                        value=title,
                        key=f"rename_input_{chat_id}",
                        label_visibility="collapsed",
                        placeholder="Chat name",
                    )

                    rename_col1, rename_col2 = st.columns(
                        [1, 1],
                        gap="small",
                    )

                    with rename_col1:
                        if st.button(
                            "Save",
                            key=f"save_rename_{chat_id}",
                            use_container_width=True,
                        ):
                            rename_chat(
                                chat_id,
                                user["user_id"],
                                new_title.strip() or "New Chat",
                            )
                            st.session_state[
                                f"rename_chat_{chat_id}"
                            ] = False
                            st.rerun()

                    with rename_col2:
                        if st.button(
                            "Cancel",
                            key=f"cancel_rename_{chat_id}",
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"rename_chat_{chat_id}"
                            ] = False
                            st.rerun()

            if st.session_state.get(
                f"share_chat_{chat_id}",
                False,
            ):

                with st.container():

                    token = create_share_link(
                        chat_id,
                        user["user_id"],
                    )

                    share_url = build_share_url(token)

                    st.markdown(
                        "<div class='share-panel-title'>Share conversation</div>",
                        unsafe_allow_html=True,
                    )

                    st.caption(
                        "Anyone with this link can view the whole conversation."
                    )

                    st.text_input(
                        "Share link",
                        value=share_url,
                        key=f"share_url_{chat_id}",
                        label_visibility="collapsed",
                    )

                    st.markdown(
                        "<div class='share-note'>"
                        "The link includes the complete chat history, "
                        "including your questions and DocuMind AI answers."
                        "</div>",
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "Close",
                        key=f"close_share_{chat_id}",
                    ):
                        st.session_state[
                            f"share_chat_{chat_id}"
                        ] = False
                        st.rerun()
# ---------------------------------------------------------
        # STUDY TOOLS
        # ---------------------------------------------------------
        st.markdown(
            "<div class='sidebar-divider'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='section-title'>🎯 Study tools</div>",
            unsafe_allow_html=True,
        )

        if st.button(
            "📝 Exam Mode",
            key="exam_tool",
            use_container_width=True,
        ):

            st.session_state.active_tool = "Exam Mode"
            st.session_state.exam_type = "Exam Mode"
            reset_chat_state()
            st.rerun()

        if st.button(
            "🧪 Mock Test",
            key="mock_tool",
            use_container_width=True,
        ):

            st.session_state.active_tool = "Mock Test"
            st.session_state.exam_type = "Mock Test"
            reset_chat_state()
            st.rerun()

        if st.button(
            "🃏 Flashcards",
            key="flashcard_tool",
            use_container_width=True,
        ):

            st.session_state.active_tool = "Flashcards"
            st.session_state.exam_type = "Flashcards"
            st.session_state.flashcards = []
            st.session_state.flashcard_index = 0
            st.rerun()

        if st.session_state.get("active_tool") != "Chat":
            if st.button(
                "← Back to Chat",
                key="back_to_chat_tool",
                use_container_width=True,
            ):
                st.session_state.active_tool = "Chat"
                st.session_state.exam_type = "Chat"
                reset_chat_state()
                st.rerun()

        # ---------------------------------------------------------
        # PROFILE
        # ---------------------------------------------------------
        st.markdown(
            "<div class='profile-spacer'></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='sidebar-divider'></div>",
            unsafe_allow_html=True,
        )

        profile_col1, profile_col2 = st.columns(
            [1, 4],
            gap="small",
        )

        with profile_col1:

            if user.get("picture"):

                st.image(
                    user["picture"],
                    width=40,
                )

            else:

                initial = (
                    user.get("name") or "U"
                )[:1].upper()

                st.markdown(
                    f"<div class='avatar'>{initial}</div>",
                    unsafe_allow_html=True,
                )

        with profile_col2:

            st.markdown(
                f"""
                <div class="profile-name">
                    {user.get("name", "User")}
                </div>
                <div class="profile-email">
                    {user.get("email", "")}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # IMPORTANT:
        # The widget key is account_button, while the state key is
        # show_account_menu. This avoids Streamlit's session-state
        # mutation error.
        if "show_account_menu" not in st.session_state:

            st.session_state.show_account_menu = False

        def toggle_account_menu():

            st.session_state.show_account_menu = (
                not st.session_state.show_account_menu
            )

        st.button(
            ":material/person_outline:  Account",
            key="account_button",
            use_container_width=True,
            on_click=toggle_account_menu,
        )

        if st.session_state.show_account_menu:

            st.caption(
                user.get("email", "")
            )

            if st.button(
                "🚪 Log out",
                key="logout_button",
                use_container_width=True,
            ):

                st.logout()



def unique_sources(sources):
    """Remove duplicate source entries while preserving order."""
    seen = set()
    result = []

    for source in sources or []:
        if isinstance(source, dict):
            value = (
                source.get("source")
                or source.get("file_name")
                or source.get("name")
                or str(source)
            )
        else:
            value = str(source)

        key = value.strip()
        if not key or key in seen:
            continue

        seen.add(key)
        result.append(source)

    return result


# ----------------------------------------------------------------
# CHAT DISPLAY
# ----------------------------------------------------------------
def render_assistant_message(content, message_key="message"):
    """
    Render an assistant message with compact, collapsed sources.

    Older saved messages may contain:
        **📌 Sources**
        - file, page N

    We keep that data but render it like ChatGPT: a small collapsed
    Sources row instead of a large block taking up the conversation.
    """
    if not content:
        return

    marker = "**📌 Sources**"
    if marker not in content:
        st.markdown(content)
        return

    answer, source_text = content.split(marker, 1)
    answer = answer.rstrip()
    source_lines = [
        line.strip()
        for line in source_text.splitlines()
        if line.strip() and line.strip() != "---"
    ]

    if answer:
        st.markdown(answer)

    # Compact source control. It stays collapsed so it does not consume
    # conversation space unless the user wants to inspect the citations.
    label = (
        f"Sources · {len(source_lines)}"
        if source_lines
        else "Sources"
    )

    with st.expander(
        label,
        expanded=False,
    ):
        if source_lines:
            for line in source_lines:
                # Remove the markdown bullet because the expander itself
                # provides the compact list spacing.
                clean = re.sub(r"^[-*]\s*", "", line)
                st.markdown(
                    f"<div class='compact-source'>{clean}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No source details available.")


def display_chat(chat_id):

    messages = get_messages(chat_id)

    for index, m in enumerate(messages):

        with st.chat_message(
            m["role"]
        ):

            if m["role"] == "assistant":
                render_assistant_message(
                    m["content"],
                    message_key=f"{chat_id}_{index}",
                )
            else:
                st.markdown(
                    m["content"]
                )


# ----------------------------------------------------------------
# CHAT TAB
# ----------------------------------------------------------------
def chat_tab(chat_id, user):

    messages = get_messages(chat_id)

    if not messages and not has_faiss(chat_id):

        st.markdown(
            """
            <div style="
                text-align:center;
                padding:80px 20px 30px 20px;
            ">
                <h2>How can I help you study?</h2>
                <p>
                    Ask a question or attach a PDF
                    using the 📌 button in the message box.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Existing conversation.
    # Keep the conversation above the composer. The composer is rendered
    # after the history so newly submitted messages never appear below it.
    st.markdown(
        '<div class="documind-chat-history">',
        unsafe_allow_html=True,
    )

    display_chat(chat_id)

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------
    # ChatGPT-style input.
    #
    # The attachment button is built into st.chat_input by
    # accept_file. This removes the need for a sidebar uploader.
    # -------------------------------------------------------------
    question_input = st.chat_input(
        "Message DocuMind AI...",
        accept_file="multiple",
        file_type=["pdf"],
        key=f"chat_input_{chat_id}",
    )

    if not question_input:
        return

    question = (
        getattr(question_input, "text", "")
        or ""
    ).strip()

    attached_files = (
        getattr(question_input, "files", [])
        or []
    )

    # -------------------------------------------------------------
    # PROCESS ATTACHED PDFS
    # -------------------------------------------------------------
    if attached_files:

        try:

            with st.spinner(
                "Processing PDF..."
            ):

                chunks, pages = process_pdfs(
                    attached_files,
                    chat_id,
                )

            # Show the uploaded files inside the conversation.
            with st.chat_message("user"):

                for attached_file in attached_files:

                    st.markdown(
                        f"📌 **{attached_file.name}**"
                    )

                if question:

                    st.markdown(
                        question
                    )

            st.toast(
                f"📌 {len(attached_files)} PDF(s) added to this chat."
            )

        except Exception as e:

            st.error(
                f"Could not process PDF: {e}"
            )

            return

    # -------------------------------------------------------------
    # FILE-ONLY MESSAGE
    # -------------------------------------------------------------
    if not question:

        # A file-only submission is valid.
        if attached_files:

            update_chat(
                chat_id,
                user["user_id"],
            )

        return

    # -------------------------------------------------------------
    # SAVE QUESTION
    # -------------------------------------------------------------
    save_message(
        chat_id,
        "user",
        question,
    )

    # -------------------------------------------------------------
    # AUTOMATIC CHAT TITLE
    # -------------------------------------------------------------
    messages = get_messages(chat_id)

    user_message_count = len(
        [
            m
            for m in messages
            if m["role"] == "user"
        ]
    )

    if user_message_count == 1:

        title = question[:55]

        if len(question) > 55:

            title += "..."

        update_chat(
            chat_id,
            user["user_id"],
            title,
        )

    # -------------------------------------------------------------
    # QUESTION
    #
    # If a PDF was attached, it has already been displayed above.
    # Otherwise display the question normally.
    # -------------------------------------------------------------
    if not attached_files:

        with st.chat_message(
            "user"
        ):

            st.markdown(
                question
            )

    # -------------------------------------------------------------
    # ANSWER
    # -------------------------------------------------------------
    with st.chat_message(
        "assistant"
    ):

        try:

            with st.spinner(
                "Thinking..."
            ):

                answer = answer_question(
                    chat_id,
                    question,
                )

            if answer == "NO_DOCUMENT":

                answer = (
                    "📄 Please attach and process "
                    "a PDF before asking document questions."
                )

            elif answer == "ANSWER_NOT_FOUND":

                answer = (
                    "I couldn't find the answer "
                    "in the uploaded documents.\n\n"
                    "You can use the **General Knowledge** "
                    "option below."
                )

                st.session_state.pending_fallback = (
                    question
                )

            if answer not in ("NO_DOCUMENT", "ANSWER_NOT_FOUND"):
                render_assistant_message(
                    answer,
                    message_key=f"live_{chat_id}_{uuid.uuid4().hex[:8]}",
                )
            else:
                st.markdown(answer)

            save_message(
                chat_id,
                "assistant",
                answer,
            )

            update_chat(
                chat_id,
                user["user_id"],
            )

        except Exception as e:

            st.error(
                f"Error: {e}"
            )


# ----------------------------------------------------------------
# EXAM UI
# ----------------------------------------------------------------
def exam_ui(chat_id, user, mock=False):
    title = "🧪 Mock Test" if mock else "🎯 Exam Mode"
    st.subheader(title)

    if not st.session_state.exam_questions:
        col1, col2 = st.columns(2)

        with col1:
            count = st.selectbox(
                "Number of questions",
                [5, 10, 15, 20],
                index=1,
                key=f"question_count_{chat_id}_{'mock' if mock else 'exam'}",
            )
            difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        index=1,
        key=f"difficulty_{chat_id}_{'mock' if mock else 'exam'}",
    )

        with col2:
            topic = st.text_input(
                "Topic (optional)",
                placeholder="e.g. Machine Learning",
                key=f"topic_{chat_id}_{'mock' if mock else 'exam'}",
            )
            duration = st.selectbox(
                "Time limit",
                [5, 10, 15, 20, 30],
                index=1,
                key=f"duration_{chat_id}_mock",
            ) if mock else None

        if st.button(
            "🚀 Start Mock Test" if mock else "🚀 Generate Exam",
            type="primary"
        ):
            try:
                with st.spinner("Generating questions from your PDF..."):
                    questions = generate_mcqs(
                        chat_id,
                        count,
                        difficulty,
                        topic
                    )

                st.session_state.exam_questions = questions
                st.session_state.exam_answers = {}
                st.session_state.exam_submitted = False

                if mock:
                    st.session_state.mock_duration = duration
                    st.session_state.mock_start_time = datetime.now().timestamp()
                    st.session_state.mock_started = True

                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

        return

    # Timer display for mock tests.
    if mock and st.session_state.mock_started and not st.session_state.exam_submitted:
        elapsed = int(datetime.now().timestamp() - st.session_state.mock_start_time)
        remaining = max(0, st.session_state.mock_duration * 60 - elapsed)
        mins, secs = divmod(remaining, 60)
        st.warning(f"⏱️ Time remaining: **{mins:02d}:{secs:02d}**")
        if remaining == 0:
            st.warning("Time is up. Submit your test now.")

    for i, q in enumerate(st.session_state.exam_questions):
        st.markdown(f"### Question {i + 1}")
        st.write(q["question"])

        choice = st.radio(
            "Choose one:",
            q["options"],
            index=None,
            key=f"answer_{chat_id}_{'mock' if mock else 'exam'}_{i}",
            disabled=st.session_state.exam_submitted,
        )

        if choice is not None:
            st.session_state.exam_answers[i] = q["options"].index(choice)

    if not st.session_state.exam_submitted:
        if st.button(
            "✅ Submit Test",
            type="primary",
            key=f"submit_test_{chat_id}_{'mock' if mock else 'exam'}",
        ):
            score = 0
            weak = {}

            for i, q in enumerate(st.session_state.exam_questions):
                selected = st.session_state.exam_answers.get(i)
                topic = q.get("topic", "General")
                if selected == q["answer"]:
                    score += 1
                else:
                    weak[topic] = weak.get(topic, 0) + 1

            st.session_state.exam_submitted = True

            save_test_result(
                user["user_id"],
                chat_id,
                "Mock Test" if mock else "Exam Mode",
                score,
                len(st.session_state.exam_questions),
                weak
            )

            st.rerun()

    else:
        score = 0
        weak = {}

        for i, q in enumerate(st.session_state.exam_questions):
            selected = st.session_state.exam_answers.get(i)
            correct = q["answer"]

            if selected == correct:
                score += 1
            else:
                topic = q.get("topic", "General")
                weak[topic] = weak.get(topic, 0) + 1

        percentage = round(score / len(st.session_state.exam_questions) * 100)

        st.divider()
        st.success(
            f"🏆 Score: **{score}/{len(st.session_state.exam_questions)} ({percentage}%)**"
        )

        if weak:
            st.warning("📌 Topics to improve:")
            for topic, mistakes in sorted(
                weak.items(), key=lambda x: x[1], reverse=True
            ):
                st.write(f"- **{topic}** — {mistakes} incorrect")

        for i, q in enumerate(st.session_state.exam_questions):
            selected = st.session_state.exam_answers.get(i)
            correct = q["answer"]

            if selected == correct:
                st.success(f"Question {i + 1}: Correct ✅")
            else:
                st.error(
                    f"Question {i + 1}: Incorrect ❌ — "
                    f"Correct answer: {q['options'][correct]}"
                )

            st.caption(q.get("explanation", ""))

        if st.button(
            "🔄 Create New Test",
            key=f"new_test_{chat_id}_{'mock' if mock else 'exam'}",
        ):
            st.session_state.exam_questions = []
            st.session_state.exam_answers = {}
            st.session_state.exam_submitted = False
            st.session_state.mock_started = False
            st.rerun()


# ----------------------------------------------------------------
# FLASHCARD UI
# ----------------------------------------------------------------
def flashcard_ui(chat_id):
    st.subheader("🃏 AI Flashcards")

    if not st.session_state.flashcards:
        col1, col2 = st.columns(2)
        with col1:
            count = st.selectbox(
        "Number of cards",
        [5, 10, 15, 20],
        index=1,
        key=f"flashcard_count_{chat_id}",
    )
        with col2:
            topic = st.text_input("Topic (optional)", key="flashcard_topic")

        if st.button("✨ Generate Flashcards", type="primary"):
            try:
                with st.spinner("Creating flashcards..."):
                    st.session_state.flashcards = generate_flashcards(
                        chat_id, count, topic
                    )
                st.session_state.flashcard_index = 0
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        return

    idx = st.session_state.flashcard_index
    card = st.session_state.flashcards[idx]

    st.caption(f"Card {idx + 1} of {len(st.session_state.flashcards)}")

    st.markdown(
        f"""
        <div style="
            border:1px solid #888;
            border-radius:15px;
            padding:30px;
            min-height:220px;
        ">
        <h3>❓ {card['front']}</h3>
        <hr>
        <p><b>💡 Answer:</b> {card['back']}</p>
        <p><i>Topic: {card.get('topic','General')}</i></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⬅️ Previous", disabled=idx == 0):
            st.session_state.flashcard_index -= 1
            st.rerun()
    with c2:
        if st.button("🔀 Shuffle"):
            import random
            random.shuffle(st.session_state.flashcards)
            st.session_state.flashcard_index = 0
            st.rerun()
    with c3:
        if st.button(
            "Next ➡️",
            disabled=idx == len(st.session_state.flashcards) - 1
        ):
            st.session_state.flashcard_index += 1
            st.rerun()


# ----------------------------------------------------------------
# PERFORMANCE DASHBOARD
# ----------------------------------------------------------------
def dashboard(user_id):
    st.subheader("📊 My Performance")

    results = get_test_results(user_id)

    if not results:
        st.info("Complete an Exam Mode or Mock Test to see your performance.")
        return

    total_score = sum(r["score"] for r in results)
    total_questions = sum(r["total"] for r in results)
    avg = round(total_score / total_questions * 100) if total_questions else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Tests Completed", len(results))
    c2.metric("Average Score", f"{avg}%")
    c3.metric("Questions Answered", total_questions)

    weak_topics = {}
    for result in results:
        try:
            data = json.loads(result["weak_topics"])
        except Exception:
            data = {}
        for topic, count in data.items():
            weak_topics[topic] = weak_topics.get(topic, 0) + count

    if weak_topics:
        st.markdown("### 📌 Weak Topics")
        for topic, count in sorted(
            weak_topics.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            st.write(f"- **{topic}** — {count} mistakes")

    st.markdown("### 📝 Recent Tests")
    for result in results[:10]:
        percentage = round(result["score"] / result["total"] * 100)
        st.write(
            f"**{result['test_type']}** — "
            f"{result['score']}/{result['total']} ({percentage}%) — "
            f"{result['created_at'][:16].replace('T',' ')}"
        )


# ----------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------
def main():
    init_db()

    # A share link is public/read-only. It must be checked before
    # authentication so a recipient can view the conversation without
    # logging into the owner's account.
    share_token = st.query_params.get("share")

    if share_token:
        render_shared_conversation(share_token)
        st.stop()

    if not st.user.is_logged_in:
        login_screen()
        st.stop()

    init_state()

    user = current_user()
    save_user(user)

    # Ensure a valid current chat.
    if st.session_state.current_chat_id:
        if not get_chat(st.session_state.current_chat_id, user["user_id"]):
            st.session_state.current_chat_id = None

    if not st.session_state.current_chat_id:
        chats = get_visible_chats(user["user_id"])
        if chats:
            st.session_state.current_chat_id = chats[0]["chat_id"]
        else:
            st.session_state.current_chat_id = create_chat(user["user_id"])

    sidebar(user)

    chat = get_chat(
        st.session_state.current_chat_id,
        user["user_id"]
    )

    if not chat:
        st.error("Unable to open this chat.")
        st.stop()

    st.title(f"📚 {chat['title']}")

    # ---------------------------------------------------------
    # MAIN VIEW ROUTER
    # Sidebar study tools open their actual screens.
    # ---------------------------------------------------------

    active_tool = st.session_state.get("active_tool", "Chat")

    if active_tool == "Exam Mode":
        exam_ui(
            st.session_state.current_chat_id,
            user,
            mock=False,
        )
        return

    if active_tool == "Mock Test":
        exam_ui(
            st.session_state.current_chat_id,
            user,
            mock=True,
        )
        return

    if active_tool == "Flashcards":
        flashcard_ui(
            st.session_state.current_chat_id,
        )
        return

    # Default Chat screen.
    st.title(f"📚 {chat['title']}")

    display_chat(st.session_state.current_chat_id)
    chat_tab(
        st.session_state.current_chat_id,
        user,
    )




if __name__ == "__main__":
    main()

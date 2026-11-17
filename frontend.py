import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Zephyr AI ",
    page_icon="✨",
    layout="centered",
)

# --- CUSTOM CSS FOR BUTTER YELLOW & WARM BROWN THEME ---
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Warm cream chat message cards with subtle honey border */
    [data-testid="stChatMessage"] {
        background-color: #FFFDF5;
        border: 1px solid #E8D89C;
        border-radius: 16px;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(30, 27, 24, 0.04);
    }
    
    /* Warm Coffee Brown gradient title */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #6B4226, #A06535);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        color: #5C5346;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_pdf" not in st.session_state:
    st.session_state.active_pdf = None

# --- SIDEBAR: KNOWLEDGE BASE & CONTROLS ---
with st.sidebar:
    st.markdown("### 📂 Document Knowledge Base")
    if st.session_state.active_pdf:
        st.success(f"Active: **{st.session_state.active_pdf}**")
    else:
        st.info("No PDF loaded yet. Upload notes or a resume below.")  # <-- Indented properly
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], label_visibility="collapsed")
    if uploaded_file and st.button("⚡ Process & Index PDF", use_container_width=True):
        with st.spinner("Extracting knowledge..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            res = requests.post(f"{BACKEND_URL}/upload-pdf", files=files)
            if res.status_code == 200:
                st.session_state.active_pdf = uploaded_file.name
                st.rerun()
            else:
                st.error("Failed to process PDF.")

    st.divider()
    st.markdown("### 🛠️ Built-In Agent Tools")
    st.caption("• **PDF Semantic QA** (Reads uploaded docs)\n• **SGPA Calculator** (Executes Python tool)")
    
    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MAIN HEADER ---
st.markdown('<div class="hero-title">✨ Nexus AI Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Your personal CSE study companion, document analyst, and academic tool agent.</div>',
    unsafe_allow_html=True,
)

# --- STARTER PROMPT SUGGESTIONS (Shown when chat is empty) ---
selected_suggestion = None
if not st.session_state.messages:
    st.markdown("**Try asking:**")
    suggestions = [
        "📄 Summarize my uploaded PDF in 5 bullet points",
        "🎓 Calculate SGPA for 4, 4, 3, 2 credits with 9, 8, 10, 9 grades",
        "💡 Explain Dynamic Programming vs Greedy Algorithms simply",
    ]
    selected_suggestion = st.pills("Suggestions", suggestions, label_visibility="collapsed")

# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else "✨"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# --- HANDLE USER INPUT (From typing OR clicking a suggestion pill) ---
user_input = st.chat_input("Message Nexus AI...") or selected_suggestion

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Thinking..."):
            res = requests.post(f"{BACKEND_URL}/chat", json={"message": user_input})
            if res.status_code == 200:
                answer = res.json().get("reply", "Error getting response.")
            else:
                answer = f"Backend error ({res.status_code}): Check your backend terminal."
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
    
    # Rerun if triggered by a pill so the pill disappears cleanly once chat starts
    if selected_suggestion:
        st.rerun()
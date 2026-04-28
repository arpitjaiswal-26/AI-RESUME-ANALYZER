import streamlit as st
import re
from groq import Groq
from PyPDF2 import PdfReader
from database import save_result, get_history, clear_history
import sqlite3
import bcrypt


# ---------- SESSION STATE ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "plan" not in st.session_state:
    st.session_state.plan = "Free"

if "usage" not in st.session_state:
    st.session_state.usage = 0

if "limit" not in st.session_state:
    st.session_state.limit = 10

if "history" not in st.session_state:
    st.session_state.history = []

# ---------- DATABASE ----------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()
def create_user(username, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        c.execute("INSERT INTO users VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login_user(username, password):
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    data = c.fetchone()

    if data:
        stored_password = data[0]

        # ✅ FIX: handle both string + bytes
        if isinstance(stored_password, str):
            stored_password = stored_password.encode()

        if bcrypt.checkpw(password.encode(), stored_password):
            return True

    return False

def read_pdf(file):
    text = ""
    pdf = PdfReader(file)
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

# ---------- CONFIG ----------
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
st.markdown("""
<style>

/* ===== BACKGROUND ===== */
body {
    background-color: #0E1117;
    color: #E6EDF3;
}

/* ===== MAIN CONTAINER ===== */
.block-container {
    padding-top: 2rem;
}

/* ===== HEADINGS ===== */
h1, h2, h3 {
    color: #FFFFFF;
}

/* ===== CARDS (premium glass look) ===== */
.css-1d391kg, .stMarkdown, .stTextInput, .stTextArea {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 12px;
}

/* ===== RADIO BUTTON CONTAINER ===== */
div[role="radiogroup"] {
    background: rgba(0, 255, 198, 0.05);
    padding: 12px;
    border-radius: 12px;
    border: 1px solid rgba(0,255,198,0.2);
}

/* ===== RADIO OPTIONS ===== */
div[role="radiogroup"] label {
    background: #161B22;
    padding: 10px 15px;
    margin: 5px 0;
    border-radius: 8px;
    transition: 0.3s;
    border: 1px solid transparent;
}

/* ===== HOVER EFFECT ===== */
div[role="radiogroup"] label:hover {
    border: 1px solid #00FFC6;
    box-shadow: 0px 0px 10px #00FFC6;
}

/* ===== SELECTED OPTION (NEON) ===== */
div[role="radiogroup"] input:checked + div {
    color: #00FFC6;
    font-weight: bold;
}

/* ===== STRONG NEON GLOW ON SELECT ===== */
div[role="radiogroup"] input:checked + div {
    text-shadow: 0px 0px 10px #00FFC6;
}

/* ===== BUTTON ===== */
.stButton > button {
    background: linear-gradient(90deg, #00FFC6, #00BFFF);
    color: black;
    border-radius: 10px;
    border: none;
    font-weight: bold;
    transition: 0.3s;
}

.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 15px #00FFC6;
}

/* ===== SUCCESS (Detected Skills) ===== */
.stSuccess {
    background-color: rgba(0, 255, 150, 0.15);
    color: #00FF9C;
    border-radius: 8px;
}

/* ===== ERROR (Missing Skills) ===== */
.stError {
    background-color: rgba(255, 80, 80, 0.15);
    color: #FF4D4D;
    border-radius: 8px;
}

/* ===== PROGRESS BAR ===== */
div[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #00FFC6, #00BFFF);
    box-shadow: 0px 0px 10px #00FFC6;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background-color: #161B22;
}

/* ===== INPUT BOX ===== */
textarea, input {
    background-color: #161B22 !important;
    color: #E6EDF3 !important;
}

/* ===== METRIC TEXT ===== */
.css-1xarl3l {
    color: #00FFC6;
}

</style>
""", unsafe_allow_html=True) 

# ---------- LOGIN SYSTEM ----------


# Initialize session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------- LOGIN UI ----------
menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if not st.session_state.logged_in:

    if choice == "Login":
        st.title("🔐 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login_user(username.strip(), password.strip()):
                st.session_state.logged_in = True
                st.session_state.user = username
                st.session_state.user = username
                st.session_state.plan = "Free"
                st.session_state.usage = 0
                st.rerun()
            else:
                st.error("❌ Invalid credentials")

    elif choice == "Signup":
        st.title("📝 Create Account")

        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Create Account"):
            if create_user(new_user.strip(), new_pass.strip()):
                st.success("✅ Account created")
            else:
                st.error("⚠️ User already exists")

    st.stop()

with st.sidebar:

    st.markdown("## 👤 Profile")

    st.image("https://www.simpleimageconvert.com/images/default/profile.jpg", width=80)
    st.markdown(f"**{st.session_state.user}**")

    if st.session_state.plan == "Pro":
        st.success("🟢 Pro Plan")
    else:
        st.warning("🟡 Free Plan")

    usage = st.session_state.usage
    limit = st.session_state.limit

    st.markdown("### ⚡ Usage")
    st.progress(usage / limit)
    st.caption(f"{usage} / {limit} analyses used")

    st.markdown("---")

    # ✅ ONLY ONE LOGOUT
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.markdown("---")

    # ✅ DATABASE HISTORY
    st.markdown("## 📜 History")
    for score, summary in get_history(st.session_state.user):
        st.write(f"⭐ {round(score,2)}")
        st.caption(summary)
        st.markdown("---")

    if st.button("🗑 Clear History", key="clear_history_btn"):
        clear_history(st.session_state.user)
        st.rerun()
# ✅ ADD HERE
API_KEY = st.secrets.get("GROQ_API_KEY")

if not API_KEY:
    st.error("❌ GROQ API key missing")
    st.stop()
    

client = Groq(api_key=API_KEY)

# ---------- SUMMARIZER ----------
def summarize_text(text):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict resume analyzer. Be concise."
                },
                {
                    "role": "user",
                    "content": f"""
Summarize this resume in STRICT format:

- Maximum 5 bullet points
- Each bullet = max 12 words
- No extra explanation
- Total output must be SHORTER than input

Then give:

Strengths (3 points max)
Weaknesses (3 points max)
Missing Skills (5 max)

Resume:
{text[:1500]}
"""
                }
            ],
            temperature=0.3,
            max_tokens=300   # 🔥 LIMIT OUTPUT
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ {str(e)}"


# ---------- SKILLS ----------
skills = {
    "python": ["python"],
    "machine learning": ["machine learning", "ml"],
    "deep learning": ["deep learning", "dl"],
    "nlp": ["nlp", "natural language processing"],
    "pytorch": ["pytorch", "torch"],
    "data analysis": ["data analysis", "analytics"],
    "tensorflow": ["tensorflow"],
    "sql": ["sql"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "c++": ["c++"]
}

weights = {
    "python": 2,
    "machine learning": 3,
    "deep learning": 3,
    "nlp": 2,
    "pytorch": 2,
    "data analysis": 2,
    "tensorflow": 2,
    "sql": 1,
    "pandas": 2,
    "numpy": 2,
    "c++": 2
}

# ---------- KEYWORD EXTRACT ----------
def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    stop = {"the","and","is","in","to","for","of","a","with","on","at","by"}
    return list(set(w for w in words if w not in stop and len(w) > 3))

roles = {
    "Machine Learning": ["python", "ml", "deep learning", "nlp", "tensorflow", "pytorch"],
    "Web Developer": ["html", "css", "javascript", "react", "node", "sql"],
    "Data Analyst": ["python", "sql", "pandas", "numpy", "excel", "data analysis"]
}
# ---------- UI ----------
st.markdown("<h1>🚀 AI Resume Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>AI-powered resume analysis + job matching</p>", unsafe_allow_html=True)

# 🎯 Role selection
st.markdown("### 🎯 Select Target Role")
selected_role = st.selectbox("", list(roles.keys()))

# 📄 INPUT SECTION (FIXED UI)
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📄 Resume Input")
    input_type = st.radio("Choose input method", ["Paste Text", "Upload PDF"])

    if input_type == "Paste Text":
        resume = st.text_area("Paste Resume", height=250)
    else:
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

        if uploaded_file:
            resume = read_pdf(uploaded_file)
            if not resume.strip():
                st.error("❌ Could not extract text from PDF")
                st.stop()
            st.success("✅ PDF Loaded")
        else:
            resume = None

with col2:
    st.markdown("### 🎯 Job Description")
    job_desc = st.text_area("Paste Job Description (Optional)", height=250)

# ---------- ANALYZE ----------
if st.session_state.usage >= st.session_state.limit:
    st.error("🚫 Usage limit reached. Upgrade to Pro.")
    st.stop()
analyze = st.button("🚀 Analyze Resume", use_container_width=True)
if analyze:

    if not resume or len(resume) < 50:
        st.warning("⚠️ Enter or upload resume")
        st.stop()

    resume = resume[:2000]

    with st.spinner("🤖 AI is analyzing your resume..."):
        final_summary = summarize_text(resume)

    # ✅ SHOW SUMMARY FIRST (IMPORTANT)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📌 Summary")
    st.markdown(final_summary[:800])
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    resume_lower = resume.lower()

    # ---------- SKILLS ----------
    found = [
        skill for skill, variants in skills.items()
        if any(v in resume_lower for v in variants)
    ]

    missing = [s for s in skills if s not in found]

    # ---------- UI ----------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Detected Skills")
       
        for s in found:
            st.success(s)
        

    with col2:
        st.markdown("### ❌ Missing Skills")
         
        for s in missing:
            st.error(s)
        
     

     
    role_keywords = roles[selected_role]

    role_score = sum(1 for skill in role_keywords if skill in resume_lower)
    role_percent = (role_score / len(role_keywords)) * 100

    st.markdown(f"### 🎯 {selected_role} Match")
    st.progress(role_percent / 100)
    st.success(f"{round(role_percent,2)}% match")




    # ---------- ATS SCORE ----------
    ats_score = 0

    ats_score += (len(found) / len(skills)) * 4

    if len(resume) > 500:
        ats_score += 2

    sections = ["education", "project", "experience", "skills"]
    ats_score += sum(1 for sec in sections if sec in resume_lower) * 0.5

    action_words = ["developed", "built", "created", "designed"]
    ats_score += sum(1 for word in action_words if word in resume_lower) * 0.5

    ats_score = min(ats_score, 10)

    report = f"""RESUME ANALYSIS REPORT
    Score: {round(ats_score,2)}/10

    Summary:
    {final_summary}

    Detected Skills:
    {', '.join(found)}

    Missing Skills:
    {', '.join(missing)}
    """

    st.download_button(
    "📄 Download Report",
    report,
    file_name="resume_report.txt"
    )
 # ✅ STORE RESULT (only once per click)
    if "last" not in st.session_state:
       st.session_state.last = ""
    save_result(st.session_state.user, ats_score, final_summary[:200])
    if st.session_state.last != resume:
        
        st.session_state.last = resume
        st.session_state.usage += 1

    st.markdown("## 📊 ATS Score")
    st.progress(ats_score / 10) 
    st.markdown(f"### ⭐ {round(ats_score,2)} / 10")

# ---------- JOB MATCH ----------
    if len(job_desc) > 20:

        job_lower = job_desc.lower()

        job_skills = [
            s for s, v in skills.items()
            if any(x in job_lower for x in v)
        ]

        job_kw = extract_keywords(job_desc)
        res_kw = extract_keywords(resume)

        matched = list(set(job_skills + [k for k in job_kw if k in res_kw]))

        total_items = len(set(job_skills + job_kw))
        percent = (len(matched) / total_items) * 100 if total_items else 0

        missing_job = [s for s in job_skills if s not in found]

        st.markdown("---")
        st.markdown("## 🎯 Job Match")

        st.metric("Match %", f"{round(percent,2)}%")
        st.progress(percent / 100)

        st.markdown("### ✅ Matched Keywords")
        st.success(", ".join(matched) if matched else "None")

        st.markdown("### ❌ Missing for Job")
        for s in missing_job:
            st.error(s)

    else:
        st.info("💡 Add job description for matching")
 
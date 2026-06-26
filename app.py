import streamlit as st
import sqlite3
import hashlib


DB_FILE = "linkedin_bot.db"

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Passwords for demo: admin123 and employee123
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        emp_hash = hashlib.sha256("employee123".encode()).hexdigest()
        
        cursor.execute("INSERT INTO users (email, password_hash, is_admin) VALUES (?, ?, ?)", 
                       ("admin@company.com", admin_hash, 1))
        cursor.execute("INSERT INTO users (email, password_hash, is_admin) VALUES (?, ?, ?)", 
                       ("employee@company.com", emp_hash, 0))
        conn.commit()
    conn.close()

def verify_user(email, password):
    """Verifies user credentials and returns (is_logged_in, is_admin)."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    cursor.execute("SELECT is_admin FROM users WHERE email = ? AND password_hash = ?", (email, password_hash))
    result = cursor.fetchone()
    conn.close()
    
    if result is not None:
        return True, bool(result[0])
    return False, False

# Initialize the DB on startup
init_db()

# ==========================================
# 2. STREAMLIT SESSION STATE MANAGEMENT
# ==========================================

st.set_page_config(page_title="AI LinkedIn Content Bot", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

def handle_login():
    email = st.session_state.login_email
    password = st.session_state.login_password
    
    success, is_admin = verify_user(email, password)
    if success:
        st.session_state.logged_in = True
        st.session_state.is_admin = is_admin
        st.session_state.user_email = email
        st.success("Logged in successfully!")
    else:
        st.error("❌ Invalid email or password.")

def handle_logout():
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.user_email = ""
    st.rerun()

# ==========================================
# 3. RENDER LOGIN SCREEN
# ==========================================

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🚀 AI LinkedIn Content Bot</h1>", unsafe_html=True)
    st.markdown("<p style='text-align: center;'>Internal Corporate Access Portal</p>", unsafe_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    
    with col_login:
        st.write("---")
        st.text_input("Email Address", key="login_email", placeholder="name@company.com")
        st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        st.button("Sign In", on_click=handle_login, type="primary", use_container_width=True)
        st.write("---")
        st.info(
            "💡 **Demo Accounts Generated:**\n\n"
            "* **Admin:** `admin@company.com` (Password: `admin123`)\n"
            "* **Employee:** `employee@company.com` (Password: `employee123`)"
        )
    st.stop()

st.set_page_config(page_title="AI LinkedIn Content Bot", layout="wide")
st.title("AI LinkedIn Content Creation Bot")

tab1, tab2 = st.tabs(["👤 User Dashboard", "⚙️ Admin Settings"])

with tab2:
    st.header("Company Brand Configuration")
    brand_statement = st.text_area("Brand Positioning Statement", "Enter your company's core mission...")
    pillars = st.text_area("Key Messaging Pillars", "E.g., Innovation, Scalability, Sustainability")
    style = st.selectbox("Writing Style Preference", ["McKinsey-style insight driven", "Executive voice", "Personal storytelling"])
    avoid_words = st.text_input("Words to Avoid (comma separated)", "disruptive, synergy, ecosystem")
    logo = st.file_uploader("Upload Company Logo", type=["png", "jpg", "jpeg"])
    
    if st.button("Save Guidelines"):
        st.success("Brand guidelines saved successfully! (Mocked for now)")

with tab1:
    st.header("Generate LinkedIn Content")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        topic = st.text_area("What is the post about?", placeholder="e.g., AI adoption in enterprise procurement")
        
        content_type = st.selectbox("Content Type", ["POV / Opinion", "Industry Insight", "Thought Leadership", "Trend Commentary", "Company Update", "Leadership Reflection"])
        audience = st.selectbox("Target Audience", ["CXO", "HR Leaders", "CIOs", "Marketers"])
        tone = st.selectbox("Tone", ["Professional", "Conversational", "Bold"])
        industry = st.selectbox("Industry", ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing"])
        length = st.selectbox("Length", ["Short", "Medium", "Long"])
        
        cta = st.text_input("Call to Action (Optional)", placeholder="e.g., Click the link below to read our full whitepaper")
        
        generate_btn = st.button("Generate Drafts", type="primary")

    with col2:
        st.subheader("Generated Output")
        if generate_btn:
            st.info(f"Generating a {tone} {content_type} post about '{topic}' for {audience}...")
            
            # Placeholders for Day 4 & 5
            st.markdown("### Draft Post")
            st.code("This is a placeholder where your AI-generated text will appear on Day 4.", language="markdown")
            
            st.markdown("### Infographic Spec")
            st.code("Title: [AI Title]\n- Insight 1\n- Insight 2\n- Insight 3", language="markdown")
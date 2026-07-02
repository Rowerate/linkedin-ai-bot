import streamlit as st
import sqlite3
import hashlib
import os
from dotenv import load_dotenv
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
from artist import generate_hf_image
from PIL import Image
import io
from supabase import create_client, Client

load_dotenv()

llm_endpoint = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-3.1-8B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    temperature=0.7
)

llm = ChatHuggingFace(llm=llm_endpoint)

st.set_page_config(page_title="AI LinkedIn Content Bot", layout="wide")

# ==========================================
# 1. SUPABASE CLOUD SETUP & UTILITIES 
# ==========================================

# Initialize Supabase Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

llm_endpoint = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-3.1-8B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    temperature=0.7
)

llm = ChatHuggingFace(llm=llm_endpoint)

st.set_page_config(page_title="AI LinkedIn Content Bot", layout="wide")

def get_system_prompt():
    """Fetches the current master system prompt from the cloud database."""
    response = supabase.table("brand_settings").select("system_prompt").eq("id", 1).execute()
    if response.data:
        return response.data[0]["system_prompt"]
    return ""

def update_system_prompt(new_prompt):
    """Updates the master system prompt in the cloud database."""
    supabase.table("brand_settings").update({"system_prompt": new_prompt}).eq("id", 1).execute()

def verify_user(email, password):
    """Verifies credentials against the cloud users table."""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    response = supabase.table("users").select("is_admin").eq("email", email).eq("password_hash", password_hash).execute()
    if response.data:
        return True, response.data[0]["is_admin"]
    return False, False

def save_draft_to_db(email, topic, content_type, audience, tone, industry, post_text, graphic_img):
    """Saves text to the database and uploads the image to the cloud bucket."""
    image_url = ""
    
    if graphic_img is not None:
        try:
            # 1. Convert the PIL Image to raw bytes
            buf = io.BytesIO()
            graphic_img.save(buf, format="PNG")
            image_bytes = buf.getvalue()
            
            # 2. Create a unique filename
            filename = f"draft_{hashlib.md5(post_text.encode()).hexdigest()[:8]}.png"
            
            # 3. Upload to Supabase Storage
            supabase.storage.from_("infographics").upload(
                path=filename,
                file=image_bytes,
                file_options={"content-type": "image/png"}
            )
            
            # 4. Retrieve the public URL for the image
            image_url = supabase.storage.from_("infographics").get_public_url(filename)
        except Exception as e:
            st.error(f"⚠️ Image cloud upload failed: {e}")

    # Insert the final row into the database
    supabase.table("draft_history").insert({
        "user_email": email,
        "topic": topic,
        "content_type": content_type,
        "audience": audience,
        "tone": tone,
        "industry": industry,
        "post_text": post_text,
        "image_url": image_url
    }).execute()

def get_draft_history(email):
    """Fetches history from the cloud, returning a list of tuples to match the UI unpacker."""
    response = supabase.table("draft_history").select("*").eq("user_email", email).order("created_at", desc=True).execute()
    
    formatted_results = []
    for row in response.data:
        formatted_results.append((
            row["topic"], row["content_type"], row["audience"],
            row["tone"], row["industry"], row["post_text"],
            row["image_url"], row["created_at"]
        ))
    return formatted_results

# ==========================================
# 2. STREAMLIT SESSION STATE MANAGEMENT
# ==========================================

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
    else:
        st.error("❌ Invalid email or password.")

def handle_logout():
    st.session_state.logged_in = False
    st.session_state.is_admin = False
    st.session_state.user_email = ""
    st.rerun()

# ==========================================
# 3. RENDER LOGIN SCREEN (Fixed Centered Card Layout)
# ==========================================

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🚀 AI LinkedIn Bot</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Internal Corporate Access Portal</p>", unsafe_allow_html=True)
    # Using a 1.2 : 1.5 : 1.2 ratio perfectly clusters the login box in the screen center
    _, col_login, _ = st.columns([1, 1, 1])
    
    with col_login:
        st.write("---")
        st.text_input("Email Address", key="login_email", placeholder="name@company.com")
        st.text_input("Password", type="password", key="login_password", placeholder="••••••••")
        st.button("Sign In", on_click=handle_login, type="primary", use_container_width=True)
        st.write("---")
            
        st.info("**Admin:** `admin@company.com` | `admin123` \n\n **Employee:** `employee@company.com` | `employee123` ")
    st.stop()

########################################## 4
col_title, col_logout = st.columns([4, 1])
with col_title:
    st.title("🚀 AI LinkedIn Content Creation Bot")
    st.caption(f"Logged in as: **{st.session_state.user_email}** ({'Admin' if st.session_state.is_admin else 'Employee'})")
with col_logout:
    st.button("Log Out", on_click=handle_logout, use_container_width=True)

# Force clean layout by role
if st.session_state.is_admin:
    user_tab, history_tab, admin_tab = st.tabs(["👤 User Dashboard", "📚 Draft History", "⚙️ Master Admin Settings"])
else:
    user_tab, history_tab = st.tabs(["👤 User Dashboard", "📚 Draft History"])
    admin_tab = None

# --- POLISHED ADMIN TAB (Fixes the squashed layout & returns Logo) ---
if st.session_state.is_admin and admin_tab is not None:
    with admin_tab:
        st.header("⚙️ Master Corporate Configuration")
        st.caption("Configure the overarching rules that dictate AI generation behavior and visual brand identity.")
        st.write("---")
        
        # Use columns to balance out the width so it doesn't look stretched or squashed
        admin_col1, admin_col2 = st.columns([3, 2])
        
        with admin_col1:
            st.subheader("🤖 Global AI System Prompt")
            st.caption("Paste your comprehensive corporate identity guidelines, tone, and formatting constraints below.")
            current_prompt = get_system_prompt()
            new_prompt_input = st.text_area("System Directive", value=current_prompt, height=400, label_visibility="collapsed")
        
        with admin_col2:
            st.subheader("🖼️ Visual Brand Assets")
            st.caption("Upload your official corporate logo. This asset will automatically overwrite default markers on all generated infographics.")
            
            # Reintroducing the logo uploader
            uploaded_logo = st.file_uploader("Upload Company Logo (PNG with transparent background preferred)", type=["png", "jpg", "jpeg"])            
            if uploaded_logo:
                # Create a universal assets directory
                os.makedirs("assets", exist_ok=True)
                logo_path = os.path.join("assets", "logo.png")
        
                # Save the file permanently
                with open(logo_path, "wb") as f:
                    f.write(uploaded_logo.getbuffer())

        if os.path.exists("assets/logo.png"):
            st.write("Current Active Logo:")
            st.image("assets/logo.png", width=150)
            st.write("---")
        if st.button("Save Master Configuration", type="primary", use_container_width=True):
                # Save the prompt text
                update_system_prompt(new_prompt_input)
                
                # Logic to handle logo storage will tie here cleanly 
                if uploaded_logo is not None:
                    st.success("💾 Guidelines and Brand Assets updated successfully inside SQLite!")
                else:
                    st.success("💾 Master System Prompt updated inside SQLite database!")
        
    # Show current logo if it exists
 

# --- USER TAB LOGIC (With RAG Context Document Uploader) ---
with user_tab:
    st.header("Generate LinkedIn Content")

# --- SESSION STATE INITIALIZATION ---
    if "post_text" not in st.session_state:
        st.session_state.post_text = ""
    if "graphic_img" not in st.session_state:
        st.session_state.graphic_img = None

    col1, col2 = st.columns([1, 1])
    
    with col1:
        topic = st.text_area("What is the post about?", placeholder="e.g., AI adoption in enterprise procurement")
        content_type = st.selectbox("Content Type", ["POV / Opinion", "Industry Insight", "Thought Leadership", "Trend Commentary", "Company Update", "Leadership Reflection"])
        
        #SUPPORTING DOCUMENTS UPLOADER ---
        st.markdown("### 📄 Context Documents (RAG)")
        uploaded_docs = st.file_uploader(
            "Upload reference materials (PDF, TXT, MD) to guide the AI with deep factual context", 
            type=["txt", "md", "pdf"], 
            accept_multiple_files=True
        )
        
        # Variable to accumulate all extracted file text
        extracted_context_text = ""
        
        if uploaded_docs:
            # Create a folder to store the saved markdown files if it doesn't exist
            os.makedirs("saved_context", exist_ok=True)
            
            for uploaded_file in uploaded_docs:
                file_name = uploaded_file.name
                file_text = ""
                
                # Handle Plain Text / Markdown files
                if file_name.endswith(('.txt', '.md')):
                    file_text = uploaded_file.read().decode("utf-8")
                
                # Handle PDF files
                elif file_name.endswith('.pdf'):
                    import pypdf
                    reader = pypdf.PdfReader(uploaded_file)
                    for page in reader.pages:           
                        text = page.extract_text()
                        if text:
                            file_text += text
                
                # 1. Append to the global context variable for the LLM prompt
                extracted_context_text += f"\n--- DOCUMENT SOURCE: {file_name} ---\n{file_text}\n"
            
            st.success(f"✅ Processed {len(uploaded_docs)} document(s) '!")

        # ------------------------------------------

        st.markdown("### ⚙️ Prompt Customization")
        audience = st.selectbox(
            "Target Audience", 
            [
                "C-Suite & Founders (CEO, CFO, CXO)", 
                "Policy Makers & Public Sector Leaders",
                "Product Managers & Technical Leads",
                "Venture Capitalists & Angel Investors",
                "CIOs & IT Directors", 
                "HR Leaders & Talent Acquisition", 
                "Marketing & Sales Executives", 
                "Procurement & Supply Chain Heads",
                "Senior Individual Contributors",
                "Mid-Level Management",
                "Entry-Level Professionals & Students"
            ]
        )
        
        tone = st.selectbox(
            "Tone", 
            [
                "Professional & Authoritative", 
                "Consultative & Advisory",
                "Conversational & Approachable", 
                "Bold & Provocative", 
                "Analytical & Data-Driven",
                "Inspirational & Visionary",
                "Urgent & Action-Oriented",
                "Empathetic & Authentic",
                "Witty & Unfiltered"
            ]
        )
        
        industry = st.selectbox(
            "Industry", 
            [
                "Technology & AI SaaS", 
                "Digital Public Infrastructure (DPI)",
                "Consulting & Professional Services",
                "Venture Capital & Private Equity",
                "Healthcare & Pharmaceuticals", 
                "Finance & Banking", 
                "Retail & E-commerce", 
                "Manufacturing & Industrial", 
                "Education & E-Learning",
                "Real Estate & Construction",
                "Logistics & Supply Chain",
                "Media & Entertainment",
                "Government & Public Sector",
                "Energy & Utilities"
            ]
        )
        length = st.selectbox("Length", ["Short", "Medium", "Long"])
        cta = st.text_input("Call to Action (Optional)", placeholder="e.g., Click the link below to read our full whitepaper")
        
        st.markdown("### 🎨 Infographic Settings")
        include_graphic = st.checkbox("Generate a matching AI graphic asset", value=True)
        style_preference = st.selectbox(
            "Visual Style", 
            [
                "Sleek Corporate Vector Art, Flat Design", 
                "3D Isometric Tech Illustration, Unreal Engine 5", 
                "Minimalist Infographic with Bold Typography",
                "Cinematic Corporate Photography"
            ],
            disabled=not include_graphic
        )
        
        generate_all_btn = st.button("Generate Post", type="primary")

    with col2:
        st.subheader("Generated Output")

        run_text_gen = False
        run_img_gen = False
        
        # 1. Main Button Logic
        if generate_all_btn:
            if not topic:
                st.warning("⚠️ Please enter a topic first!")
            else:
                run_text_gen = True
                if include_graphic:
                    run_img_gen = True
        
        # 2. Individual Regeneration Buttons (Only show if content already exists)
        if st.session_state.post_text != "":
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("🔄 Regenerate Text Only"):
                    run_text_gen = True
            with col_btn2:
                if include_graphic and st.button("🎨 Regenerate Graphic Only"):
                    run_img_gen = True

        if run_text_gen:
            with st.spinner("🤖 AI is craft-fitting your LinkedIn post..."):
                try:
                    master_system_prompt = get_system_prompt()
                    
                    user_instructions = f"""
                        Please generate a LinkedIn post based on the following specific requirements:
                        
                        - CONTENT TYPE: {content_type}
                        - TARGET AUDIENCE: {audience}
                        - TONE: {tone}
                        - INDUSTRY: {industry}
                        - LENGTH REFERENCE: {length} (Short: ~300-600 chars, Medium: ~800-1200 chars, Long: ~1500+ chars)
                        - CORE TOPIC: {topic}
                        """

                    if cta:
                        user_instructions += f"\n- MANDATORY CALL TO ACTION (CTA): {cta}"
                    if extracted_context_text:
                        user_instructions += f"\n\n--- ADDITIONAL FACTUAL BACKGROUND MATERIAL (RAG CONTEXT) ---\n{extracted_context_text}"
                    print(master_system_prompt)
                    print(user_instructions)
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", "{system_prompt}"),
                        ("human", "{human_input}")
                    ])
                    
                    chain = prompt_template | llm
                    
                    response = chain.invoke({
                        "system_prompt": master_system_prompt,
                        "human_input": user_instructions
                    })
                    
                    # Save to session state
                    st.session_state.post_text = response.content
                    st.session_state.debug_sys_prompt = master_system_prompt
                    st.session_state.debug_user_prompt = user_instructions

                    st.success("🎉 LinkedIn Draft Generated!")
                except Exception as e:
                    st.error(f"❌ Text Pipeline Failed: {e}")

        # Display Text Area (Updates session_state if user types in it)
        if st.session_state.post_text != "":
            st.markdown("### 📝 Draft Post")
            edited_text = st.text_area("Copy/Edit Draft:", value=st.session_state.post_text, height=350)
            st.session_state.post_text = edited_text
            
            # --- DEBUGGING EXPORT ---
            with st.expander("🐛 Debugging: Export Prompt Logs"):
                if "debug_sys_prompt" in st.session_state and "debug_user_prompt" in st.session_state:
                    # Compile the markdown string
                    debug_md_content = f"""# 🧠 MASTER SYSTEM PROMPT
{st.session_state.debug_sys_prompt}

---

# 👤 USER INSTRUCTIONS & RAG CONTEXT
{st.session_state.debug_user_prompt}

---

# 🤖 AI OUTPUT
{st.session_state.post_text}
"""
                    
                    # Provide the download button
                    st.download_button(
                        label="📥 Download debug_logs.md",
                        data=debug_md_content,
                        file_name="debug_logs.md",
                        mime="text/markdown"
                    )
        
        if include_graphic and st.session_state.post_text != "":
            if run_img_gen:
                with st.spinner("🎨 Directing AI graphic asset..."):
                    try:
                        # 🚨 FIX: Re-initialize the template and chain so it works independently
                        from langchain_core.prompts import ChatPromptTemplate
                        
                        art_director_prompt = f"""
                        You are a master information architect. Write a highly structured, single-paragraph layout prompt for the Z-Image-Turbo model to generate a complex corporate infographic matching this content:
                        
                        Post Content: {st.session_state.post_text}
                        
                        CRITICAL VISUAL STRUCTURE MAP:
                        - Layout: A highly organized, multi-panel B2B data infographic with strict geometric layout lines.
                        - Top Banner: Features a large bold hero headline in crisp white and gold typography.
                        - Main Canvas Body: Divided into distinct horizontal sections separated by thin, clean white divider lines. Each horizontal section contains a subtitle heading.
                        - Section 1 Grid: A horizontal row showing 3 columns. Each column has a clean flat circular icon containing a minimalist vector symbol, with clean text beneath it.
                        - Section 2 Grid: A horizontal row showing 4 columns. Each column contains a unique minimalist flat line icon with clean data descriptions underneath.
                        - Section 3 Grid: A highlighted bottom row with 5 dark blue rectangular panels side-by-side. Each panel has a bright vector icon and a single bold title.
                        - Right-Hand Sidebar: A distinct vertical narrow column spanning the right edge, labeled "AT A GLANCE" at the top with a vertical stack of clean bullet points and icons.
                        - Do not leave a lot of empty space. Fill the infographic with meaningful, data-driven content blocks and visual cues.
                        - keep top left corner free for a corporate logo placement (which will be stamped later).
                        - Use soft corporate color palette: blues specifically, grays, and whites with occasional gold accents for emphasis.
                        - Footer: A bottom full-width section containing a large white blockquote graphic on the left and corporate social media call-to-action badges at the absolute bottom edge.
                        - Overall Aesthetic: {style_preference}, flat vector UI design, sharp focus, professional corporate data visualization layout, perfectly aligned grids, immaculate presentation.
                        """
                        
                        img_prompt_template = ChatPromptTemplate.from_messages([
                            ("system", "{system_prompt}"),
                            ("human", "{human_input}")
                        ])
                        
                        # Tie it to your global llm instance
                        img_chain = img_prompt_template | llm
                        
                        visual_prompt_res = img_chain.invoke({
                            "system_prompt": "You only output direct, descriptive image prompt syntax without chat filler.",
                            "human_input": art_director_prompt
                        })
                        visual_prompt = visual_prompt_res.content
                        
                        import io
                        import os
                        from PIL import Image
                        from artist import generate_hf_image
                        
                        # Generate base image using Z-Image-Turbo
                        final_image = generate_hf_image(visual_prompt)
                        
                        # Stamp Universal Logo
                        logo_path = "assets/logo.png"
                        if os.path.exists(logo_path):
                            try:
                                final_image = final_image.convert("RGBA")
                                logo = Image.open(logo_path).convert("RGBA")
                                target_width = 150
                                aspect_ratio = logo.height / logo.width
                                target_height = int(target_width * aspect_ratio)
                                logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
                                final_image.paste(logo, (890, 40), logo)
                                final_image = final_image.convert("RGB")
                            except Exception as e:
                                print(f"Logo stamping failed: {e}")
                        
                        # Save final image to session state
                        st.session_state.graphic_img = final_image
                        st.success("✨ Graphic compiled perfectly!")
                    except Exception as e:
                        st.error(f"❌ Image Pipeline Failed: {e}") 

            # ==========================================
            # SAFE STREAMLIT IMAGE RENDERING (NEW)
            # ==========================================
            # This checks if there is an image in memory and draws it to the screen.
            if st.session_state.graphic_img is not None:
                st.write("---")
                st.markdown("### 📊 AI Graphic Companion")
                
                try:
                    import io
                    # 1. Create a safe memory buffer
                    buf = io.BytesIO()
                    
                    # 2. Save the PIL image object into the buffer as a raw PNG file
                    st.session_state.graphic_img.save(buf, format="PNG")
                    image_bytes = buf.getvalue()
                    
                    # 3. Force Streamlit to render the raw bytes (Bulletproof method)
                    st.image(image_bytes, caption="AI Generated Graphic Asset", use_container_width=True)
                    
                    # 4. Use the exact same bytes for the download button
                    st.download_button(
                        label="📥 Download Branded Graphic",
                        data=image_bytes,
                        file_name="linkedin_asset.png",
                        mime="image/png"
                    )
                except Exception as e:
                    st.error(f"⚠️ Could not render image bytes: {e}")
            
                # ==========================================
                # SAVE TO HISTORY BUTTON (NEW)
                # ==========================================
            if st.session_state.post_text != "":
                st.write("---")
                if st.button("💾 Save Draft to History", type="secondary", use_container_width=True):
                    save_draft_to_db(
                    email=st.session_state.user_email,
                    topic=topic,
                    content_type=content_type,
                    audience=audience,
                    tone=tone,
                    industry=industry,
                    post_text=st.session_state.post_text,
                    graphic_img=st.session_state.graphic_img
                )
                    st.success("✅ Draft locked into your history vault!")

# --- DRAFT HISTORY TAB ---
with history_tab:
    st.header("📚 Your Draft History")
    st.caption("A complete ledger of your past generations, settings, and visual assets.")
    st.write("---")
    
    drafts = get_draft_history(st.session_state.user_email)
    
    if not drafts:
        st.info("No drafts saved yet. Generate a post in the User Dashboard and click 'Save Draft to History'!")
    else:
        for draft in drafts:
            # Unpack the database row
            d_topic, d_ctype, d_aud, d_tone, d_ind, d_text, d_img_path, d_time = draft
            
            # Create a clean drop-down expander for each post
            with st.expander(f"🗓️ {d_time.split('.')[0]} | Topic: {d_topic[:100]}..."):
                
                # Show the settings used
                st.markdown(f"**Settings Used:** `{d_ctype}` | `{d_ind}` | `{d_aud}` | `{d_tone}`")
                st.write("---")
                
                # Show Text & Image side-by-side if an image exists
                hist_col1, hist_col2 = st.columns([2, 1])
                
                with hist_col1:
                    st.text_area("Generated Post:", value=d_text, height=300, disabled=True, key=d_time)
                
                with hist_col2:
                    # Just check if the URL string exists
                    if d_img_path and d_img_path.strip() != "":
                        st.image(d_img_path, caption="Saved Graphic Asset", use_container_width=True)
                    else:
                        st.info("No image generated for this draft.")
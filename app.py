import streamlit as st

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
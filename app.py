import streamlit as st
import pdf2image
import io
import json
import base64
import google.generativeai as genai
import re
from datetime import datetime, timezone

genai.configure(api_key=st.secrets.GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
# Define cached functions
@st.cache_data(show_spinner=False)
def get_gemini_response(input, pdf_content, prompt):
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

def _extract_first_json_object(text: str) -> dict:
    """
    Gemini sometimes wraps JSON in markdown fences. This extracts the first JSON object safely.
    """
    if not text:
        raise ValueError("Empty response")
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in response")
    return json.loads(match.group(0))


@st.cache_data(show_spinner=False)
def get_gemini_response_keywords(input, pdf_content, prompt):
    response = model.generate_content([input, pdf_content[0], prompt])
    return _extract_first_json_object(response.text)

@st.cache_data(show_spinner=False)
def input_pdf_setup(uploaded_file):
    if uploaded_file is not None:
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        first_page = images[0]
        img_byte_arr = io.BytesIO()
        first_page.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr).decode()
            }
        ]
        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Streamlit App

st.set_page_config(
    page_title="ATS Resume Scanner",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
  /* Motion + micro-interactions (kept lightweight) */
  @keyframes ats-fade-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes ats-gradient-pan { 0% { transform: translateX(-8%); } 50% { transform: translateX(8%); } 100% { transform: translateX(-8%); } }
  .block-container { animation: ats-fade-in 380ms ease-out; }

  .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
  [data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
  .ats-hero {
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 18px;
    padding: 20px 20px 18px 20px;
    margin: 0.35rem 0.35rem 0.75rem 0.35rem; /* top / right / bottom / left */
    box-sizing: border-box;
    position: relative;
    overflow: hidden; /* keeps rounded corners crisp */
    background: rgba(255, 255, 255, 0.02); /* subtle base behind gradient */
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.12);
  }
  .ats-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(88, 101, 242, 0.14), rgba(16, 185, 129, 0.10));
    opacity: 1;
    pointer-events: none;
    animation: ats-gradient-pan 7s ease-in-out infinite;
  }
  .ats-hero * { position: relative; z-index: 1; }
  .ats-hero-title { font-size: 1.8rem; font-weight: 750; letter-spacing: -0.02em; line-height: 1.15; }
  .ats-hero-subtitle { margin-top: 0.4rem; font-size: 0.98rem; opacity: 0.86; line-height: 1.35; }
  .ats-hero-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; flex-wrap: wrap; }
  .ats-card {
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 14px;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.5);
    transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
  }
  .ats-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.12);
    border-color: rgba(49, 51, 63, 0.18);
  }
  .ats-muted { opacity: 0.8; }

  /* Nicer buttons */
  div.stButton > button {
    transition: transform 120ms ease, box-shadow 160ms ease, border-color 160ms ease;
    border-radius: 12px;
  }
  div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.14);
  }
  div.stButton > button:active { transform: translateY(0); }

  /* Tabs: subtle emphasis */
  button[data-baseweb="tab"] {
    transition: color 120ms ease, background-color 120ms ease;
    border-radius: 999px;
  }

  @media (prefers-color-scheme: dark) {
    .ats-hero {
      border-color: rgba(250, 250, 250, 0.16);
      background: rgba(0, 0, 0, 0.16);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
    }
    .ats-hero::before {
      background: linear-gradient(135deg, rgba(88, 101, 242, 0.26), rgba(16, 185, 129, 0.18));
    }
    .ats-card { background: rgba(30, 31, 35, 0.35); border-color: rgba(250, 250, 250, 0.12); }
    .ats-card:hover { border-color: rgba(250, 250, 250, 0.18); box-shadow: 0 18px 34px rgba(0, 0, 0, 0.35); }
  }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="ats-hero">
  <div class="ats-hero-row">
    <div>
      <div class="ats-hero-title">ATS Resume Scanner</div>
      <div class="ats-hero-subtitle">Upload a resume PDF, paste a job description, then run an ATS-style analysis powered by Gemini.</div>
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if 'resume' not in st.session_state:
    st.session_state.resume = None

if "job_description" not in st.session_state:
    st.session_state.job_description = ""

if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "keywords_result" not in st.session_state:
    st.session_state.keywords_result = None
if "match_result" not in st.session_state:
    st.session_state.match_result = None
if "last_run" not in st.session_state:
    st.session_state.last_run = None

with st.sidebar:
    st.subheader("Resume")
    uploaded_file = st.file_uploader(
        "Resume PDF",
        type=["pdf"],
        help="We only use the first page image for analysis (current implementation).",
    )
    if uploaded_file is not None:
        st.session_state.resume = uploaded_file
        st.success("Resume uploaded.")
    else:
        st.info("Upload a PDF to enable analysis.")

    st.divider()
    st.subheader("Run")
    run_review = st.button("Review", use_container_width=True, help="Strengths, gaps, and role fit.")
    run_keywords = st.button("Keywords", use_container_width=True, help="Categorized skills from the job description.")
    run_match = st.button("Match", use_container_width=True, help="Match % + missing keywords + final thoughts.")

    cols = st.columns(2, gap="small")
    with cols[0]:
        clear_results = st.button("Clear results", use_container_width=True)
    with cols[1]:
        clear_jd = st.button("Clear JD", use_container_width=True)

    if clear_results:
        st.session_state.review_result = None
        st.session_state.keywords_result = None
        st.session_state.match_result = None
        st.session_state.last_run = None

    if clear_jd:
        st.session_state.job_description = ""

    st.divider()
    st.caption("Tip: paste the full JD (requirements + responsibilities) for better signal.")

left, right = st.columns([1.2, 1], gap="large")

with left:
    st.subheader("Job Description")
    st.session_state.job_description = st.text_area(
        "Paste job description",
        value=st.session_state.job_description,
        height=260,
        placeholder="Include requirements, responsibilities, skills, tools, seniority, domain keywords…",
        help="This is treated as the source of truth for keyword extraction.",
    )
    jd_words = len((st.session_state.job_description or "").split())

    m1, m2 = st.columns(2, gap="medium")
    m1.metric("JD words", jd_words)
    m2.metric("Last run", st.session_state.last_run or "—")

with right:
    st.subheader("Resume Preview")
    st.markdown('<div class="ats-card">', unsafe_allow_html=True)
    if st.session_state.resume is None:
        st.write("Upload a PDF in the sidebar to see a preview here.")
    else:
        try:
            # Create a fresh preview without consuming the cached resume bytes
            preview_images = pdf2image.convert_from_bytes(st.session_state.resume.getvalue(), first_page=1, last_page=1)
            st.image(preview_images[0], caption="Page 1", use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render preview: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

input_prompt1 = """
 You are an experienced Technical Human Resource Manager, your task is to review the provided resume against the job description. 
 Please share your professional evaluation on whether the candidate's profile aligns with the role. 
 Highlight the strengths and weaknesses of the applicant in relation to the specified job requirements.
"""

input_prompt2 = """
As an expert ATS (Applicant Tracking System) scanner with an in-depth understanding of AI and ATS functionality, 
your task is to evaluate a resume against a provided job description. Please identify the specific skills and keywords 
necessary to maximize the impact of the resume and provide response in json format as {Technical Skills:[], Analytical Skills:[], Soft Skills:[]}.
Note: Please do not make up the answer only answer from job description provided"""

input_prompt3 = """
You are a skilled ATS (Applicant Tracking System) scanner with a deep understanding of data science and ATS functionality, 
your task is to evaluate the resume against the provided job description. Give me the percentage of match if the resume matches
the job description. First the output should come as percentage and then keywords missing and last final thoughts.
"""

st.divider()
st.caption("Run an analysis from the sidebar. Results stay available while you switch tabs.")

tabs = st.tabs(["Resume review", "Keywords", "Match score"])

def _validate_inputs() -> tuple[bool, str]:
    if st.session_state.resume is None:
        return False, "Please upload your resume PDF in the sidebar."
    if not st.session_state.job_description or not st.session_state.job_description.strip():
        return False, "Please paste a job description."
    return True, ""


with tabs[0]:
    st.subheader("Resume Review")
    if run_review:
        ok, msg = _validate_inputs()
        if not ok:
            st.warning(msg)
        else:
            with st.spinner("Analyzing resume vs job description…"):
                pdf_content = input_pdf_setup(st.session_state.resume)
                response = get_gemini_response(input_prompt1, pdf_content, st.session_state.job_description)
            st.session_state.review_result = response
            st.session_state.last_run = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            st.toast("Resume review ready.", icon="✅")
    if st.session_state.review_result:
        st.markdown('<div class="ats-card">', unsafe_allow_html=True)
        st.write(st.session_state.review_result)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Click **Generate Resume Review** in the sidebar to run this analysis.")

with tabs[1]:
    st.subheader("Keyword Extraction")
    if run_keywords:
        ok, msg = _validate_inputs()
        if not ok:
            st.warning(msg)
        else:
            with st.spinner("Extracting skills and keywords…"):
                pdf_content = input_pdf_setup(st.session_state.resume)
                try:
                    response = get_gemini_response_keywords(input_prompt2, pdf_content, st.session_state.job_description)
                except Exception as e:
                    response = None
                    st.error(f"Could not parse keywords JSON: {e}")
            if response:
                st.session_state.keywords_result = response
                st.session_state.last_run = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                st.toast("Keywords extracted.", icon="✅")

    if st.session_state.keywords_result:
        response = st.session_state.keywords_result
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown('<div class="ats-card">', unsafe_allow_html=True)
            st.markdown("**Technical Skills**")
            st.write(response.get("Technical Skills", []))
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="ats-card">', unsafe_allow_html=True)
            st.markdown("**Analytical Skills**")
            st.write(response.get("Analytical Skills", []))
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown('<div class="ats-card">', unsafe_allow_html=True)
            st.markdown("**Soft Skills**")
            st.write(response.get("Soft Skills", []))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Click **Extract Skills & Keywords** in the sidebar to run this analysis.")

with tabs[2]:
    st.subheader("Match Score")
    if run_match:
        ok, msg = _validate_inputs()
        if not ok:
            st.warning(msg)
        else:
            with st.spinner("Computing match score…"):
                pdf_content = input_pdf_setup(st.session_state.resume)
                response = get_gemini_response(input_prompt3, pdf_content, st.session_state.job_description)
            st.session_state.match_result = response
            st.session_state.last_run = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            st.toast("Match score ready.", icon="✅")

    if st.session_state.match_result:
        st.markdown('<div class="ats-card">', unsafe_allow_html=True)
        st.write(st.session_state.match_result)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Click **Compute Match Score** in the sidebar to run this analysis.")

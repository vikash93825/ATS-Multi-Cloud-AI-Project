import streamlit as st
import pdf2image
import io
import json
import base64
import google.generativeai as genai
import re

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
  .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
  [data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
  .ats-card {
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 14px;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.5);
  }
  @media (prefers-color-scheme: dark) {
    .ats-card { background: rgba(30, 31, 35, 0.35); border-color: rgba(250, 250, 250, 0.12); }
  }
</style>
""",
    unsafe_allow_html=True,
)

st.title("ATS Resume Scanner")
st.caption("Upload a resume PDF, paste a job description, then run an ATS-style analysis powered by Gemini.")

if 'resume' not in st.session_state:
    st.session_state.resume = None

if "job_description" not in st.session_state:
    st.session_state.job_description = ""

with st.sidebar:
    st.subheader("Inputs")
    uploaded_file = st.file_uploader("Resume (PDF)", type=["pdf"])
    if uploaded_file is not None:
        st.session_state.resume = uploaded_file
        st.success("Resume uploaded.")
    else:
        st.info("Upload a PDF to enable analysis.")

    st.divider()
    st.subheader("Actions")
    run_review = st.button("Resume Review", use_container_width=True)
    run_keywords = st.button("Extract Keywords", use_container_width=True)
    run_match = st.button("Match Score", use_container_width=True)

left, right = st.columns([1.2, 1], gap="large")

with left:
    st.subheader("Job Description")
    st.session_state.job_description = st.text_area(
        "Paste the role description here",
        value=st.session_state.job_description,
        height=260,
        placeholder="Responsibilities, requirements, skills, tools, etc.",
    )

with right:
    st.subheader("Resume Preview (first page)")
    st.markdown('<div class="ats-card">', unsafe_allow_html=True)
    if st.session_state.resume is None:
        st.write("Upload a PDF to see a preview.")
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
            st.markdown('<div class="ats-card">', unsafe_allow_html=True)
            st.write(response)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Click **Resume Review** in the sidebar to run this analysis.")

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
        st.caption("Click **Extract Keywords** in the sidebar to run this analysis.")

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
            st.markdown('<div class="ats-card">', unsafe_allow_html=True)
            st.write(response)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.caption("Click **Match Score** in the sidebar to run this analysis.")

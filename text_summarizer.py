
import streamlit as st
from pypdf import PdfReader
from LLM import ask_ai

st.title("AI-Powered Text Summarizer")

# Upload a resume PDF
resume_file = st.file_uploader(
    "Upload your resume PDF",
    type=["pdf"]
)

resume_text = ""

# Extract text from the PDF
if resume_file is not None:
    reader = PdfReader(resume_file)

    for page in reader.pages:
        resume_text += page.extract_text() or ""

    if resume_text.strip():
        st.success("Resume text extracted successfully!")

        with st.expander("See extracted text"):
            st.text(resume_text)
    else:
        st.warning("No readable text was found in this PDF.")

# Enter or paste text
user_text = st.text_area(
    "Enter text to summarize, or paste extracted resume text",
    value=resume_text,
    height=250
)

# Summarize button
if st.button("Summarize"):

    if user_text.strip() == "":
        st.warning("Please enter some text to summarize.")

    else:
        prompt = f"""
        Summarize the following text in a short,
        clear and simple words.
        include these points in the summary:
        -Key skills and experience
        -Achievements and contributions
        -Overall suitability for the role

        TEXT:
        {user_text}
        """

        with st.spinner("Generating summary..."):
            summary = ask_ai(prompt)

        st.subheader("Summary")
        st.write(summary)

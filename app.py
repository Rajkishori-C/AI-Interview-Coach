import streamlit as st
from pypdf import PdfReader
from coach import analyze_profile
from coach import generate_questions
from coach import evaluate_answers, final_report

st.title("AI-Interview-Coach")


# to define pdf reading function to extract all the pages
def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


# to allow users to upload a resume in pdf format
resume_file = st.file_uploader(
    "Upload your resume in PDF format", type="pdf"
)

# to allow users to upload a job description
job_description = st.text_area(
    "Upload the job description", height=200
)


# to process the resume
if resume_file is not None:
    resume_text = read_pdf(resume_file)

    if resume_text.strip() == "":
        st.error("The uploaded resume is empty. Please upload a valid PDF file.")
    else:
        st.success("Resume uploaded successfully!")

        with st.expander("see extracted text"):
            st.text(resume_text)

        # Analyze button
        if st.button("Analyze my profile"):
            if job_description.strip() == "":
                st.error("Please enter the job description.")
            else:
                with st.spinner("Analyzing your profile..."):
                    st.session_state.resume_text = resume_text
                    st.session_state.job_description = job_description
                    st.session_state.analysis_result = analyze_profile(
                        resume_text, job_description
                    )


# to display the analysis result
if "analysis_result" in st.session_state:
    a = st.session_state.analysis_result

    st.header(f"Profile analysis: {a.get('Role', 'Role')}")
    st.metric("Match score", f"{a.get('match score', 0)}%")
    st.write(a.get("summary", ""))

    # matching skills should be declared in columns/table
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Matching skills")
        for skill in a.get("Matching skills", []):
            st.write(f"- {skill}")

    with col2:
        st.subheader("Missing skills")
        for skill in a.get("missing skills", []):
            st.write(f"- {skill}")

    with st.expander("view full JSON response"):
        st.json(a)


# to generate interview questions after profile analysis
if "analysis_result" in st.session_state:
    st.divider()
    st.header("Interview questions")

    # select the number of questions
    num = st.slider("How many questions", 3, 10, 5)

    if st.button("generate questions"):
        with st.spinner("Generating questions..."):
            result = generate_questions(
                st.session_state.resume_text,
                st.session_state.job_description,
                st.session_state.analysis_result,
                num_questions=num
            )

        # to store the questions
        st.session_state.questions = result.get("questions", [])
        st.session_state.current_q = 0
        st.session_state.answers = []

    if "questions" in st.session_state and st.session_state.questions:
        st.success(f"{len(st.session_state.questions)} questions are ready!")

        if st.button("Start interview"):
            st.session_state.pop("evaluations", None)
            st.session_state.pop("report", None)
            first_q=st.session_state.questions[0]["question"]

            st.session_state.interview_started = True
            st.session_state.current_q = 0
            st.session_state.answers = []
            st.session_state.messages =[

            {
                "role": "assistant",
                "content": "Let's Begin",
            },
            {
                "role":"assistant",
                "content": f"**Q1:** {first_q}"
            },
            ]

        if not st.session_state.questions:
            st.warning("No interview questions were generated.")


# # to display the generated questions
# if "questions" in st.session_state:
#     st.subheader("Generated Interview Questions")

#     for i, q in enumerate(st.session_state.questions, start=1):
#         st.markdown(f"**Q{i}:** {q.get('question', '')}")
#         st.write(f"- Type: {q.get('type', '')}")
#         st.write(f"- Skill: {q.get('skill', '')}")
#         st.divider()


# interview flow
if "questions" in st.session_state and st.session_state.get("interview_started"):
    st.divider()
    st.header("Interview")
    
    questions = st.session_state.questions
    current = st.session_state.current_q
    total = len(questions)

    if total > 0:
        st.progress(
            current / total,
            text=f"Answered {current} out of {total} questions"
        )

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if current < total:
            answer = st.chat_input("Type your answer:")

            if answer:
                q = questions[current]
                st.session_state.messages.append({
                    "role": "user",
                    "content": answer
                })

                st.session_state.answers.append({
                    "question": q.get("question"),
                    "type": q.get("type"),
                    "skill": q.get("skill"),
                    "answer": answer
                })

                st.session_state.current_q += 1
                nxt = st.session_state.current_q

                if nxt < total:
                    next_text = (
                        f"**Q{nxt + 1}:** "
                        f"{questions[nxt].get('question', '')}"
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": next_text
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "Interview completed! Thank you."
                    })
                    st.session_state.interview_started = False

                st.rerun()

        else:
            st.success("Interview completed! Thank you for your time.")
            st.session_state.interview_started = False


# evaluate answers after the interview is finished
if ("questions" in st.session_state and st.session_state.questions
        and len(st.session_state.get("answers", [])) == len(st.session_state.questions)
        and not st.session_state.get("interview_started", False)):
    if st.button("Evaluate answers"):
        with st.spinner("Evaluating your answers..."):
            result = evaluate_answers(
                st.session_state.answers,
                st.session_state.analysis_result.get("Role", "the role")
            )
            st.session_state.evaluations = result.get("evaluations", [])

    if "evaluations" in st.session_state:
        st.subheader("Answer Evaluation")
        for i, evaluation in enumerate(st.session_state.evaluations, start=1):
            st.markdown(f"**Q{i} Evaluation**")
            st.write(f"- Relevance: {evaluation.get('relevance', evaluation.get('relevence', 0))}/10")
            st.write(f"- Depth: {evaluation.get('depth', 0)}/10")
            st.write(f"- Clarity: {evaluation.get('clarity', 0)}/10")
            st.write(f"- Example: {evaluation.get('example', 0)}/10")
            st.write(f"Feedback: {evaluation.get('feedback', '')}")
            st.write(f"Suggestion: {evaluation.get('Suggestion', evaluation.get('suggestion', ''))}")
            st.divider()


# Final scorecard
if "evaluations" in st.session_state and st.session_state.evaluations:
    st.divider()
    st.header("Final scorecard")

    evals = st.session_state.evaluations

    # Calculate the average across all rubric scores
    rubric_names = ["relevance", "depth", "clarity", "example"]
    all_scores = []

    for e in evals:
        for area in rubric_names:
            score = e.get(area, e.get("relevence", 0) if area == "relevance" else 0)
            all_scores.append(score)

    overall = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

    if overall >= 7.5:
        readiness = "Ready for interviews"
    elif overall >= 5:
        readiness = "Almost ready; more practice recommended"
    else:
        readiness = "More practice needed"

    col1, col2 = st.columns(2)

    col1.metric("Interview score", f"{overall}/10")
    col2.metric(
        "Resume match",
        f"{st.session_state.analysis_result.get('match score', 0)}%"
    )

    st.subheader(readiness)

    st.markdown("#### Score by rubric area")

    for area in rubric_names:
        avg = sum(
            e.get(area, e.get("relevence", 0) if area == "relevance" else 0)
            for e in evals
        ) / len(evals)

        st.write(f"{area.title()}: {avg:.1f}/10")
        st.progress(min(avg / 10, 1.0))

    if st.button("Get my improvement plan"):
        with st.spinner("Preparing your personal feedback..."):
            st.session_state.report = final_report(
                st.session_state.analysis_result,
                st.session_state.answers,
                evals,
            )

    if "report" in st.session_state:
        report = st.session_state.report

        st.markdown("#### Strengths")
        for item in report.get("strengths", []):
            st.write("-", item)

        st.markdown("#### Areas to improve")
        for item in report.get("improvements", []):
            st.write("-", item)

        st.markdown("#### Study plan")
        for item in report.get("study_plan", []):
            st.write("-", item)

        st.success(report.get("message", ""))

        lines = [
            "AI INTERVIEW COACH - SCORECARD",
            f"Role: {st.session_state.analysis_result.get('Role', '')}",
            f"Interview score: {overall}/10",
            f"Resume match: {st.session_state.analysis_result.get('match score', 0)}%",
            f"Readiness: {readiness}",
            "",
            "STRENGTHS:",
            *[f"- {x}" for x in report.get("strengths", [])],
            "",
            "AREAS TO IMPROVE:",
            *[f"- {x}" for x in report.get("improvements", [])],
            "",
            "STUDY PLAN:",
            *[f"- {x}" for x in report.get("study_plan", [])],
        ]

        st.download_button(
            "Download scorecard",
            "\n".join(lines),
            file_name="interview_scorecard.txt",
        )

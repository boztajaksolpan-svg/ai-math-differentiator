
import streamlit as st

st.set_page_config(page_title="AI Math Differentiator")

st.title("AI Math Differentiator")
st.write("Topic: Linear Equations")

level = st.selectbox(
    "Choose your difficulty level:",
    ["Basic", "Standard", "Advanced"]
)

problems = {
    "Basic": {
        "question": "x + 5 = 12",
        "answer": "7",
        "hint": "Subtract 5 from both sides."
    },
    "Standard": {
        "question": "3x - 7 = 14",
        "answer": "7",
        "hint": "Add 7, then divide by 3."
    },
    "Advanced": {
        "question": "2(x + 3) + 5 = 3x - 4",
        "answer": "15",
        "hint": "Expand brackets and collect like terms."
    }
}

problem = problems[level]

st.subheader("Solve the equation:")
st.write(problem["question"])

answer = st.text_input("Enter x:")

if st.button("Check Answer"):
    if answer.strip() == problem["answer"]:
        st.success("Correct answer!")
    else:
        st.error("Try again!")

if st.button("Get Hint"):
    st.info(problem["hint"])

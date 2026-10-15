
import json
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="AI Math Differentiator")
st.title("AI Math Differentiator")
st.write("Topic: Linear Equations")

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

def signed(n):
    return f"+ {n}" if n >= 0 else f"- {abs(n)}"

level = st.selectbox(
    "Choose your difficulty level:",
    ["Basic", "Standard", "Advanced"]
)

if st.session_state.get("last_level") != level:
    st.session_state.last_level = level
    st.session_state.problem = None
    st.session_state.hint = None

if st.button("Generate AI Problem"):
    prompt = f"""
    Create parameters for a {level} linear equation.
    Return a JSON object containing five integers:
    a, b, c, d, x.

    Requirements:
    a: 2 to 8
    d: 1 to 8, different from a
    b: -9 to 9
    c: -9 to 9
    x: -10 to 10

    Choose varied values for each new problem.
    The app builds the equation and calculates
    the correct answer from these parameters.
    """

    try:
        with st.spinner("AI is generating a problem..."):
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            data = json.loads(response.text)
            a, b, c, d, x = [
                int(data[k]) for k in ("a", "b", "c", "d", "x")
            ]

            if not (
                2 <= a <= 8 and 1 <= d <= 8
                and a != d and -9 <= b <= 9
                and -9 <= c <= 9 and -10 <= x <= 10
            ):
                raise ValueError("Invalid parameters")

            if level == "Basic":
                right = x + b
                equation = f"x {signed(b)} = {right}"
                solution = f"x = {right} - ({b}) = {x}"

            elif level == "Standard":
                right = a * x + b
                equation = f"{a}x {signed(b)} = {right}"
                solution = (
                    f"{a}x = {right - b}, "
                    f"so x = {right - b} / {a} = {x}"
                )

            else:
                e = a * (x + b) + c - d * x
                equation = (
                    f"{a}(x {signed(b)}) {signed(c)} "
                    f"= {d}x {signed(e)}"
                )
                solution = (
                    f"Expand the brackets and collect x terms. "
                    f"({a} - {d})x = {e - a*b - c}. "
                    f"Therefore x = {x}."
                )

            st.session_state.problem = {
                "equation": equation,
                "answer": x,
                "solution": solution
            }
            st.session_state.hint = None

   
    except Exception as e:
        st.error("Could not generate a problem.")
        st.error(f"Error type: {type(e).__name__}")
        st.error(f"Error code: {getattr(e, 'code', 'unknown')}")

problem = st.session_state.get("problem")

if problem:
    st.subheader("Solve the equation")
    st.markdown(f"### {problem['equation']}")

    answer = st.text_input("Enter your answer (x):")

    if st.button("Check Answer"):
        try:
            if abs(float(answer) - problem["answer"]) < 0.000001:
                st.success("Correct! Well done!")
            else:
                st.warning("Try again or request an AI hint.")
        except ValueError:
            st.warning("Please enter a number.")

    if st.button("Get AI Hint"):
        try:
            with st.spinner("AI is preparing a hint..."):
                response = client.models.generate_content(
                    model=MODEL,
                    contents=f"""
                    You are a mathematics tutor.
                    The student's level is {level}.
                    The equation is {problem['equation']}.

                    Provide one clear, helpful hint.
                    Basic: explain very simply.
                    Standard: guide the next step.
                    Advanced: suggest a strategy.
                    Do not reveal the final answer.
                    Use simple English.
                    """
                )
                st.session_state.hint = response.text
        except Exception:
            st.error("AI hint is temporarily unavailable.")

    if st.session_state.get("hint"):
        st.info(st.session_state.hint)

    with st.expander("Show Solution"):
        st.write(problem["solution"])

else:
    st.info("Select a level and generate an AI problem.")

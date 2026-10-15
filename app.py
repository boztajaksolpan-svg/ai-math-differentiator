"""AI Math Differentiator - differentiated linear equations using Gemini AI.

The AI proposes parameters and offers hints. Python checks the values,
constructs solvable equations, validates answers, and avoids repeated problems
within a Streamlit session. No API key is stored in this file.
"""

import json

import streamlit as st
from google import genai
from google.genai import types


MODEL = "gemini-3.5-flash-lite"  # This is the model previously tested in the app.
LEVELS = ("Basic", "Standard", "Advanced")


def signed(number):
    """Display an integer with a readable + / - sign."""
    return f"+ {number}" if number >= 0 else f"- {abs(number)}"


def make_problem(level, a, b, c, d, x):
    """Create an equation and a checked step-by-step solution."""
    if level == "Basic":
        right = x + b
        equation = f"x {signed(b)} = {right}"
        operation = (
            f"Subtract {b} from both sides."
            if b > 0 else f"Add {abs(b)} to both sides."
        )
        steps = [
            f"Start with: {equation}",
            operation,
            f"x = {right} - ({b}) = {x}",
            f"Check: {x} + ({b}) = {right}",
        ]
        assert x + b == right

    elif level == "Standard":
        right = a * x + b
        equation = f"{a}x {signed(b)} = {right}"
        operation = (
            f"Subtract {b} from both sides."
            if b > 0 else f"Add {abs(b)} to both sides."
        )
        steps = [
            f"Start with: {equation}",
            operation,
            f"{a}x = {right} - ({b}) = {a * x}",
            f"Divide both sides by {a}: x = {a * x} / {a} = {x}",
            f"Check: {a}({x}) + ({b}) = {right}",
        ]
        assert a * x + b == right

    elif level == "Advanced":
        e = a * (x + b) + c - d * x
        equation = f"{a}(x {signed(b)}) {signed(c)} = {d}x {signed(e)}"
        steps = [
            f"Start with: {equation}",
            f"Expand the brackets: {a}x + ({a * b}) + ({c}) = {d}x + ({e})",
            f"Move variable terms left and constants right: "
            f"({a} - {d})x = {e} - ({a * b}) - ({c})",
            f"Simplify: {a - d}x = {(a - d) * x}",
            f"Divide by {a - d}: x = {x}",
            f"Check: left side = {a * (x + b) + c}; "
            f"right side = {d * x + e}",
        ]
        assert a != d and a * (x + b) + c == d * x + e

    else:
        raise ValueError("Unknown difficulty level")

    return {"equation": equation, "answer": x, "steps": steps, "level": level}


def validate_parameters(data):
    """Do not trust API responses without checking keys, types and ranges."""
    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object")
    keys = ("a", "b", "c", "d", "x")
    if any(k not in data or type(data[k]) is not int for k in keys):
        raise ValueError("AI response requires five integer parameters")
    a, b, c, d, x = (data[k] for k in keys)
    if not (2 <= a <= 8 and 1 <= d <= 8 and a != d
            and -9 <= b <= 9 and -9 <= c <= 9 and -10 <= x <= 10):
        raise ValueError("AI parameters are outside the permitted ranges")
    return a, b, c, d, x


def make_unique_problem(level, params, used_equations):
    """Keep AI-suggested parameters, adjusting b/x only to avoid repetition.

    There are hundreds of valid b/x combinations in each level, so consecutive
    clicks don't need to show the same equation even if the model repeats values.
    """
    a, b, c, d, x = params
    for b_shift in range(19):
        candidate_b = ((b + 9 + b_shift) % 19) - 9
        if candidate_b == 0:
            continue  # Basic/Standard should require an actual arithmetic step.
        for x_shift in range(21):
            candidate_x = ((x + 10 + x_shift) % 21) - 10
            problem = make_problem(level, a, candidate_b, c, d, candidate_x)
            if problem["equation"] not in used_equations:
                return problem
    raise ValueError("All possible equation variations have been used")


# ---------- Streamlit user interface ----------
st.set_page_config(page_title="AI Math Differentiator", page_icon="🧮")
st.title("🧮 AI Math Differentiator")
st.caption("Topic: Linear Equations | AI for Differentiated Learning")
st.write("Choose a level, generate a problem, check your answer, and get an AI hint.")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

level = st.selectbox("Choose your difficulty level:", LEVELS)

if "used_equations" not in st.session_state:
    st.session_state.used_equations = {name: [] for name in LEVELS}
if "problem" not in st.session_state:
    st.session_state.problem = None
if "hint" not in st.session_state:
    st.session_state.hint = None
if "problem_number" not in st.session_state:
    st.session_state.problem_number = 0
if st.session_state.get("last_level") != level:
    st.session_state.last_level = level
    st.session_state.problem = None
    st.session_state.hint = None

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if st.button("Generate AI Problem", type="primary"):
    previous = st.session_state.used_equations[level][-5:]
    prompt = f"""
    You are helping a mathematics teacher build differentiated learning tasks.
    Generate NEW integer parameters for a {level} linear equation.
    Return ONLY a JSON object with exactly five integer keys: a, b, c, d, x.
    Permitted ranges: a=2..8; d=1..8 and d!=a;
    b=-9..9 except zero; c=-9..9; x=-10..10.
    Choose varied numbers rather than always repeating the same values.
    Previously generated equations to avoid: {previous}.
    The application constructs the equation and checks the answer itself.
    For Basic, it creates a one-step equation x+b=right.
    For Standard, it creates a two-step equation ax+b=right.
    For Advanced, it creates a multi-step equation a(x+b)+c=dx+e.
    """
    try:
        with st.spinner("Gemini is generating a problem..."):
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            if not response.text:
                raise ValueError("Gemini returned an empty response")
            parameters = validate_parameters(json.loads(response.text))
            problem = make_unique_problem(
                level, parameters, st.session_state.used_equations[level]
            )
            st.session_state.used_equations[level].append(problem["equation"])
            st.session_state.problem = problem
            st.session_state.hint = None
            st.session_state.problem_number += 1
    except Exception as exc:
        error_code = getattr(exc, "code", None)
        st.error("Gemini could not generate a problem. Please try again.")
        st.caption(
            f"Error: {type(exc).__name__}"
            + (f" (code {error_code})" if error_code else "")
        )

problem = st.session_state.problem
if problem:
    st.subheader(f"{problem['level']} — Solve the equation")
    st.markdown(f"### {problem['equation']}")

    answer = st.text_input(
        "Enter your answer (x):",
        key=f"answer_{st.session_state.problem_number}",
    )

    if st.button("Check Answer"):
        try:
            if abs(float(answer) - problem["answer"]) < 1e-6:
                st.success("Correct! Well done!")
            else:
                st.warning("Not quite. Try again, or ask Gemini for a hint.")
        except ValueError:
            st.warning("Please enter a number, such as 4 or -3.")

    if st.button("Get AI Hint"):
        hint_prompt = f"""
        Act as a supportive mathematics tutor teaching linear equations.
        Level: {problem['level']}
        Equation: {problem['equation']}
        Give one short, mathematically correct hint in plain English.
        Basic: state the very next arithmetic operation simply.
        Standard: guide the student on isolating the variable.
        Advanced: suggest expanding brackets and combining like terms.
        Do not give the final value of x or the complete solution.
        """
        try:
            with st.spinner("Gemini is preparing a hint..."):
                response = client.models.generate_content(
                    model=MODEL, contents=hint_prompt
                )
                if not response.text:
                    raise ValueError("Empty hint response")
                st.session_state.hint = response.text
        except Exception as exc:
            st.warning("The AI hint is temporarily unavailable. Try again.")
            st.caption(f"Error: {type(exc).__name__}")

    if st.session_state.hint:
        st.info(st.session_state.hint)

    with st.expander("Show Step-by-Step Solution"):
        for index, step in enumerate(problem["steps"], start=1):
            st.write(f"{index}. {step}")
else:
    st.info("Select a level, then click 'Generate AI Problem'.")

st.caption("Gemini proposes parameters and hints; Python verifies the equation and answer.")

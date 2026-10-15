"""AI Math Differentiator: Gemini-assisted linear equations (without SymPy).

Gemini suggests integer parameters and student hints. Python builds and checks
mathematically solvable equations and avoids repetition within a session.
"""

import json
import re

import streamlit as st
from google import genai
from google.genai import types


MODEL = "gemini-3.5-flash-lite"
LEVELS = ("Basic", "Standard", "Advanced")


def signed(number):
    """Format a signed integer for a readable equation."""
    return f"+ {number}" if number >= 0 else f"- {abs(number)}"


def validate_parameters(data):
    """Check all AI-generated values before using them in mathematics."""
    keys = ("a", "b", "c", "d", "x")
    if not isinstance(data, dict) or any(
        key not in data or type(data[key]) is not int for key in keys
    ):
        raise ValueError("Gemini must return five integer parameters")

    a, b, c, d, x = (data[key] for key in keys)
    if not (
        2 <= a <= 8
        and 1 <= d <= 8
        and a != d
        and -9 <= b <= 9
        and b != 0
        and -9 <= c <= 9
        and -10 <= x <= 10
    ):
        raise ValueError("Gemini returned parameters outside permitted ranges")
    return a, b, c, d, x


def make_problem(level, a, b, c, d, proposed_x):
    """Create a unique-solution equation and check its answer using arithmetic."""
    if level == "Basic":
        right = proposed_x + b
        equation = f"x {signed(b)} = {right}"
        left_coefficient, left_constant = 1, b
        right_coefficient, right_constant = 0, right
        steps = [
            f"Start with: {equation}",
            f"{'Subtract ' + str(b) if b > 0 else 'Add ' + str(abs(b))} to both sides.",
            f"x = {right} - ({b}) = {proposed_x}",
            f"Check: {proposed_x} + ({b}) = {right}",
        ]

    elif level == "Standard":
        right = a * proposed_x + b
        equation = f"{a}x {signed(b)} = {right}"
        left_coefficient, left_constant = a, b
        right_coefficient, right_constant = 0, right
        steps = [
            f"Start with: {equation}",
            f"{'Subtract ' + str(b) if b > 0 else 'Add ' + str(abs(b))} to both sides.",
            f"{a}x = {right} - ({b}) = {a * proposed_x}",
            f"Divide both sides by {a}: x = {a * proposed_x} / {a} = {proposed_x}",
            f"Check: {a}({proposed_x}) + ({b}) = {right}",
        ]

    elif level == "Advanced":
        e = a * (proposed_x + b) + c - d * proposed_x
        equation = f"{a}(x {signed(b)}) {signed(c)} = {d}x {signed(e)}"
        left_coefficient, left_constant = a, a * b + c
        right_coefficient, right_constant = d, e
        steps = [
            f"Start with: {equation}",
            f"Expand: {a}x + ({a * b}) + ({c}) = {d}x + ({e})",
            f"Collect x terms: ({a} - {d})x = {e} - ({a * b}) - ({c})",
            f"Simplify: {a - d}x = {(a - d) * proposed_x}",
            f"Divide both sides by {a - d}: x = {proposed_x}",
            f"Check: left = {a * (proposed_x + b) + c}; "
            f"right = {d * proposed_x + e}",
        ]
    else:
        raise ValueError("Unknown level")

    # Independently solve Ax+B=Cx+D (without trusting an AI-written answer).
    coefficient = left_coefficient - right_coefficient
    constant = right_constant - left_constant
    if coefficient == 0 or constant % coefficient != 0:
        raise ValueError("Equation is not uniquely solvable with an integer answer")
    answer = constant // coefficient
    if (
        answer != proposed_x
        or left_coefficient * answer + left_constant
        != right_coefficient * answer + right_constant
    ):
        raise ValueError("Mathematical verification failed")

    return {"level": level, "equation": equation, "answer": answer, "steps": steps,
            "b": b}


def make_unique_problem(level, parameters, used_equations):
    """Try valid variations until we find an equation not shown this session."""
    a, b, c, d, x = parameters
    for b_offset in range(19):
        candidate_b = (b + 9 + b_offset) % 19 - 9
        if candidate_b == 0:
            continue
        for x_offset in range(21):
            candidate_x = (x + 10 + x_offset) % 21 - 10
            candidate = make_problem(level, a, candidate_b, c, d, candidate_x)
            if candidate["equation"] not in used_equations:
                return candidate
    raise ValueError("Could not find an unused equation; please generate again")


def fallback_hint(problem):
    """Return a safe hint if Gemini is unavailable or reveals the answer."""
    if problem["level"] == "Basic":
        b = problem["b"]
        return f"{'Subtract ' + str(b) if b > 0 else 'Add ' + str(abs(b))} on both sides."
    if problem["level"] == "Standard":
        return "Move the constant term to the other side, then divide by the coefficient of x."
    return "Expand the brackets, then collect all x terms on one side."


def reveals_final_answer(hint):
    """Reject hints that explicitly give a numerical solution for x."""
    return bool(re.search(r"\bx\s*(?:=|is|equals)\s*[-+]?\d+\b|\b(?:answer|solution)\s*(?:is|=|:)\s*[-+]?\d+\b", hint, re.I))


# -------------------- Streamlit interface --------------------
st.set_page_config(page_title="AI Math Differentiator", page_icon="🧮")
st.title("🧮 AI Math Differentiator")
st.caption("Topic: Linear Equations | AI for Differentiated Learning")
st.write("Choose a level, generate a problem, check your answer, or request an AI hint.")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Missing GEMINI_API_KEY. Add it in your Streamlit app's Secrets settings.")
    st.stop()

# These checks also handle session data left behind by older app versions.
if not isinstance(st.session_state.get("used_equations"), dict):
    st.session_state.used_equations = {name: [] for name in LEVELS}
for name in LEVELS:
    if not isinstance(st.session_state.used_equations.get(name), list):
        st.session_state.used_equations[name] = []
if not isinstance(st.session_state.get("problem_number"), int):
    st.session_state.problem_number = 0
if not isinstance(st.session_state.get("problem"), dict) or not {
    "level", "equation", "answer", "steps", "b"
}.issubset(st.session_state.problem):
    st.session_state.problem = None
if "hint" not in st.session_state:
    st.session_state.hint = None

level = st.selectbox("Choose your difficulty level:", LEVELS)
if st.session_state.get("last_level") != level:
    st.session_state.last_level = level
    st.session_state.problem = None
    st.session_state.hint = None

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

if st.button("Generate AI Problem", type="primary"):
    previous = st.session_state.used_equations[level][-5:]
    prompt = f"""
    You are generating practice exercises for differentiated mathematics teaching.
    Generate NEW integer parameters for a {level} linear equation.
    Return ONLY a JSON object with five integer keys: a, b, c, d, x.
    Ranges: a from 2 to 8; d from 1 to 8, d != a;
    b from -9 to 9 excluding 0; c from -9 to 9; x from -10 to 10.
    Vary the numbers and avoid these recent equations: {previous}.
    Basic uses x+b=right; Standard uses ax+b=right;
    Advanced uses a(x+b)+c=dx+e.
    The application will construct and independently check the equation.
    """
    try:
        with st.spinner("Gemini is generating a problem..."):
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            )
            if not response.text:
                raise ValueError("Empty Gemini response")
            parameters = validate_parameters(json.loads(response.text))
            new_problem = make_unique_problem(
                level, parameters, st.session_state.used_equations[level]
            )
            st.session_state.used_equations[level].append(new_problem["equation"])
            st.session_state.problem = new_problem
            st.session_state.hint = None
            st.session_state.problem_number += 1
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code in (429, 500, 503):
            st.warning(f"Gemini is temporarily busy (error {code}). Please try again shortly.")
        elif code in (400, 403, 404):
            st.error(f"Gemini request was rejected (error {code}). Check the model and API access.")
        else:
            st.error("Could not generate a valid problem. Please try again.")
        st.caption(f"Error type: {type(exc).__name__}")

problem = st.session_state.problem
if problem and problem["level"] == level:
    st.subheader(f"{level} — Solve the equation")
    st.markdown(f"### {problem['equation']}")

    answer_input = st.text_input(
        "Enter your answer for x:", key=f"answer_{st.session_state.problem_number}"
    )
    if st.button("Check Answer"):
        try:
            student_answer = float(answer_input)
            if abs(student_answer - problem["answer"]) < 1e-9:
                st.success("Correct! Well done!")
            else:
                st.warning("Not quite. Try again or request a hint.")
        except ValueError:
            st.warning("Please enter a number, such as 4 or -3.")

    if st.button("Get AI Hint"):
        hint_prompt = f"""
        Act as a supportive mathematics tutor. Topic: linear equations.
        Student level: {level}. Equation: {problem['equation']}.
        Give ONE short, mathematically correct hint in plain English.
        Basic: explain the next arithmetic operation simply.
        Standard: guide the student on isolating x.
        Advanced: suggest a strategy involving brackets and like terms.
        Do NOT reveal the numerical answer, write x = ..., or give a full solution.
        """
        try:
            with st.spinner("Gemini is preparing a hint..."):
                response = client.models.generate_content(model=MODEL, contents=hint_prompt)
                hint = (response.text or "").strip()
                if not hint or reveals_final_answer(hint):
                    hint = fallback_hint(problem)
                st.session_state.hint = hint
        except Exception:
            st.session_state.hint = fallback_hint(problem)
            st.caption("AI hint unavailable; showing a verified guidance hint instead.")

    if st.session_state.hint:
        st.info(st.session_state.hint)

    with st.expander("Show Step-by-Step Solution"):
        for number, step in enumerate(problem["steps"], start=1):
            st.write(f"{number}. {step}")
else:
    st.info("Select a level, then click 'Generate AI Problem'.")

st.caption("Gemini proposes parameters and hints; Python checks the mathematics.")

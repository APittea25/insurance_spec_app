import streamlit as st
import docx
import re
import openai
import os

# 🔐 OpenAI API key: fallback to environment variable for local dev
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

# Parse .docx into lines of text
def parse_docx(file):
    doc = docx.Document(file)
    content = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return content

# Extract structured function specs from the text
def extract_functions(content):
    functions = []
    current = {}
    mode = None  # Tracks if we're in Inputs, Logic, etc.

    for line in content:
        line = line.strip()

        # Detect function name (lowercase, no spaces, no colon)
        if line and not line.endswith(":") and not line.startswith("-") and " " not in line and line.islower():
            if current:
                functions.append(current)
            current = {"Function": line}
            mode = None

        elif line.lower().startswith("purpose:"):
            current["Purpose"] = line.split(":", 1)[1].strip()
            mode = None

        elif line.lower().startswith("inputs:"):
            current["Inputs"] = []
            mode = "Inputs"

        elif line.lower().startswith("output:"):
            current["Output"] = line.split(":", 1)[1].strip()
            mode = None

        elif line.lower().startswith("logic:"):
            current["Logic"] = []
            mode = "Logic"

        elif line.lower().startswith("validation:"):
            current["Validation"] = line.split(":", 1)[1].strip()
            mode = None

        elif line.startswith("-") and mode in {"Inputs", "Logic"}:
            current[mode].append(line.strip("- ").strip())

    if current:
        functions.append(current)

    return functions

# Call GPT to generate Python code from spec
def generate_code_from_spec(spec):
    prompt = f"""
Write a Python function based on the following actuarial specification:

Function Name: {spec.get('Function', 'function_name')}
Purpose: {spec.get('Purpose', '')}
Inputs:
{chr(10).join(spec.get('Inputs', []))}
Output: {spec.get('Output', '')}
Logic:
{chr(10).join(spec.get('Logic', []))}
Validation: {spec.get('Validation', '')}

Return only the Python code (with function definition and docstring).
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",  # You can switch to "gpt-3.5-turbo" if needed
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response['choices'][0]['message']['content']

# ----------------------------
# Streamlit App UI
# ----------------------------
st.set_page_config(page_title="Insurance Spec Code Generator", layout="wide")
st.title("🧮 Actuarial Spec to Python Code Generator")

uploaded_file = st.file_uploader("Upload a Word document (.docx)", type="docx")

if uploaded_file:
    st.success("✅ Document uploaded.")
    content = parse_docx(uploaded_file)
    specs = extract_functions(content)

    if not specs:
        st.warning("No function specs detected. Please check the document format.")
    else:
        for i, spec in enumerate(specs):
            with st.expander(f"🔧 {spec.get('Function', f'Function {i+1}')}"):
                st.markdown(f"**📌 Purpose:** {spec.get('Purpose', '')}")
                st.markdown("**🔣 Inputs:**")
                st.markdown("\n".join(f"- {inp}" for inp in spec.get("Inputs", [])))
                st.markdown(f"**📤 Output:** {spec.get('Output', '')}")
                st.markdown("**⚙️ Logic:**")
                st.markdown("\n".join(f"- {step}" for step in spec.get("Logic", [])))
                st.markdown(f"**🧪 Validation:** {spec.get('Validation', '')}")

                if st.button(f"Generate Python code for `{spec.get('Function', 'function')}`", key=i):
                    with st.spinner("🧠 Generating code using GPT..."):
                        code = generate_code_from_spec(spec)
                        st.code(code, language="python")

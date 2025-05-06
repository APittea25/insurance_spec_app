import streamlit as st
import docx
import re
import os
from openai import OpenAI

# Initialize OpenAI client using API key
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=api_key)

# Parse Word doc content
def parse_docx(file):
    doc = docx.Document(file)
    return [para.text.strip() for para in doc.paragraphs if para.text.strip()]

# Extract function specs from the document
def extract_functions(content):
    functions = []
    current = {}
    mode = None

    for line in content:
        line = line.strip()

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

# Generate Python code using OpenAI
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
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Insurance Spec Code Generator", layout="wide")
st.title("🧮 Actuarial Spec to Python Code Generator")

uploaded_file = st.file_uploader("Upload a Word document (.docx)", type="docx")

if uploaded_file:
    st.success("✅ Document uploaded.")
    content = parse_docx(uploaded_file)
    specs = extract_functions(content)

    if not specs:
        st.warning("⚠️ No function specs detected.")
    else:
        for i, spec in enumerate(specs):
            function_name = spec.get('Function') or f"Function {i+1}"
            with st.expander(f"🔧 {function_name}"):
                st.markdown(f"**📌 Purpose:** {spec.get('Purpose', '')}")
                st.markdown("**🔣 Inputs:**")
                st.markdown("\n".join(f"- {inp}" for inp in spec.get("Inputs", [])))
                st.markdown(f"**📤 Output:** {spec.get('Output', '')}")
                st.markdown("**⚙️ Logic:**")
                st.markdown("\n".join(f"- {step}" for step in spec.get("Logic", [])))
                st.markdown(f"**🧪 Validation:** {spec.get('Validation', '')}")

                if st.button(f"Generate Python code for `{function_name}`", key=i):
                    with st.spinner("🧠 Generating code using GPT..."):
                        code = generate_code_from_spec(spec)
                        st.code(code, language="python")

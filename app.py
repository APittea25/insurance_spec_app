import streamlit as st
import docx
import re
import openai

# Set up OpenAI key (use secrets.toml for Streamlit Cloud)
openai.api_key = st.secrets["OPENAI_API_KEY"]

def parse_docx(file):
    doc = docx.Document(file)
    content = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return content

def extract_functions(content):
    functions = []
    current = {}
    for line in content:
        if re.match(r"^[a-zA-Z_]+\(", line):  # function name
            if current:
                functions.append(current)
            current = {"Function": line.strip()}
        elif line.lower().startswith("purpose:"):
            current["Purpose"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("inputs:"):
            current["Inputs"] = []
        elif line.lower().startswith("-") and "Inputs" in current:
            current["Inputs"].append(line.strip("- ").strip())
        elif line.lower().startswith("output:"):
            current["Output"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("logic:"):
            current["Logic"] = []
        elif "Logic" in current and line.startswith("-"):
            current["Logic"].append(line.strip("- ").strip())
        elif line.lower().startswith("validation:"):
            current["Validation"] = line.split(":", 1)[1].strip()
    if current:
        functions.append(current)
    return functions

def generate_code_from_spec(spec):
    prompt = f"""
Write a Python function based on the following actuarial specification:

Function Name: {spec['Function']}
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
        model="gpt-4",  # or gpt-3.5-turbo
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response['choices'][0]['message']['content']

# Streamlit UI
st.title("🧮 Actuarial Spec to Python Code Generator")

uploaded_file = st.file_uploader("Upload a Word document (.docx)", type="docx")

if uploaded_file:
    st.success("Document uploaded successfully.")
    content = parse_docx(uploaded_file)
    specs = extract_functions(content)

    for i, spec in enumerate(specs):
        with st.expander(f"🔧 {spec['Function']}"):
            st.markdown(f"**Purpose:** {spec.get('Purpose', '')}")
            st.markdown("**Inputs:**")
            st.markdown("\n".join(f"- {inp}" for inp in spec.get("Inputs", [])))
            st.markdown(f"**Output:** {spec.get('Output', '')}")
            st.markdown("**Logic:**")
            st.markdown("\n".join(f"- {step}" for step in spec.get("Logic", [])))
            st.markdown(f"**Validation:** {spec.get('Validation', '')}")

            if st.button(f"Generate Python code for `{spec['Function']}`", key=i):
                with st.spinner("Generating code..."):
                    code = generate_code_from_spec(spec)
                    st.code(code, language="python")

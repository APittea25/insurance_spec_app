import streamlit as st
import docx
import re
import os
from openai import OpenAI

# Initialize OpenAI client using Streamlit secrets or environment variable
api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=api_key)

# Load and parse Word document
def parse_docx(file):
    doc = docx.Document(file)
    content = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
    return content

# Extract actuarial function specs from the document content
def extract_functions(content):
    functions = []
    current = {}
    mode = None  # Tracks which block we're in (Inputs, Logic, etc.)

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

# Generate Python code using OpenAI GPT
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
Validation: {

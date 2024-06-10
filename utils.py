import re

def extract_language(description):
    description_lower = description.lower()
    if 'javascript' in description_lower:
        return 'javascript'
    elif 'ruby' in description_lower:
        return 'ruby'
    else:
        return 'python'  # Default language

def clean_snippet(snippet):
    # Remove backticks from the beginning and end of the string
    cleaned_snippet = snippet.strip('`')
    
    # Remove the language identifier if it exists
    if cleaned_snippet.startswith('javascript'):
        cleaned_snippet = cleaned_snippet[len('javascript'):].strip()
    if cleaned_snippet.startswith('ruby'):
        cleaned_snippet = cleaned_snippet[len('ruby'):].strip()
    return cleaned_snippet

def extract_function_content(response_text: str, language: str):

    code_start = response_text.find('```')
    code_end = response_text.rfind('```')
    if code_start != -1 and code_end != -1:
        code =  response_text[code_start + 3:code_end].strip()
    else:
        code = response_text.strip()

    code = clean_snippet(code)
    # Regex to find the first function definition and its content up to the first return statement
    if language == 'python':
        pattern = r"(def\s+\w+\(.*?\):\s*(?:\n\s*.*)*?return\s+.*)"
    elif language == 'javascript':
        pattern = r"(function\s+\w+\(.*?\):\s*(?:\n\s*.*)*?return\s+.*)"
    else:
        pattern = r"(def\s+\w+\(.*?\):\s*(?:\n\s*.*)*?end\s+.*)"

    match = re.search(pattern, code, re.MULTILINE)
    
    if match:
        # Extract the function content
        function_content = match.group(1)
        function_content = clean_snippet(function_content)
        return function_content.strip()
    else:
        return clean_snippet(response_text)
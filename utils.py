import re
import openai

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

def find_function_name(code: str, language:str):
    # Using regular expression to extract function name
    if language != 'javascript':
        match = re.match(r"def\s+(\w+)\(", code)
    else:
        match = re.match(r"function\s+(\w+)\(", code)
    if match:
        return match.group(1)
    else:
        return "dummy"
    
def convert_to_assert_statements(test_output: str, code: str, language: str):
    import re
    # Extract the function name from the output
    # function_name = extract_function_name(test_output)
    function_name = find_function_name(code, language)
    # Regex pattern to match test cases in the given format
    pattern = r"Input:\s*(.+?)\s*Output:\s*(.+?)(?:\n|$)"
    if pattern is None:
        pattern = r"Input:\s*(.+?)\s*Expected Output:\s*(.+?)(?:\n|$)"
    matches = re.findall(pattern, test_output)

    # Generating assert statements
    assert_statements = []
    for input_val, expected_output in matches:
        # Clean input and output values
        input_val = input_val.strip().replace("=", "==").replace("==", " = ")
        expected_output = expected_output.strip()

        # Create the assert statement
        assert_statements.append(f"assert {function_name}({input_val}) == {expected_output}")
    
    return '\n'.join(assert_statements)
    
# Utility function to generate tests
def generate_tests(code: str, language: str):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate 5 test cases for the following {language} code:\n\n{code}. Strictly follow the following format for the test cases. for eg: 1. Test Case 1: \n Input: `` \n Output: ``"}
        ]
    )
    generated_test = response.choices[0].message.content
    return convert_to_assert_statements(generated_test, code, language)


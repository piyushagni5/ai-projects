from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional
import openai
import os
from dotenv import load_dotenv
import re
import utils

load_dotenv()

app = FastAPI()

# Load environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SnippetRequest(BaseModel):
    description: str
    language: str

class Snippet(BaseModel):
    id: int
    description: str
    language: str
    code: str
    tests: Optional[str] = None  # To store generated test cases

class Feedback(BaseModel):
    snippet_id: int
    feedback: str
    language: str

# In-memory database
snippets_db = []

# Counter for snippet IDs
snippet_id_counter = 1

# Utility function to generate code
def generate_code(description: str, language: str):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Generate a {language} code function using following {description}: \n\n Output Code as: \n def function_name(parameters): \n  Generate code below \n\n  Constraints : In the output, do not use any unnecessary lines, backticks and comments. Simply ouput cleaned code. \n"}
        ]
    )
    print('response:', response.choices[0].message.content)
    generated_def =  utils.extract_function_content(response.choices[0].message.content, language)
    return generated_def

# Serve the HTML file

@app.get("/", response_class=HTMLResponse)
async def get_home():
    return FileResponse('design.html')

# API Endpoints
@app.post("/generate", response_model=Snippet)
async def generate_snippet(request: SnippetRequest):
    global snippet_id_counter

    language = utils.extract_language(request.description)
    code = generate_code(request.description, language)
    print('code :', code)
    snippet = Snippet(id=snippet_id_counter, description=request.description, language=request.language, code=code)
    snippets_db.append(snippet)
    snippet_id_counter += 1
    
    return snippet

### get access of all the snippets generated
@app.get("/snippets", response_model=List[Snippet])
async def get_snippets():
    return snippets_db

@app.get("/snippets/{snippet_id}", response_model=Snippet)
async def get_snippet(snippet_id: int):
    for snippet in snippets_db:
        if snippet.id == snippet_id:
            return snippet
    raise HTTPException(status_code=404, detail="Snippet not found")

@app.put("/snippets/{snippet_id}", response_model=Snippet)
async def update_snippet(snippet_id: int, request: SnippetRequest):
    snippet = next((s for s in snippets_db if s.id == snippet_id), None)
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet not found")

    language = utils.extract_language(request.description)
    code = generate_code(request.description, language)
    snippet.description = request.description
    snippet.language = language
    snippet.code = code

    return snippet

@app.post("/feedback", response_model=Snippet)
async def improve_snippet(feedback: Feedback):
    snippet = next((s for s in snippets_db if s.id == feedback.snippet_id), None)
    print(snippet)
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet not found")

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Improve the following {snippet.language} code based on this feedback: {feedback.feedback}\n\n{snippet.code}"}
        ]
    )
    improved_code = utils.extract_function_content(response.choices[0].message.content, snippet.language)
    snippet.code = improved_code
    return snippet

@app.post("/generate-tests", response_model=str)
async def generate_tests_endpoint(snippet_id: int):
    snippet = next((s for s in snippets_db if s.id == snippet_id), None)
    if snippet is None:
        raise HTTPException(status_code=404, detail="Snippet not found")

    tests = utils.generate_tests(snippet.code, snippet.language)
    snippet.tests = tests
    # print('tests :', tests)
    return tests
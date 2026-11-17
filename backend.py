import os
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai
from google.genai import types

# 1. Load your secret API key from the .env file
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(title="AI Study & Document Assistant")

# Simple in-memory storage for the uploaded PDF text
document_store = {"text": "", "filename": None}

# --- CUSTOM TOOL FOR THE AI AGENT ---
def calculate_sgpa(credits: list[int], grade_points: list[int]) -> float:
    """Calculates SGPA given a list of course credits and corresponding grade points (out of 10)."""
    if not credits or len(credits) != len(grade_points):
        return 0.0
    total_points = sum(c * g for c, g in zip(credits, grade_points))
    return round(total_points / sum(credits), 2)

# --- API ENDPOINTS ---
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Extracts text from an uploaded PDF and stores it in memory."""
    reader = PdfReader(file.file)
    extracted_text = ""
    for page in reader.pages:
        extracted_text += (page.extract_text() or "") + "\n"
    
    document_store["text"] = extracted_text
    document_store["filename"] = file.filename
    return {"message": f"Successfully loaded '{file.filename}' ({len(reader.pages)} pages)."}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_with_assistant(request: ChatRequest):
    """Answers questions using the uploaded PDF context and Python tools."""
    try:
        pdf_context = document_store["text"][:25000]
        
        system_prompt = (
            "You are a helpful CSE study and productivity assistant. "
            "If document context is provided below, answer questions based on it and cite details accurately. "
            "If the user asks to calculate SGPA, use the calculate_sgpa tool.\n\n"
            f"--- UPLOADED DOCUMENT ({document_store['filename']}) ---\n{pdf_context}"
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[calculate_sgpa],
                temperature=0.3,
            ),
        )
        return {"reply": response.text}
    except Exception as e:
        return {"reply": f"⚠️ Exact Error: {str(e)}"}
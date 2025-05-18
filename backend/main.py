from fastapi import FastAPI, File, UploadFile, Form, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import shutil
import json
from typing import Optional

from backend.pdfquiz import set_pdf_path as set_quiz_pdf, pdf_agent as generate_quiz
from backend.pdfqa import answer_question_from_pdf, load_chat_history, save_chat_history

app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_index():
    return FileResponse("static/index.html")

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"filename": file.filename}

@app.post("/generate_quiz/")
async def generate_quiz_api(
    filename: str = Form(...),
    topic: str = Form(...),
    num_questions: int = Form(...),
    difficulty: str = Form(...)
):
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    set_quiz_pdf(pdf_path)
    result = generate_quiz(topic=topic, num_questions=num_questions, difficulty=difficulty)
    return JSONResponse(content=result)

@app.post("/ask_question/")
async def ask_question_api(
    filename: str = Form(...),
    message: str = Form(...),
    clear_history: Optional[bool] = Form(False)
):
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    
    # Clear history if requested
    if clear_history:
        save_chat_history(pdf_path, [])
    
    result = answer_question_from_pdf(pdf_path, message)
    return {"response": result}

@app.get("/chat_history/{filename}")
async def get_chat_history_api(
    filename: str,
    limit: Optional[int] = Query(None, description="Limit the number of history entries returned")
):
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    history = load_chat_history(pdf_path)
    
    # Apply limit if provided
    if limit is not None and limit > 0:
        history = history[-limit:]
        
    return {"history": history}

@app.delete("/chat_history/{filename}")
async def clear_chat_history(filename: str):
    pdf_path = os.path.join(UPLOAD_DIR, filename)
    save_chat_history(pdf_path, [])
    return {"message": "Chat history cleared successfully"}
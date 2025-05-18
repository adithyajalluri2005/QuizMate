# pro1.py
import typer
from rich.prompt import Prompt
from typing import Optional, List
from rich.pretty import pprint
from pydantic import BaseModel, Field
from agno.agent import Agent, RunResponse
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.chroma import ChromaDb
from agno.models.groq import Groq
from agno.embedder.sentence_transformer import SentenceTransformerEmbedder
import os
from dotenv import load_dotenv
import json

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise EnvironmentError("GROQ_API_KEY not set. Please set it in your .env file or environment variables.")

embeddings = SentenceTransformerEmbedder()
model = Groq(id="deepseek-r1-distill-llama-70b", api_key=groq_api_key)
model.timeout = 120
model.max_retries = 3

knowledge_base = None

DEFAULT_PDF_PATH = "attention.pdf"

def setup_knowledge_base(pdf_path=DEFAULT_PDF_PATH):
    return PDFKnowledgeBase(
        path=pdf_path,
        vector_db=ChromaDb(collection="recipes", embedder=embeddings)
    )

def set_pdf_path(pdf_path: str):
    global knowledge_base
    knowledge_base = setup_knowledge_base(pdf_path)
    knowledge_base.load(recreate=False)

class QuestionItem(BaseModel):
    question: str = Field(...)
    options: List[str] = Field(..., min_items=4, max_items=4)
    answer: str = Field(...)
    explanation: str = Field(...)

class QuizModel(BaseModel):
    questions: List[QuestionItem]

def create_system_prompt(topic: str, num_questions: int, difficulty: str) -> str:
    difficulty_descriptions = {
        "easy": "basic understanding and recall of fundamental concepts",
        "medium": "application of concepts and moderate analytical thinking",
        "hard": "advanced analysis, synthesis of multiple concepts, and deeper critical thinking"
    }

    difficulty_desc = difficulty_descriptions.get(difficulty.lower(), difficulty_descriptions["medium"])

    return (
        f"You are a helpful assistant that generates multiple-choice quiz questions based on PDF content. "
        f"Extract key concepts from the provided PDF focusing specifically on the topic of '{topic}' and create {num_questions} "
        f"{difficulty.lower()}-level quiz questions. '{difficulty.capitalize()}' difficulty means questions should require {difficulty_desc}.\n\n"
        f"Generate {num_questions} quiz questions and return them in valid JSON format with these exact keys:\n"
        "- questions: An array of question objects, where each object has the following structure:\n"
        "  - question: The quiz question\n"
        "  - options: List of 4 possible answers (one correct, three plausible distractors)\n"
        "  - answer: The correct answer (must be exactly one of the options)\n"
        "  - explanation: Brief explanation of why the answer is correct\n\n"
        "Only output the JSON object with exactly {num_questions} questions, nothing else. Ensure the output is valid JSON."
    )

def pdf_agent(topic: str = "attention mechanisms", num_questions: int = 10, difficulty: str = "medium", user: str = "user"):
    if not knowledge_base:
        return {"error": "PDF not loaded yet"}

    system_prompt = create_system_prompt(topic, num_questions, difficulty)

    agent = Agent(
        model=model,
        description=system_prompt,
        user_id=user,
        knowledge=knowledge_base
    )

    try:
        response: RunResponse = agent.run(timeout=600)

        content = response.content.strip() if response and hasattr(response, 'content') else ""

        if not content:
            return {"error": "Empty response from agent. Please try again."}

        if not content.startswith("{"):
            json_start = content.find("{")
            json_end = content.rfind("}")
            if json_start >= 0 and json_end >= 0:
                content = content[json_start:json_end+1]
            else:
                return {"error": "Could not extract valid JSON from response"}

        try:
            quiz_data = json.loads(content)
            validated_data = QuizModel(**quiz_data)

            actual_questions = len(validated_data.questions)
            if actual_questions != num_questions:
                print(f"Warning: Requested {num_questions} questions but got {actual_questions}")

            return quiz_data

        except json.JSONDecodeError as e:
            return {"error": f"JSON Parse Error: {str(e)}"}
        except Exception as e:
            return {"error": f"Validation Error: {str(e)}"}

    except Exception as e:
        return {"error": f"Agent Run Error: {str(e)}"}

def main(
    topic: str = typer.Option("attention mechanisms"),
    num_questions: int = typer.Option(10, min=1, max=50),
    difficulty: str = typer.Option("medium"),
    reload_knowledge: bool = typer.Option(False),
    pdf_path: str = typer.Option(DEFAULT_PDF_PATH),
    verbose: bool = typer.Option(False)
):
    if difficulty.lower() not in ["easy", "medium", "hard"]:
        return {"error": "Invalid difficulty"}

    if not os.path.exists(pdf_path):
        return {"error": "PDF path not found"}

    set_pdf_path(pdf_path)

    return pdf_agent(topic=topic, num_questions=num_questions, difficulty=difficulty)

if __name__ == "__main__":
    typer.run(main)

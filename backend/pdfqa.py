import os
import json
import uuid
import time
from typing import Dict, List, Any

from dotenv import load_dotenv
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Validate and load Groq API key
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise EnvironmentError("GROQ_API_KEY not set. Please set it in your .env file or environment variables.")

# Set up Groq LLM
llm = ChatGroq(model="deepseek-r1-distill-llama-70b", groq_api_key=groq_api_key)

# Set up embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Chat history storage configuration
CHAT_HISTORY_DIR = "chat_history"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

MAX_HISTORY_ENTRIES = 5
MAX_ENTRY_LENGTH = 500

def get_pdf_id(pdf_path: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pdf_path))

def save_chat_history(pdf_path: str, history: List[Any]) -> None:
    pdf_id = get_pdf_id(pdf_path)
    history_file = os.path.join(CHAT_HISTORY_DIR, f"{pdf_id}.json")
    with open(history_file, 'w') as f:
        json.dump(history, f)

def load_chat_history(pdf_path: str) -> List[Any]:
    pdf_id = get_pdf_id(pdf_path)
    history_file = os.path.join(CHAT_HISTORY_DIR, f"{pdf_id}.json")
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def convert_history_format(history: List[Any]) -> List[Dict[str, Any]]:
    converted = []
    for entry in history:
        if isinstance(entry, dict) and "question" in entry and "answer" in entry:
            if "timestamp" not in entry:
                entry["timestamp"] = time.time()
            converted.append(entry)
        elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
            converted.append({
                "question": entry[0],
                "answer": entry[1],
                "timestamp": time.time()
            })
    return converted

def get_vectorstore(pdf_path: str):
    pdf_id = get_pdf_id(pdf_path)
    persist_directory = f"chroma_db_{pdf_id}"

    if os.path.exists(persist_directory) and os.path.isdir(persist_directory):
        try:
            return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        except Exception:
            pass

    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    splits = splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=persist_directory,
    )
    return vectorstore

def truncate_text(text: str, max_length: int) -> str:
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= max_length:
        return text

    cutoff = max_length - 3
    last_period = text[:cutoff].rfind('.')
    last_question = text[:cutoff].rfind('?')
    last_exclamation = text[:cutoff].rfind('!')
    sentence_break = max(last_period, last_question, last_exclamation)

    if sentence_break > 0.7 * cutoff:
        return text[:sentence_break + 1] + "..."
    else:
        last_space = text[:cutoff].rfind(' ')
        if last_space > 0:
            return text[:last_space] + "..."
        else:
            return text[:cutoff] + "..."

def prepare_history_for_prompt(history: List[Any], max_entries: int = 5) -> str:
    if not history:
        return "No previous conversation."
    history = convert_history_format(history)
    recent_history = history[-max_entries:]
    formatted_entries = []
    for entry in recent_history:
        question = truncate_text(entry.get("question", ""), MAX_ENTRY_LENGTH)
        answer = truncate_text(entry.get("answer", ""), MAX_ENTRY_LENGTH)
        formatted_entries.append(f"User: {question}\nAssistant: {answer}")
    return "\n\n".join(formatted_entries)

# --- Output Enhancement Chain ---
output_enhancement_prompt = PromptTemplate.from_template(
    "Improve the clarity and readability of the following answer while keeping it accurate and concise:\n\n{raw_answer}"
)
parser=StrOutputParser()
enhance_output_chain = output_enhancement_prompt|llm|parser

def enhance_answer(raw_answer: str) -> str:
    try:
        result = enhance_output_chain.invoke({"raw_answer": raw_answer})
        return result.get("text", raw_answer).strip()
    except Exception:
        return raw_answer

# --- Main PDF QA function ---
def answer_question_from_pdf(pdf_path: str, user_input: str) -> str:
    try:
        full_history = load_chat_history(pdf_path)
        full_history = convert_history_format(full_history)
        vectorstore = get_vectorstore(pdf_path)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Professional and concise prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a knowledgeable, professional assistant. Your goal is to respond clearly and concisely to user questions. "
             "Use only the relevant background information provided. Avoid speculation and do not reference the source of your knowledge."),
            ("human", 
             "Conversation so far:\n{history}\n\nQuestion:\n{input}\n\nReference material:\n{context}")
        ])

        qa_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, qa_chain)

        history_text = prepare_history_for_prompt(full_history, MAX_HISTORY_ENTRIES)

        result = rag_chain.invoke({"input": user_input, "history": history_text})
        raw_answer = result.get("answer", "I'm not sure how to answer that based on the information.")

        # ✨ Enhance the raw answer
        enhanced_answer = enhance_answer(raw_answer)

        # Save chat history with enhanced answer
        full_history.append({
            "question": user_input,
            "answer": enhanced_answer,
            "timestamp": time.time()
        })
        save_chat_history(pdf_path, full_history)

        return enhanced_answer
    except Exception as e:
        return f"Error processing your question: {str(e)}"

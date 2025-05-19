# QuizMate

**QuizMate** is an interactive web-based quiz application designed to provide users with an engaging platform to test and enhance their knowledge across various subjects. Built using modern web technologies, QuizMate offers a seamless and responsive user experience.

---

## ✅ Key Features

- 📄 **PDF Upload**  
  Upload any content-rich academic or professional PDF. The system securely stores the file and prepares it for semantic search and AI interaction.

- 🤖 **AI-Powered Q&A**  
  Ask natural language questions from the uploaded document. Using **LLMs (Groq + DeepSeek LLaMA)** and **vector search**, the assistant retrieves the most relevant content and generates clear, concise answers.

- 🧠 **Dynamic Quiz Generation**  
  Automatically generate multiple-choice questions (MCQs) from a chosen topic within the PDF. Each quiz includes:
  - 4 answer options  
  - A correct answer  
  - An explanation

- 🎯 **Difficulty Customization**  
  Choose the complexity of questions — **Easy**, **Medium**, or **Hard** — to match learning goals or testing depth.

- 💬 **Conversational Memory**  
  Maintains contextual history of previous questions and answers for a more natural, flowing user interaction. Ideal for follow-up questions and continuous learning sessions.

- 🌐 **Clean REST API**  
  Built using **FastAPI**, the backend exposes well-documented endpoints that are easy to consume via frontend interfaces or other services:
  - `/upload_pdf/`  
  - `/ask_question/`  
  - `/generate_quiz/`  
  - `/chat_history/`


## 🖼️ Screenshots

![quiz-1](https://github.com/user-attachments/assets/bede7357-c57a-46f0-a2ba-83889761fa30)
![quiz-2](https://github.com/user-attachments/assets/4caabfdb-5bb5-4a91-ba3c-9d99fff1ee3c)
![quiz-3](https://github.com/user-attachments/assets/f0fd461c-a374-4b76-aefc-2f294f9045e1)
![quiz-4](https://github.com/user-attachments/assets/d93480b3-a014-4166-8b53-11c63840baa5)

---



## 🛠️ Tech Stack

### Frontend:
- HTML5  
- CSS3  
- JavaScript  

### Backend:
- Python (Flask or Django)

### Database:
- SQLite / MySQL

### Version Control:
- Git & GitHub

---


## 📁 Project Structure
<pre> ``` QuizMate/ ├── backend/ │ ├── app.py │ ├── models.py │ └── ... ├── static/ │ ├── css/ │ ├── js/ │ └── images/ ├── templates/ │ ├── index.html │ ├── quiz.html │ └── ... ├── README.md └── requirements.txt ``` </pre>

---

## 🚀 Getting Started

### Prerequisites

- Python 3.x  
- pip (Python package installer)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/adithyajalluri2005/QuizMate.git
   cd QuizMate
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
3. Run the application:
   ```bash
   python backend/app.py

4. Open your browser and navigate to:
   ```bash
   http://localhost:5000

## 📬 Contact
### Author: Adithya Jalluri

### GitHub: adithyajalluri2005








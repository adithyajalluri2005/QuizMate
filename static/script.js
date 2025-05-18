document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');
  let uploadedQuizFilename = "";
  let uploadedChatFilename = "";

  // Tab Switching
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      const tabId = button.getAttribute('data-tab');
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      button.classList.add('active');
      document.getElementById(tabId).classList.add('active');
    });
  });

  // ===================== Quiz Setup =====================

  const fileInput = document.getElementById('pdf-file');
  const fileInfo = document.querySelector('.file-info');
  const fileName = document.getElementById('file-name');
  const removeFile = document.querySelector('.remove-file');

  fileInput.addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("http://localhost:8000/upload_pdf/", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      uploadedQuizFilename = data.filename;
      fileName.textContent = file.name;
      fileInfo.classList.remove('hidden');
    }
  });

  removeFile.addEventListener('click', () => {
    fileInput.value = '';
    uploadedQuizFilename = '';
    fileInfo.classList.add('hidden');
  });

  const quizForm = document.getElementById('quiz-form');
  const quizSetup = document.getElementById('quiz-setup');
  const loadingScreen = document.getElementById('loading');
  const quizContainer = document.getElementById('quiz-container');
  const resultsContainer = document.getElementById('results-container');
  const questionContainer = document.getElementById('question-container');
  const questionNumber = document.getElementById('question-number');
  const scoreDisplay = document.getElementById('score-display');
  const progressBar = document.querySelector('.progress');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const submitQuizBtn = document.getElementById('submit-quiz');
  const finalScoreDisplay = document.getElementById('final-score');
  const resultsListDisplay = document.getElementById('results-list');
  const newQuizBtn = document.getElementById('new-quiz');

  let currentQuestion = 0;
  let score = 0;
  let userAnswers = [];
  let questions = [];

  quizForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!uploadedQuizFilename) {
      alert('Please upload a PDF file first.');
      return;
    }

    const topic = document.getElementById("topic").value;
    const numQuestions = document.getElementById("num-questions").value;
    const difficulty = document.getElementById("difficulty").value;

    quizSetup.classList.add('hidden');
    loadingScreen.classList.remove('hidden');

    const formData = new FormData();
    formData.append("filename", uploadedQuizFilename);
    formData.append("topic", topic);
    formData.append("num_questions", numQuestions);
    formData.append("difficulty", difficulty);

    try {
      const res = await fetch("http://localhost:8000/generate_quiz/", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (data.questions) {
        questions = data.questions;
        userAnswers = Array(questions.length).fill(null);
        currentQuestion = 0;
        score = 0;
        loadingScreen.classList.add('hidden');
        quizContainer.classList.remove('hidden');
        displayQuestion(currentQuestion);
      } else {
        throw new Error(data.error || "Unknown error");
      }
    } catch (err) {
      alert("Error generating quiz: " + err.message);
      quizSetup.classList.remove('hidden');
      loadingScreen.classList.add('hidden');
    }
  });

  function displayQuestion(index) {
    const question = questions[index];
    questionNumber.textContent = `Question ${index + 1} of ${questions.length}`;
    const progressPercentage = ((index + 1) / questions.length) * 100;
    progressBar.style.width = `${progressPercentage}%`;

    const questionHTML = `
      <div class="question">${question.question}</div>
      <div class="options">
        ${question.options.map((option, i) => `
          <div class="option ${userAnswers[index] === i ? 'selected' : ''}" data-index="${i}">
            ${option}
          </div>
        `).join('')}
      </div>
    `;

    questionContainer.innerHTML = questionHTML;

    const optionElements = questionContainer.querySelectorAll('.option');
    optionElements.forEach(option => {
      option.addEventListener('click', () => {
        optionElements.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        userAnswers[index] = parseInt(option.getAttribute('data-index'));
        nextBtn.disabled = false;
      });
    });

    prevBtn.disabled = index === 0;
    nextBtn.disabled = userAnswers[index] === null;

    if (index === questions.length - 1) {
      nextBtn.classList.add('hidden');
      submitQuizBtn.classList.remove('hidden');
    } else {
      nextBtn.classList.remove('hidden');
      submitQuizBtn.classList.add('hidden');
    }
  }

  prevBtn.addEventListener('click', () => {
    if (currentQuestion > 0) {
      currentQuestion--;
      displayQuestion(currentQuestion);
    }
  });

  nextBtn.addEventListener('click', () => {
    if (currentQuestion < questions.length - 1) {
      currentQuestion++;
      displayQuestion(currentQuestion);
    }
  });

  submitQuizBtn.addEventListener('click', () => {
    score = 0;
    userAnswers.forEach((answer, index) => {
      if (answer === questions[index].options.indexOf(questions[index].answer)) {
        score++;
      }
    });

    quizContainer.classList.add('hidden');
    resultsContainer.classList.remove('hidden');
    finalScoreDisplay.textContent = `You scored ${score} out of ${questions.length}`;

    let resultsHTML = '';
    questions.forEach((question, index) => {
      const isCorrect = userAnswers[index] === question.options.indexOf(question.answer);
      resultsHTML += `
  <div class="result-item">
    <p><strong>${index + 1}. ${question.question}</strong></p>
    <p>Your answer: ${question.options[userAnswers[index]]}</p>

    <div class="answer-box">
      <strong>Correct answer:</strong> ${question.answer}
    </div>

    <div class="explanation-box">
      <strong>Explanation:</strong> ${question.explanation}
    </div>

    <p class="${isCorrect ? 'correct' : 'incorrect'}">
      ${isCorrect ? '✓ Correct' : '✗ Incorrect'}
    </p>
  </div>
`;
    });

    resultsListDisplay.innerHTML = resultsHTML;
  });

  newQuizBtn.addEventListener('click', () => {
    resultsContainer.classList.add('hidden');
    quizSetup.classList.remove('hidden');
  });

  // ===================== Chat Setup =====================

  const chatFileInput = document.getElementById('chat-pdf-upload');
  const chatFileInfo = document.getElementById('chat-file-info');
  const chatFileName = document.getElementById('chat-file-name');
  const chatRemoveFile = document.getElementById('chat-remove-file');
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('user-message');

  chatFileInput.addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (file) {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/upload_pdf/", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    uploadedChatFilename = data.filename;

    chatFileName.textContent = file.name;
    chatFileInfo.classList.remove('hidden');

    chatMessages.innerHTML += `
      <div class="message system"><div class="message-content">
        PDF "${file.name}" uploaded. You can now ask questions about it.
      </div></div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
});

  chatRemoveFile.addEventListener('click', () => {
    chatFileInput.value = '';
    uploadedChatFilename = '';
    chatFileInfo.classList.add('hidden');

    chatMessages.innerHTML += `
      <div class="message system"><div class="message-content">
        PDF removed. Please upload a new PDF to continue.
      </div></div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
  });

  chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    if (!uploadedChatFilename) {
      chatMessages.innerHTML += `
        <div class="message system"><div class="message-content">
          Please upload a PDF file first.
        </div></div>`;
      chatMessages.scrollTop = chatMessages.scrollHeight;
      return;
    }

    chatMessages.innerHTML += `
      <div class="message user"><div class="message-content">${userMessage}</div></div>`;
    chatInput.value = '';

    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>`;
    chatMessages.appendChild(typingIndicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    const formData = new FormData();
    formData.append("filename", uploadedChatFilename);
    formData.append("message", userMessage);

    try {
      const res = await fetch("http://localhost:8000/ask_question/", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      typingIndicator.remove();
      chatMessages.innerHTML += `
        <div class="message system"><div class="message-content">
          ${data.response}
        </div></div>`;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (err) {
      typingIndicator.remove();
      chatMessages.innerHTML += `
        <div class="message system"><div class="message-content">
          Error: ${err.message}
        </div></div>`;
    }
  });
});
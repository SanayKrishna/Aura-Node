# Aura Node 🤖

**Aura Node is a full-stack, AI-powered chat assistant designed to be your personal expert for building PCs. It leverages the power of large language models and real-time web search to provide accurate, up-to-date answers to all your hardware compatibility, installation, and troubleshooting questions.**

This project is a complete implementation of a modern AI application, featuring a sleek, responsive frontend and a powerful, intelligent backend.



## ✨ Features

*   **Intelligent Chat Interface:** A clean, modern, and responsive UI built with Next.js and Tailwind CSS.
*   **Live Research Agent:** The AI is not limited to pre-fed knowledge. For every question, it performs a live Google search to find the most relevant, up-to-the-minute information.
*   **Natural Language Understanding:** Powered by Google's Gemini Pro, the bot can understand complex, technical questions.
*   **Clean, Formatted Answers:** Advanced prompt engineering ensures the AI provides clear, readable answers without messy special characters.
*   **Scalable Architecture:** A decoupled frontend and backend, perfect for future expansion and development.

---

## 🛠️ Tech Stack

This project is a demonstration of a modern, full-stack AI architecture.

#### **Frontend (UI)**
*   **Framework:** [Next.js](https://nextjs.org/) (React)
*   **Styling:** [Tailwind CSS](https://tailwindcss.com/)
*   **Icons:** [Lucide React](https://lucide.dev/)
*   **Language:** TypeScript

#### **Backend (API)**
*   **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **AI Orchestration:** [LangChain](https://www.langchain.com/)
*   **Core AI Model:** [Google Gemini Pro](https://deepmind.google/technologies/gemini/)

#### **AI Core & Tools**
*   **LLM & Embeddings:** Google Gemini API
*   **Live Data Source:** Google Custom Search API
*   **Autonomous Agent:** The backend features a "Live Researcher Agent" that uses Google Search as a tool to find real-time context for every user query.

---

## 🚀 Getting Started

To run this project locally, you will need two separate terminals.

### Prerequisites

*   Python 3.10+
*   Node.js (LTS version)
*   Git
*   API keys for Google AI (Gemini) and Google Custom Search.

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt 
    ```
    *(**Note:** You will need to create a `requirements.txt` file. See the section below.)*

4.  **Set up environment variables:**
    *   Create a file named `.env` in the `backend` directory.
    *   Add your API keys to it (see `.env.example` for the format).

5.  **Run the server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend will be running at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install dependencies:**
    ```bash
    npm install
    ```

3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The frontend will be running at `http://localhost:3000`.

---

## 📝 Next Steps: Creating `requirements.txt`

To make your backend easy for others to set up, it's best practice to create a `requirements.txt` file.

1.  Navigate to your `backend` directory in the terminal.
2.  Make sure your virtual environment is active.
3.  Run the following command:
    ```bash
    pip freeze > requirements.txt
    ```
This command will automatically generate a list of all the Python packages your project needs. Be sure to commit this new file to your GitHub repository!

```bash
git add backend/requirements.txt
git commit -m "Add backend requirements file"
git push
```
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_google_community import GoogleSearchAPIWrapper  # ✅ Correct new import
from langchain.tools import Tool  # ✅ Correct import for Tool

# --- 1. Load Environment Variables ---
load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")

if not all([google_api_key, google_cse_id, google_search_api_key]):
    raise ValueError("❌ Missing one or more required Google API keys in .env")

# --- 2. Initialize the LLM and Google Search tool ---
print("🚀 Initializing LLM and Google Search tool...")

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.5,
    google_api_key=google_api_key
)

# Set up environment variables for Google Search
os.environ["GOOGLE_CSE_ID"] = google_cse_id
os.environ["GOOGLE_API_KEY"] = google_search_api_key

# Initialize Google Search API Wrapper (✅ no `num` argument)
search_wrapper = GoogleSearchAPIWrapper(k=5)

# Restrict search to PC build-related websites
google_search_tool = Tool(
    name="google_search",
    description="Search Google for PC build-related information and prices in India.",
    func=lambda query: search_wrapper.run(
        f"{query} site:pcpartpicker.com OR site:mdcomputers.in OR site:vedantcomputers.com OR site:amazon.in"
    ),
)

# --- 3. Define improved prompt ---
template = """
💻 PC & Tech Assistant (India)

You are an expert PC and technology assistant. You help users with:
- Building optimized gaming and workstation PCs
- Troubleshooting PC errors and issues
- Checking system compatibility (motherboards, CPUs, GPUs, RAM, etc.)
- General PC-related guidance and advice

You will receive:
- The user's question
- A set of recent Google search results

Use search results for relevant, recent information (prices, specs, compatibility).  
If results are insufficient, rely on your expertise to provide the best solution.

⚠️ Important Output Style Instructions:
- Do NOT use asterisks `**` for bold text anywhere
- Do NOT use underscores `_` for italics
- Emphasize sections using emojis, headings, spacing, and subtle formatting
- Keep the text visually appealing, readable, and structured
- Use numbered or bulleted lists where needed
- Add emojis for components, steps, or important points, but avoid excessive symbols

Structure your answer using these sections:

🔹 Overview
- Briefly restate the user's question or issue
- Describe the goal or type of solution

🔹 Recommendation / Solution
- For PC builds: List components with reasoning and approximate prices  
- For troubleshooting: List steps clearly, numbered or bulleted, with explanations  
- For compatibility checks: Provide clear suggestions or alternatives

🔹 Tips & Alternatives
- Optional upgrades, budget alternatives, troubleshooting advice, or compatibility notes

🔹 Summary
- Provide a short, clear paragraph summarizing the solution, recommendation, or build suitability

---
Search Results:  
{context}

User's Question:  
{question}

Generate a complete, clean, and visually appealing response following these instructions.
"""



prompt = ChatPromptTemplate.from_template(template)

# --- 4. Pydantic Model ---
class Question(BaseModel):
    text: str

# --- 5. FastAPI App ---
app = FastAPI(title="PC Build Buddy - Live Research API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update if your frontend URL differs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 6. Define the Live Research Chain ---
live_research_chain = (
    {"context": google_search_tool, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- 7. API Endpoints ---
@app.post("/ask")
def process_question(question: Question):
    print(f"🧠 Received question: {question.text}")
    print("🔍 Running live research chain...")
    
    response = live_research_chain.invoke(question.text)
    
    print("✅ Chain completed. Returning response.")
    return {"response": response}

@app.get("/")
def read_root():
    return {"message": "Welcome to the PC Build Buddy - Live Research API!"}

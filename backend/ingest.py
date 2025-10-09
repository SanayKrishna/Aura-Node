import os
import time
from dotenv import load_dotenv
from typing import List

# LangChain core and agent imports
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain import hub
from langchain_core.documents import Document

# Google LLM + Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Modern Google Search tool
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Supabase
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import create_client, Client


# --- 1. Load Environment Variables ---
load_dotenv()
os.environ["USER_AGENT"] = "Mozilla/5.0 (compatible; PCBuildBuddy/1.0; +https://pcbuildbuddy.com)"

google_api_key = os.getenv("GOOGLE_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")

if not all([google_api_key, supabase_url, supabase_key, google_cse_id, google_search_api_key]):
    raise ValueError("One or more required environment variables are missing. Please check your .env file.")


# --- 2. Configuration ---
TOPIC_TO_RESEARCH = "NVIDIA GeForce RTX 4080 Super"


# --- 3. Initialize Models and Clients ---
print("Initializing models and clients...")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.1,
    google_api_key=google_api_key
)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=google_api_key
)
supabase: Client = create_client(supabase_url, supabase_key)


# --- 4. Set Up Google Search Tool ---
print("Setting up agent tools...")
os.environ["GOOGLE_CSE_ID"] = google_cse_id
os.environ["GOOGLE_API_KEY"] = google_search_api_key

search_wrapper = GoogleSearchAPIWrapper(k=5)
google_search_tool = Tool(
    name="google_search",
    description="Search Google for recent results. Input should be a search query.",
    func=search_wrapper.run,
)


# --- 5. Define Research Agent ---
def run_research_agent(topic: str):
    """
    Runs a ReAct agent to research a topic, find relevant URLs,
    scrape them, and ingest the content into Supabase.
    """

    # --- A. Load and Customize the Prompt ---
    prompt = hub.pull("hwchase17/react")
    prompt.template = f"""
    You are a world-class researcher for a PC hardware company. Your goal is to find the most authoritative and detailed information on a given topic.

    Your task is to research the following topic: "{topic}"

    You have access to the following tool:
    {{tools}}

    Use this exact format:

    Question: the input question you must answer
    Thought: what you think you should do
    Action: the action to take, should be one of [{{tool_names}}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: A clean, comma-separated list of the 3 best URLs you found.

    Begin!

    Question: Find the 3 most authoritative and detailed web pages about the topic: {topic}
    {{agent_scratchpad}}
    """

    agent = create_react_agent(
        llm=llm,
        tools=[google_search_tool],
        prompt=prompt,
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=[google_search_tool],
        verbose=True,
        handle_parsing_errors=True,
    )

    # --- B. Run Agent with Retry Logic ---
    print(f"\n--- Running Research Agent for topic: '{topic}' ---")
    for attempt in range(3):
        try:
            response = agent_executor.invoke(
                {"input": f"Find the 3 most authoritative and detailed web pages about {topic}."}
            )
            break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                print("Retrying in 5 seconds...")
                time.sleep(5)
            else:
                raise

    url_list_str = response.get("output", "")
    urls = [url.strip() for url in url_list_str.split(",") if url.strip().startswith("http")]

    if not urls:
        print("\nAgent did not return any valid URLs. Exiting.")
        return

    print(f"\nAgent identified the following URLs:\n" + "\n".join(f"- {url}" for url in urls))


    # --- C. Scrape and Process the Content ---
    print("\n--- Scraping and Processing Content ---")
    all_chunks: List[Document] = []

    try:
        loader = WebBaseLoader(urls)
        loader.requests_per_second = 1
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        chunks = text_splitter.split_documents(documents)
        all_chunks.extend(chunks)

        print(f"  -> Successfully processed {len(chunks)} chunks.")
    except Exception as e:
        print(f"  -> Error scraping/processing URLs: {e}")
        return

    if not all_chunks:
        print("\nNo content was processed. Exiting.")
        return


    # --- D. Ingest Data into Supabase ---
    table_name = "documents"
    try:
        print(f"\n--- Clearing and Ingesting Data into Supabase ---")
        print(f"  -> Clearing existing data from '{table_name}' table...")
        supabase.from_(table_name).delete().neq("content", "this will never be the content").execute()
        print("     Cleared old records successfully.")
    except Exception as e:
        print(f"     Error clearing table: {e}")

    print(f"  -> Ingesting {len(all_chunks)} new chunks...")
    SupabaseVectorStore.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        client=supabase,
        table_name=table_name,
        query_name="match_documents",
        chunk_size=500,
    )

    print("\n--- Autonomous ingestion complete! ✅ ---")


# --- 6. Run the Script ---
if __name__ == "__main__":
    run_research_agent(TOPIC_TO_RESEARCH)

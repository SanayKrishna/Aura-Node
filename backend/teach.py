# In backend/teach.py

import os
import sys  # We need this to read command-line arguments
from dotenv import load_dotenv

# All the LangChain imports remain the same
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain import hub
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import GoogleSearchRun, GoogleSearchAPIWrapper
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import create_client, Client

# --- 1. Load Environment Variables and Initialize Clients ---
load_dotenv()
# ... [All the key loading and client initialization code is the same as ingest.py] ...
google_api_key = os.getenv("GOOGLE_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")
google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")

if not all([google_api_key, supabase_url, supabase_key, google_cse_id, google_search_api_key]):
    raise ValueError("One or more required environment variables are missing. Please check your .env file.")

llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1, google_api_key=google_api_key)
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)
supabase: Client = create_client(supabase_url, supabase_key)

# --- 2. The Agent Logic (as a function) ---
def run_research_agent(topic: str, should_clear: bool = False):
    """
    Runs the research agent for a given topic.
    If should_clear is True, it wipes the database before ingesting.
    """
    # ... [The entire agent logic from ingest.py (defining tools, prompt, executor)] ...
    os.environ["GOOGLE_CSE_ID"] = google_cse_id
    os.environ["GOOGLE_API_KEY"] = google_search_api_key
    search_wrapper = GoogleSearchAPIWrapper(k=5)
    google_search_tool = Tool(
        name="google_search",
        description="Search Google for recent results. Input should be a search query.",
        func=search_wrapper.run,
    )
    prompt = hub.pull("hwchase17/react")
    prompt.template = f"""
    You are a world-class researcher... [The rest of the long prompt is exactly the same] ...
    Question: Find the 3 most authoritative and detailed web pages about the topic: {topic}
    {{agent_scratchpad}}
    """
    agent = create_react_agent(llm=llm, tools=[google_search_tool], prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[google_search_tool], verbose=True, handle_parsing_errors=True)
    
    # --- Run agent to get URLs ---
    print(f"\n--- Running Research Agent for topic: '{topic}' ---")
    try:
        response = agent_executor.invoke({"input": prompt.template})
        url_list_str = response['output']
        urls = [url.strip() for url in url_list_str.split(',') if url.strip().startswith('http')]
        if not urls:
            print("\nAgent did not return any valid URLs. Exiting.")
            return
        print(f"\nAgent identified the following URLs:\n" + "\n".join(f"- {url}" for url in urls))
    except Exception as e:
        print(f"\nError during agent execution: {e}")
        return

    # --- Scrape and Process Content ---
    print("\n--- Scraping and Processing Content ---")
    try:
        loader = WebBaseLoader(urls)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
        all_chunks = text_splitter.split_documents(documents)
        print(f"  -> Successfully processed content into {len(all_chunks)} chunks.")
    except Exception as e:
        print(f"  -> Error scraping/processing URLs: {e}")
        return
    
    if not all_chunks:
        print("\nNo content was processed. Exiting.")
        return

    # --- Clear (Optional) and Ingest Data ---
    table_name = "documents"
    if should_clear:
        try:
            print(f"\n--- Clearing all existing data from '{table_name}' table ---")
            supabase.from_(table_name).delete().neq("content", "this will never be the content").execute()
            print("     Cleared old records successfully.")
        except Exception as e:
            print(f"     Error clearing table: {e}")

    print(f"\n--- Ingesting {len(all_chunks)} new chunks into Supabase ---")
    SupabaseVectorStore.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        client=supabase,
        table_name=table_name,
        query_name="match_documents",
        chunk_size=500,
    )
    print("\n--- Autonomous ingestion complete! ---")


# --- 3. Main Script Execution ---
if __name__ == "__main__":
    # Check if a topic was provided as a command-line argument
    if len(sys.argv) > 1:
        # Join all arguments after the script name to form the topic
        topic_to_research = " ".join(sys.argv[1:])
        
        # Optional: Check for a "--clear" flag
        should_clear_db = "--clear" in topic_to_research
        if should_clear_db:
            # Remove the flag from the topic string
            topic_to_research = topic_to_research.replace("--clear", "").strip()

        run_research_agent(topic_to_research, should_clear=should_clear_db)
    else:
        print("\nUsage: python teach.py \"<your topic here>\" [--clear]")
        print("Example: python teach.py \"How to install a Noctua NH-D15 cooler\"")
        print("         Add --clear to wipe the database before adding new knowledge.")
"""List the Gemini models your API key can use. Reads GOOGLE_API_KEY from backend/.env."""
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("Set GOOGLE_API_KEY in backend/.env first.")

genai.configure(api_key=api_key)
for m in genai.list_models():
    print(m.name)

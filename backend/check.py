import google.generativeai as genai
genai.configure(api_key="REDACTED")

for m in genai.list_models():
    print(m.name)

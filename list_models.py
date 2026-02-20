import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)

print("Available Gemini models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")

"""
Script to list available Gemini models for debugging
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in environment variables")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available Gemini models:\n")
try:
    models = genai.list_models()
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name
            # Extract short name
            short_name = model_name.split('/')[-1] if '/' in model_name else model_name
            print(f"✓ {short_name}")
            print(f"  Full name: {model_name}")
            print(f"  Methods: {model.supported_generation_methods}")
            print()
except Exception as e:
    print(f"Error listing models: {e}")
    print("\nTrying common model names directly:")
    for model_name in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            print(f"✓ {model_name} - Available")
        except Exception as err:
            print(f"✗ {model_name} - Not available: {err}")


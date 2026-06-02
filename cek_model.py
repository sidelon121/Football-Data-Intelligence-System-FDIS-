import os
from google import genai
from dotenv import load_dotenv

# Load .env agar API key terbaca
load_dotenv() 

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Mencari model yang tersedia untuk API Key Anda...")
print("-" * 40)

# Menampilkan semua model yang bisa digunakan
for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(model.name)
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# 1. Dynamically build the path to app/chatbot.env
# Assuming the file you are pasting this into is in your project root
current_dir = Path(__file__).resolve().parent
env_path = current_dir / 'chatbot.env'

# Or, if this code is inside app/src/ai.py, use this path instead:
# env_path = Path(__file__).resolve().parent.parent / 'chatbot.env'

print(f"🔍 DEBUG: Loading env from: {env_path}")

# 2. Explicitly tell load_dotenv to read THIS specific file
load_dotenv(dotenv_path=env_path)

# 3. Fetch the API key
API_KEY = os.getenv("GEMINI_API_KEY")

# 4. Initialize Client
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY is still not found. Check the path!")
    client = None
else:
    try:
        client = genai.Client(api_key=API_KEY)
        print("✅ Gemini API connected successfully.")
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        client = None
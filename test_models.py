from google import genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get API key from .env file
api_key = os.getenv("GEMINI_API_KEY")

# Check if API key exists
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env file")
    exit()

# Create Gemini client
client = genai.Client(api_key=api_key)

# List available models
try:
    print("Available Gemini Models:\n")

    for model in client.models.list():
        print(model.name)

except Exception as e:
    print("Error:", e)
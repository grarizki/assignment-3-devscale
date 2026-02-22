from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENROUTER_KEY")
if not api_key:
    raise RuntimeError("OPENROUTER_KEY is not set. Create a .env file with OPENROUTER_KEY=your_key")

client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
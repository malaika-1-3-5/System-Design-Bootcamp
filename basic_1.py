import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
if not OPENAI_BASE_URL:
    raise ValueError("OPENAI_BASE_URL is not set in the environment variables.")
if not OPENAI_MODEL:
    raise ValueError("OPENAI_MODEL is not set in the environment variables.")

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)

completion = client.chat.completions.create(
    model=OPENAI_MODEL,
    messages=[
        {"role": "system","content": "You are a helpful AI assistant for farmers."},
        #{"role": "user", "content": "What should I do if my crops are wilting?"},
        {"role": "user", "content": "What is Tomato late blight and how to prevent it?"},
    ],
    temperature=0.7,
)

print(completion.choices[0].message.content)
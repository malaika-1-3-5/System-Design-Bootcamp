from langchain_openai import ChatOpenAI

import langchain
import os
from dotenv import load_dotenv
from openai import OpenAI, NotFoundError
import json
from langchain import OpenAI

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

client = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    model=OPENAI_MODEL,
    temperature=0.7
)

response = client.invoke(
    [
        {"role": "system","content": "You are a helpful AI assistant for farmers."},
        {"role": "user", "content": "Explain what is Tomato late blight and how to prevent it."},
    ]
)

print(response.content)

prompt_input = """Explain what is Tomato late blight and how to prevent it. Limit it to 100 characters."""
response = client.invoke(prompt_input)

print("---------------------------------")

print(response.content)
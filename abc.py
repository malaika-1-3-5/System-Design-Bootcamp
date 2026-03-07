
import os
from dotenv import load_dotenv
from openai import OpenAI, NotFoundError
import json

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
if not OPENAI_MODEL:
    OPENAI_MODEL = "gpt-4o-mini"

client_kwargs = {"api_key": OPENAI_API_KEY}
if OPENAI_BASE_URL:
    client_kwargs["base_url"] = OPENAI_BASE_URL
client = OpenAI(**client_kwargs)

try:
    response = client.responses.create(
        model=OPENAI_MODEL,
        input="prevent tomato late blight.",
        text={
            "format": {
                "type": "json_schema",
                "name": "short_json",
                "schema": {
                    "type": "object",
                    "properties": {
                        "response": {"type": "string", "maxLength": 100}
                    },
                    "required": ["response"],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        },
    )
except NotFoundError as exc:
    raise ValueError(
        f"Model '{OPENAI_MODEL}' was not found for this endpoint. "
        "Set OPENAI_MODEL to a valid deployed model name."
    ) from exc

data = json.loads(response.output_text)
print(data)  # {"response":"..."} (<=100 chars)
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

models_to_try = [OPENAI_MODEL, "gpt-4o-mini", "gpt-4.1-mini"]
seen = set()
models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

response = None
last_error = None
for model_name in models_to_try:
    try:
        response = client.responses.create(
            model=model_name,
            input="Explain tomato late blight and prevention for farmers.",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "short_json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "response": {
                                "type": "string",
                                "maxLength": 100,
                            }
                        },
                        "required": ["response"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )
        break
    except NotFoundError as exc:
        last_error = exc

if response is not None:
    data = json.loads(response.output_text)
else:
    # Fallback for OpenAI-compatible endpoints that do not implement /responses.
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Return JSON only.",
                },
                {
                    "role": "user",
                    "content": (
                        "Explain tomato late blight and prevention for farmers. "
                        "Respond as JSON with key 'response' and keep value <=100 chars."
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        data = json.loads(completion.choices[0].message.content)
    except Exception as exc:
        raise ValueError(
            f"None of these models were available via /responses: {models_to_try}. "
            "Also failed fallback /chat/completions. "
            "Set OPENAI_MODEL to a deployed model for your endpoint."
        ) from exc

if "response" not in data or not isinstance(data["response"], str):
    raise ValueError("Model output is not valid JSON with a string 'response' field.")

if len(data["response"]) > 100:
    data["response"] = data["response"][:100]

print(json.dumps(data, ensure_ascii=True))
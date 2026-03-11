import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from bs4 import BeautifulSoup

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

load_dotenv(ENV_PATH)
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
    api_key = OPENAI_API_KEY,
    base_url = OPENAI_BASE_URL,
    model=OPENAI_MODEL,
    temperature=0.7
)

# prompt_template = PromptTemplate(
#     input_variables=["topic"],
#     template="Explain what is {topic} and how to prevent it. Limit it to 100 words."
# )

#response = client.invoke(prompt_template.format(topic="Tomato Late Blight"))

#print(response.content)

# chat_prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are an expert agricultural advisor. Be concise and accurate."),
#     ("human", "Explain what is {topic} and how to prevent it. Limit it to {num_words} words.")
# ])
# messages = chat_prompt.invoke({"topic": "Tomato Late Blight", "num_words": 100})
# response = client.invoke(messages)
# print(response.content)

# ##Context
# context = """
# Tomato Late Blight is a fast-spreading disease of tomato caused by the oomycete Phytophthora infestans. It develops quickly in cool (about 10-25 C), humid, and rainy weather, especially when leaves remain wet for long periods.

# Key symptoms:
# - Leaves: pale-green to dark-brown water-soaked spots that expand rapidly; white fuzzy growth may appear on undersides in humid conditions.
# - Stems/petioles: dark brown to black lesions that can girdle tissue and collapse shoots.
# - Fruits: firm, greasy-looking brown patches that enlarge and may later rot.

# How it spreads:
# - Wind-blown spores from infected plants.
# - Splashing rain or irrigation water.
# - Infected volunteer plants, cull piles, or nearby potato fields.

# Prevention and management:
# - Start with healthy seedlings and resistant/tolerant varieties where available.
# - Improve airflow with proper spacing and pruning; use staking to keep foliage off soil.
# - Water at the base (drip irrigation preferred) and avoid overhead irrigation late in the day.
# - Scout fields frequently, especially after cool, wet weather.
# - Remove and destroy infected plant material immediately to reduce inoculum.
# - Use protectant/systemic fungicides according to local agricultural guidance and rotate modes of action to reduce resistance risk.
# - Practice crop rotation and sanitize tools/equipment between plots.

# Impact:
# Without early intervention, Late Blight can destroy a tomato crop within days under favorable weather, causing severe yield and quality losses.
# """

# rag_prompt = ChatPromptTemplate.from_messages([
#     ("system", "You are a helpful agricultural advisor. Answer using ONLY the previous context."),
#     ("human", """Context:
#      {context}
#      Question: {question}
#      Answer:""")
# ])

# messages = rag_prompt.invoke({
#     "context": context,
#     "question": "How to prevent tomato disease?"})
# response = client.invoke(messages)
# print(response.content)

# Web Loader Examples
WIKI_URL = "https://en.wikipedia.org/wiki/Phytophthora_infestans"
loader = WebBaseLoader(WIKI_URL)
docs = loader.load()

#Truncate context if too long
web_context = docs[0].page_content[:6000]  # Truncate to first 6000 characters

rag_prompt_web = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful agricultural advisor. Answer using ONLY the provided context."),
    ("human", """Context (from {source}):
     {context}
     Question: {question}
     Answer:""")
])

message_web = rag_prompt_web.invoke({
    "source": WIKI_URL,
    "context": web_context,
    "question": "How to prevent tomato disease?"
})

response_web = client.invoke(message_web)
print(response_web.content)
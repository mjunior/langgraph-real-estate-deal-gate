import getpass
import os
from langchain_openrouter import ChatOpenRouter

if not os.getenv("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = getpass.getpass("Enter your OpenRouter API key: ")


llm = ChatOpenRouter(
  model="deepseek/deepseek-v4-flash-0731", # 
  temperature=0.1,
  max_tokens=2000
)
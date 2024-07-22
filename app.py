import os

from dotenv import load_dotenv

from AgentMint import AgentMint

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "mintAgent"

agent = AgentMint()
agent.invoke()

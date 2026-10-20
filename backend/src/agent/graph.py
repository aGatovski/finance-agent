from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.tools import TOOLS
from src.agent.prompts import SYSTEM_PROMPT
from src.config import settings

def build_agent_graph(checkpointer):
    model = ChatGoogleGenerativeAI(model=settings.gemini_model, temperature=0.3, google_api_key=settings.gemini_api_key)
    return create_agent(
        model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,  # conversation memory (in-memory for Step 1)
    )

from fastapi import APIRouter, Request
from langchain_core.messages import HumanMessage
from src.api.deps import DEV_USER_ID
from src.schemas.chat import ChatRequest

router = APIRouter()

# @router.post("/chat")
# async def chat(req: ChatRequest, request: Request, user=Depends(get_current_user)):
#     agent = request.app.state.agent
#     #config = {"configurable": {"thread_id": req.thread_id, "user_id": user.id}}
#     config = {"configurable": {"thread_id": req.thread_id, "user_id": DEV_USER_ID}}
#     result = await agent.ainvoke(
#         {"messages": [HumanMessage(req.message)]}, config
#     )
#     return {"reply": result["messages"][-1].content}

@router.post("/chat")
def chat(req: ChatRequest, request: Request):
    agent = request.app.state.agent
    config = {"configurable": {"thread_id": req.thread_id, "user_id": DEV_USER_ID}}
    result =  agent.invoke({"messages": [HumanMessage(req.message)]}, config)
    return {"reply": _extract_text(result["messages"][-1])}


def _extract_text(message) -> str:
    """Flatten an agent message to plain text.

    Gemini 3.x returns `content` as a list of block dicts
    (e.g. [{'type': 'text', 'text': '...'}]) rather than a plain string.
    The frontend expects a string, so join any text blocks."""
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)
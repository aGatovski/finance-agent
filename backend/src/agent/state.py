from langgraph.graph import MessagesState

class AgentState(MessagesState):
    # MessagesState already gives us `messages` with the right reducer.
    user_id: int  # carried via config, surfaced in state for tools
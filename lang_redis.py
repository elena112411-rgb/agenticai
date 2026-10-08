import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.redis import RedisSaver

load_dotenv()

REDIS_URL = "redis://localhost:8001"

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatGroq(model="openai/gpt-oss-120b")

def chat_model(state: GraphState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(GraphState)
builder.add_node("chat", chat_model)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

checkpointer_context = RedisSaver.from_conn_string(REDIS_URL)
checkpointer = checkpointer_context.__enter__()
checkpointer.setup()
graph = builder.compile(checkpointer=checkpointer)

def chat_agent(user_message: str, thread_id: str) -> str:
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = graph.invoke(
        {"messages": [("user", user_message)]},
        config=config
    )

    return result["messages"][-1].content

THREAD_ID = "elena-chat-1"

while True:
    user_input = input("You: ")

    if user_input.lower() in ["exit", "quit"]:
        break

    print("AI:", chat_agent(user_input, THREAD_ID))
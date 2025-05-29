from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_core.messages import ToolMessage
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Load environment variables from .env file
load_dotenv()


# Define a tool that can be used in the agent
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Define the tool that the agent can use to perform addition
@tool
def add(a: int, b: int):
    """This is a function that adds two numbers."""
    # print(f"Adding {a} and {b}")  # Debugging output
    return a + b


# Define tools and bind them to the model
tools = [add]
model = ChatOpenAI(model="gpt-4o").bind_tools(tools)


# Define the state graph for the agent
def model_call(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(
        content="You are a helpful assistant, please answer my query using the tools provided."
    )
    response = model.invoke([system_prompt])
    return {"messages": [response]}


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"


graph = StateGraph(AgentState)
graph.add_node("our_agent", model_call)

tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("our_agent")
graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {"continue": "tools", "end": END},
)

graph.add_edge("tools", "our_agent")

app = graph.compile()


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()


inputs = {"messages": [("user", "Add  2 + 3")]}
print_stream(app.stream(inputs, stream_mode="values"))

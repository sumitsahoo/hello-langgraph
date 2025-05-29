from typing import Annotated, Sequence, TypedDict
from dotenv import load_dotenv
from langchain_core.messages import (
    BaseMessage,
)  # The foundational class for all message types in LangGraph
from langchain_core.messages import (
    ToolMessage,
)  # Passes data back to LLM after it calls a tool such as the content and the tool_call_id
from langchain_core.messages import (
    SystemMessage,
)  # Message for providing instructions to the LLM
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import os
import requests

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def get_weather(city: str):
    """Fetch the current weather for a given city using OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "OpenWeatherMap API key not found."
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("cod") != 200:
            return f"Error: {data.get('message', 'Unable to fetch weather.')}"
        weather = data["weather"][0]["description"].capitalize()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]
        return (
            f"Weather in {city}: {weather}. "
            f"Temperature: {temp}°C (feels like {feels_like}°C). "
            f"Humidity: {humidity}%. Wind speed: {wind_speed} m/s."
        )
    except Exception as e:
        return f"Failed to fetch weather: {e}"


tools = [get_weather]

model = ChatOpenAI(model="gpt-4o").bind_tools(tools)


def model_call(state: AgentState) -> AgentState:
    system_prompt = SystemMessage(
        content="You are my AI assistant, please answer my query to the best of your ability."
    )
    # Convert Sequence[BaseMessage] to list for concatenation
    messages = [system_prompt] + list(state["messages"])
    response = model.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    # Use getattr to safely check for tool_calls
    if not getattr(last_message, "tool_calls", None):
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
    {
        "continue": "tools",
        "end": END,
    },
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


inputs = {
    "messages": [
        (
            "user",
            "How is the weather in Pune, India?",
        )
    ]
}
print_stream(app.stream(inputs, stream_mode="values"))

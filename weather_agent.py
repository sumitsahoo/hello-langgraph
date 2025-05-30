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
from requests import Session, exceptions
from rich.console import Console

load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


console = Console()


@tool
def get_weather(city: str) -> str:
    """Fetch the current weather for a given city using OpenWeatherMap API."""
    console.print(f"\n[magenta]Fetching weather for {city}...[/magenta]")
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "OpenWeatherMap API key not found."
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    session = Session()
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError:
            return "Error: Invalid JSON response from weather API."
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
    except exceptions.Timeout:
        return "Failed to fetch weather: Request timed out."
    except exceptions.HTTPError as e:
        return f"Failed to fetch weather: HTTP error {e.response.status_code}."
    except exceptions.RequestException as e:
        return f"Failed to fetch weather: {e}"
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
graph.add_node("weather_agent", model_call)


tool_node = ToolNode(tools=tools)
graph.add_node("tools", tool_node)

graph.set_entry_point("weather_agent")

graph.add_conditional_edges(
    "weather_agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)

graph.add_edge("tools", "weather_agent")

app = graph.compile()

# Save the graph image to a file in the project root
with open("weather_agent.png", "wb") as f:
    f.write(app.get_graph().draw_mermaid_png())

console.print("\n[magenta]Weather Agent graph created successfully![/magenta]\n")


def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            console.print(f"\n[bold cyan]Assistant:[/bold cyan] {message}\n")
        else:
            message.pretty_print()


# --- Chat loop implementation ---


def chat():

    console.print("\n[red]Type 'exit' to quit.[/red]\n")
    messages = []
    while True:
        user_input = console.input("[bold cyan]You:[/bold cyan] ")
        if user_input.strip().lower() == "exit":
            console.print("\n[red]Exiting chat.[/red]\n")
            break
        messages.append(("user", user_input))
        stream = app.stream({"messages": messages}, stream_mode="values")
        last_message = None
        for s in stream:
            message = s["messages"][-1]
            last_message = message
        # Print and store only the last assistant message
        if last_message is not None:
            if hasattr(last_message, "content"):
                console.print(
                    f"\n[bold green]Assistant:[/bold green] {getattr(last_message, 'content', str(last_message)).strip()}\n"
                )
                messages.append(
                    ("assistant", getattr(last_message, "content", str(last_message)))
                )
            elif isinstance(last_message, tuple):
                console.print(f"\n[bold green]Assistant:[/bold green] {last_message}\n")
            else:
                console.print("\n[bold green]Assistant:[/bold green]")
                last_message.pretty_print()
                console.print()


if __name__ == "__main__":
    chat()

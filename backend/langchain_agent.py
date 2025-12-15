import os
import requests
from dotenv import load_dotenv

from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_openai import ChatOpenAI


load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 


def get_weather(city: str) -> str:
    try:
        geo = requests.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": city, "limit": 1, "appid": OPENWEATHER_API_KEY},
            timeout=8
        ).json()

        if not geo:
            return "Sorry, I could not find that city."

        lat, lon = geo[0]["lat"], geo[0]["lon"]

        weather = requests.get(
            "https://api.openweathermap.org/data/3.0/onecall",
            params={
                "lat": lat,
                "lon": lon,
                "units": "metric",
                "exclude": "minutely,hourly,alerts",
                "appid": OPENWEATHER_API_KEY
            },
            timeout=8
        ).json()

        temp = weather["current"]["temp"]
        desc = weather["current"]["weather"][0]["description"]

        return f"It's {temp}°C in {city.title()} with {desc}."

    except Exception:
        return "Unable to fetch weather right now."


weather_tool = Tool(
    name="WeatherTool",
    func=lambda city: get_weather(city.strip()),
    description=(
        "Use this tool to get the current weather of a city. "
        "Input must be a city name like Pune, Mumbai, Delhi."
    )
)

llm = None
agent = None

if OPENAI_API_KEY:
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3
    )

    agent = initialize_agent(
        tools=[weather_tool],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False
    )


def agent_response(message: str) -> str:
    """
    1. Try LangChain agent (LLM + Tool)
    2. If quota/network fails → fallback to direct weather
    """
    # Try agent if available
    if agent:
        try:
            result = agent.invoke(message)
            if isinstance(result, dict):
                return result.get("output", "")
            return result
        except Exception as e:
            # Graceful fallback
            print("LLM failed, falling back:", e)

    # Fallback: extract last word as city
    city = message.strip().split()[-1]
    return get_weather(city)

import os
import requests

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

OPENROUTER_CHAT_URL = "https://api.openrouter.ai/v1/chat/completions"

# Words that should never be treated as cities
STOP_WORDS = {
    "hi", "hello", "hey", "thanks", "thank", "ok", "okay",
    "yes", "no", "please", "sorry", "help", "who", "what",
    "why", "how", "when"
}


def get_lat_lon(city: str):
    """
    Convert city name to latitude and longitude
    using OpenWeather Geocoding API
    """
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        "q": city,
        "limit": 1,
        "appid": OPENWEATHER_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        if not data or "lat" not in data[0] or "lon" not in data[0]:
            return None, None

        return data[0]["lat"], data[0]["lon"]

    except Exception:
        return None, None


def get_weather(city: str):
    """
    Fetch current weather using One Call API 3.0
    """
    lat, lon = get_lat_lon(city)

    if lat is None or lon is None:
        return None

    url = "https://api.openweathermap.org/data/3.0/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly,alerts",
        "units": "metric",
        "appid": OPENWEATHER_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        temp = data["current"]["temp"]
        desc = data["current"]["weather"][0]["description"]

        return f"It's {temp}°C in {city.title()} with {desc}."

    except Exception:
        return None


def call_openrouter(prompt: str):
    """
    Call LLM via OpenRouter API
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200
    }

    try:
        response = requests.post(
            OPENROUTER_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception:
        return None


def agent_response(message: str):
    """
    Agent logic:
    - Explicit weather queries
    - City-only queries with name & greeting protection
    - General chat fallback
    """

    original_message = message.strip()
    msg = original_message.lower().replace("?", "")
    tokens = msg.split()

    weather_keywords = {"weather", "temperature", "degree", "climate"}

    # Case 1: Explicit weather query
    if any(word in weather_keywords for word in tokens):
        if "in" in tokens:
            city = tokens[tokens.index("in") + 1]
        elif "of" in tokens:
            city = tokens[tokens.index("of") + 1]
        else:
            city = tokens[-1]

        weather = get_weather(city)
        if weather:
            refined = call_openrouter(f"Rewrite this politely: {weather}")
            return refined or weather

        return "Sorry, I could not fetch the weather right now."

    # Case 2: City-only input (heuristic validation)
    if len(tokens) <= 2 and all(word.isalpha() for word in tokens):

        # Block greetings & common words
        if any(word in STOP_WORDS for word in tokens):
            return call_openrouter(original_message) or "Hello! How can I help you?"

        # Block proper names (capitalized single words like 'Satyam')
        if original_message[0].isupper() and len(tokens) == 1:
            return call_openrouter(original_message) or "How can I help you?"

        city = " ".join(tokens)
        lat, lon = get_lat_lon(city)

        if lat and lon:
            weather = get_weather(city)
            if weather:
                refined = call_openrouter(f"Rewrite this politely: {weather}")
                return refined or weather

    # Case 3: General conversation
    return call_openrouter(original_message) or "Sorry, I could not generate a response."

import React, { useState } from "react";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(false);
  const [weatherType, setWeatherType] = useState("default");

  function detectWeatherType(text) {
    const lower = text.toLowerCase();

    if (lower.includes("clear")) return "clear";
    if (lower.includes("cloud")) return "clouds";
    if (lower.includes("rain") || lower.includes("drizzle")) return "rain";
    if (lower.includes("snow")) return "snow";

    return "default";
  }

  async function sendMessage() {
    if (!input.trim()) return;

    setLoading(true);
    setReply("");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      const data = await res.json();
      setReply(data.reply);

      const type = detectWeatherType(data.reply);
      setWeatherType(type);

    } catch {
      setReply("Unable to connect to backend.");
      setWeatherType("default");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`app-container ${weatherType}`}>
      <div className="card">
        <h2 className="title"> SkySense AI</h2>
        <p className="subtitle">
          Ask weather by city
        </p>

        <div className="input-group">
          <input
            value={input}
            placeholder="e.g. Pune, Mumbai, weather of Delhi"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          />
          <button onClick={sendMessage} disabled={loading}>
            {loading ? "Loading..." : "Send"}
          </button>
        </div>

        <div className="response-box">
          {reply && <p>{reply}</p>}
          {loading && <p className="loading-text">Loading...</p>}
        </div>
      </div>

      <footer className="footer">
        Built using React, FastAPI & OpenWeather API
      </footer>
    </div>
  );
}

export default App;

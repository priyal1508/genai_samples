# Plan: AutoGen 0.4+ Multi-Agent Travel Planner

A lightweight, config-driven travel planner using AutoGen 0.4+ (`ag2`) with a multi-agent team: a **Planner** orchestrates specialist agents for flights, hotels, weather, and itinerary generation — all backed by Azure OpenAI and mock APIs.

**TL;DR**: 5 agents coordinated via `SelectorGroupChat`. Each agent has its system prompt in a separate file, all secrets live in `.env`, mock tools simulate external APIs, and the code stays thin by leaning on AutoGen's built-in orchestration. Total ~10 files, <300 lines of application code.

---

## Project Structure

Hiring_GenAI/
├── .env # Azure OpenAI credentials
├── .env.example # Template for others
├── requirements.txt
├── README.md
├── config/
│ └── settings.py # Loads .env, exposes config dataclass
├── prompts/
│ ├── planner.md
│ ├── flight_agent.md
│ ├── hotel_agent.md
│ ├── weather_agent.md
│ └── itinerary_agent.md
├── tools/
│ ├── init.py
│ ├── flight_search.py # Mock flights API
│ ├── hotel_search.py # Mock hotels API
│ └── weather.py # Mock weather API
├── agents/
│ ├── init.py
│ └── team.py # Agent + team wiring
└── main.py # Entry point (async)


---

## Steps

### 1. Scaffold project structure
Create all directories and files as shown above.

### 2. Create `.env` and `.env.example`
Store Azure OpenAI config:
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT` (e.g., `gpt-4o`)
- `AZURE_OPENAI_API_VERSION` (e.g., `2024-08-01-preview`)

`.env.example` has the same keys with placeholder values.

### 3. Create `config/settings.py`
- Use `python-dotenv` to load `.env`
- Expose a `Settings` dataclass with all config values
- A helper `load_prompt(name: str) -> str` that reads from `prompts/{name}.md`
- Zero hardcoded secrets or model names in application code

### 4. Create mock tool functions in `tools/`

**`tools/flight_search.py`** — `search_flights(origin: str, destination: str, date: str) -> list[dict]`
- Returns 3–5 mock flights with airline, price, departure/arrival times, duration
- Randomized but deterministic (seeded by route+date hash) so results feel realistic

**`tools/hotel_search.py`** — `search_hotels(city: str, check_in: str, check_out: str) -> list[dict]`
- Returns 3–5 mock hotels with name, price/night, rating, amenities

**`tools/weather.py`** — `get_weather(city: str, date: str) -> dict`
- Returns mock weather: temperature, condition (sunny/rainy/cloudy), humidity, wind
- Varies by city name hash + date so different queries give different data

All tools are pure functions with type hints — AutoGen 0.4+ wraps them via `FunctionTool`.

### 5. Write agent system prompts in `prompts/`

Each `.md` file contains a focused system prompt:
- **`planner.md`**: Orchestrator — understands user's travel request, delegates to specialists, synthesizes final answer. Instructs it to gather all info before handing off to itinerary agent.
- **`flight_agent.md`**: Flight specialist — uses `search_flights` tool, presents options clearly, recommends best value.
- **`hotel_agent.md`**: Hotel specialist — uses `search_hotels` tool, recommends based on budget/preferences.
- **`weather_agent.md`**: Weather specialist — uses `get_weather` tool, provides forecast and packing suggestions.
- **`itinerary_agent.md`**: Itinerary compiler — takes all gathered info and produces a structured day-by-day travel plan. Says `TERMINATE` when the itinerary is complete.

### 6. Wire agents in `agents/team.py`

- Create `AzureOpenAIChatCompletionClient` using config from `settings.py`
- Define 5 `AssistantAgent` instances:
  - `planner_agent` — no tools, just orchestration prompt
  - `flight_agent` — tools: `[FunctionTool(search_flights)]`
  - `hotel_agent` — tools: `[FunctionTool(search_hotels)]`
  - `weather_agent` — tools: `[FunctionTool(get_weather)]`
  - `itinerary_agent` — no tools, generates the final plan
- Create a `SelectorGroupChat` with all 5 agents:
  - The model-based selector picks which agent speaks next based on conversation context
  - `TextMentionTermination("TERMINATE")` as the termination condition
  - `MaxMessageTermination(25)` as a safety cap
- Expose a `build_team() -> SelectorGroupChat` factory function

### 7. Create `main.py` entry point

- Async main function
- Accepts user travel query via `Console` (AutoGen's built-in console streaming interface)
- Calls `build_team()` and runs `Console(team.run_stream(task=user_query))`
- Clean, <20 lines of application logic

### 8. Create `requirements.txt`


### 9. Write `README.md`

- Project overview, architecture diagram (text-based)
- Setup instructions: venv, pip install, `.env` configuration
- Usage: how to run, example queries
- Agent team description

---

## Verification

1. Create and activate venv: `python -m venv venv && venv\Scripts\activate`
2. Install: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, fill in Azure OpenAI credentials
4. Run: `python main.py`
5. Test with query: *"Plan a 5-day trip from New York to Tokyo in March 2026. Budget: $3000"*
6. Verify: all 4 specialist agents are invoked, itinerary is generated, conversation terminates cleanly

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Group chat type | `SelectorGroupChat` over `RoundRobinGroupChat` | Selector lets the model dynamically choose which agent speaks next based on what info is still needed, avoiding rigid turn ordering |
| Prompt file format | `.md` over `.txt` | Enables richer formatting in prompts and better readability |
| Mock data strategy | Seeded randomization over static JSON | Gives varied but reproducible results per query without external dependencies |
| Tool wrapping | `FunctionTool` with type hints | AutoGen 0.4+ auto-infers schemas from type hints — keeps code minimal |
| User interface | `Console` streaming | Gives real-time token streaming out of the box with zero extra code |



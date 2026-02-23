# Travel Planner Assistant

A multi-agent travel planner built with **AutoGen 0.4+** and **Azure OpenAI**. Five specialized agents collaborate to search flights, find hotels, check weather, and compile a day-by-day itinerary.

## Architecture

```
User Query
    │
    ▼
┌─────────┐      ┌──────────────┐
│ Planner │─────▶│ Flight Agent │──▶ search_flights()
│ (coord) │      └──────────────┘
│         │      ┌──────────────┐
│         │─────▶│ Hotel Agent  │──▶ search_hotels()
│         │      └──────────────┘
│         │      ┌───────────────┐
│         │─────▶│ Weather Agent │──▶ get_weather()
│         │      └───────────────┘
│         │      ┌─────────────────┐
│         │─────▶│ Itinerary Agent │──▶ Final Plan
└─────────┘      └─────────────────┘
```

**Orchestration**: `SelectorGroupChat` — the LLM dynamically picks which agent speaks next based on conversation context.

## Project Structure

```
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── main.py                   # Entry point
├── config/
│   └── settings.py           # Loads .env, typed config, prompt loader
├── prompts/                  # Agent system prompts (one .md per agent)
│   ├── planner.md
│   ├── flight_agent.md
│   ├── hotel_agent.md
│   ├── weather_agent.md
│   └── itinerary_agent.md
├── tools/                    # Mock API functions
│   ├── flight_search.py
│   ├── hotel_search.py
│   └── weather.py
└── agents/
    └── team.py               # Agent definitions + team wiring
```

## Setup

### 1. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your Azure OpenAI credentials:

```
AZURE_OPENAI_API_KEY=your-actual-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### 4. Run

```bash
python main.py
```

## Example Query

```
You: Plan a 5-day trip from New York to Tokyo in March 2026. Budget: $3000
```

The agents will:
1. **Planner** parses the request and delegates
2. **Flight Agent** searches outbound + return flights
3. **Hotel Agent** finds hotels in Tokyo
4. **Weather Agent** checks Tokyo weather for March
5. **Itinerary Agent** compiles everything into a day-by-day plan

## Design Principles

| Principle | Implementation |
|-----------|---------------|
| No hardcoded secrets | All config via `.env` + `Settings` dataclass |
| Separated prompts | Each agent prompt in its own `.md` file |
| Minimal code | AutoGen handles orchestration; tools auto-infer schemas |
| Deterministic mocks | Seeded hash-based randomization for reproducible results |
| Config-driven | Change model, deployment, or API version without touching code |

"""Build the multi-agent travel planner team using AutoGen 0.4+ SelectorGroupChat."""

from typing import Sequence

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from config.settings import Settings, load_prompt
from config.memory import load_memory, format_memory_context
from tools.flight_search import search_flights
from tools.hotel_search import search_hotels
from tools.weather import get_weather

# Agent name constants (referenced in selector prompt)
PLANNER = "planner"
FLIGHT_AGENT = "flight_agent"
HOTEL_AGENT = "hotel_agent"
WEATHER_AGENT = "weather_agent"
ITINERARY_AGENT = "itinerary_agent"
USER = "user"


def _build_model_client(settings: Settings) -> AzureOpenAIChatCompletionClient:
    """Create the shared Azure OpenAI model client using Entra ID auth."""
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAIChatCompletionClient(
        azure_deployment=settings.azure_openai_deployment,
        model=settings.azure_openai_deployment,
        azure_ad_token_provider=token_provider,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "unknown",
            "structured_output": True,
        },
    )


def _build_tools() -> dict[str, list[FunctionTool]]:
    """Wrap mock API functions as AutoGen FunctionTools."""
    return {
        FLIGHT_AGENT: [FunctionTool(search_flights, description="Search for available flights between two cities on a given date.")],
        HOTEL_AGENT: [FunctionTool(search_hotels, description="Search for available hotels in a city for given dates.")],
        WEATHER_AGENT: [FunctionTool(get_weather, description="Get weather forecast for a city on a given date.")],
    }


def build_team() -> SelectorGroupChat:
    """Assemble and return the travel planner agent team.

    Returns:
        A SelectorGroupChat ready to run with ``team.run_stream(task=...)``.
    """
    settings = Settings.from_env()
    model_client = _build_model_client(settings)
    tools = _build_tools()

    # --- Agents ---

    # Build planner system message with memory context injected
    planner_base_prompt = load_prompt("planner")
    memory_data = load_memory()
    memory_context = format_memory_context(memory_data)
    planner_system_message = (
        f"{planner_base_prompt}\n\n{memory_context}" if memory_context else planner_base_prompt
    )

    planner = AssistantAgent(
        name=PLANNER,
        model_client=model_client,
        system_message=planner_system_message,
        description="The lead travel planner that coordinates the team. Delegates to specialists, asks the user clarifying questions when needed, and synthesizes results.",
    )

    # Human-in-the-loop: prompts the real user for input in the terminal
    user_proxy = UserProxyAgent(
        name=USER,
        description="The human traveler. Route here when the planner asks a clarifying question or needs user input.",
    )

    flight_agent = AssistantAgent(
        name=FLIGHT_AGENT,
        model_client=model_client,
        tools=tools[FLIGHT_AGENT],
        system_message=load_prompt("flight_agent"),
        description="Searches for flights between cities using the search_flights tool.",
    )

    hotel_agent = AssistantAgent(
        name=HOTEL_AGENT,
        model_client=model_client,
        tools=tools[HOTEL_AGENT],
        system_message=load_prompt("hotel_agent"),
        description="Searches for hotels in a city using the search_hotels tool.",
    )

    weather_agent = AssistantAgent(
        name=WEATHER_AGENT,
        model_client=model_client,
        tools=tools[WEATHER_AGENT],
        system_message=load_prompt("weather_agent"),
        description="Provides weather forecasts using the get_weather tool.",
    )

    itinerary_agent = AssistantAgent(
        name=ITINERARY_AGENT,
        model_client=model_client,
        system_message=load_prompt("itinerary_agent"),
        description="Compiles all gathered information into a polished day-by-day travel itinerary. Says TERMINATE when done.",
    )

    # --- Termination conditions ---
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(max_messages=30)

    # --- Selector prompt (guides which agent speaks next) ---
    selector_prompt = """You are the orchestrator selecting which agent should speak next.
The available agents are:
- planner: Coordinates the team. Speaks FIRST to parse the request. Can ask clarifying questions.
- user: The human traveler. Select ONLY when the planner has asked a question that needs human input.
- flight_agent: Searches for flights. Call when flight information is needed.
- hotel_agent: Searches for hotels. Call when hotel information is needed.
- weather_agent: Provides weather forecasts. Call when weather data is needed.
- itinerary_agent: Compiles the final itinerary. Call ONLY ONCE after ALL specialist data is collected.

Flow:
1. planner (parse request — may ask the user a question OR delegate directly)
2. IF planner asked a question → user (human responds)
3. IF user responded → planner (process answer, then delegate to specialists)
4. flight_agent → hotel_agent → weather_agent (in any order, one at a time)
5. planner (summarize all findings)
6. itinerary_agent (compile final itinerary — says TERMINATE when done)

Key rules:
- Select "user" ONLY RIGHT AFTER the planner asks a question. Never select "user" at any other time.
- After "user" responds, ALWAYS go back to "planner".
- NEVER select the same agent twice in a row (except planner after user).
- NEVER go back to a specialist that has already reported.
"""

    def _selector_func(messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> str | None:
        """Deterministic selector that gates human-in-the-loop properly.

        Only routes to 'user' when the planner asks a genuine question
        (has '?' but does NOT delegate to specialists). Otherwise follows:
        planner → specialists → planner (summary) → itinerary_agent.
        """
        if not messages:
            return PLANNER

        last = messages[-1]
        last_source = getattr(last, "source", "")
        last_content = (getattr(last, "content", "") or "").strip()

        # After the user responds, always go back to planner
        if last_source == USER:
            return PLANNER

        # If planner just spoke, decide: question → user, delegation → first specialist
        if last_source == PLANNER:
            content_lower = last_content.lower()
            delegation_map = [
                ("flight agent", FLIGHT_AGENT),
                ("hotel agent", HOTEL_AGENT),
                ("weather agent", WEATHER_AGENT),
                ("itinerary agent", ITINERARY_AGENT),
            ]
            first_specialist = None
            for keyword, agent_name in delegation_map:
                if keyword in content_lower:
                    first_specialist = agent_name
                    break

            if first_specialist:
                # Planner delegated — go to the first specialist mentioned
                return first_specialist

            # Not a delegation — if there's a '?', it's a question for the user
            if "?" in last_content:
                return USER

            # Planner said something else (e.g., summary) — fall through
            return None

        # After a specialist (or tool call) responds, find the next specialist
        # that hasn't spoken yet, then planner summary, then itinerary
        spoken_agents = {getattr(m, "source", "") for m in messages}
        specialist_order = [FLIGHT_AGENT, HOTEL_AGENT, WEATHER_AGENT]

        for agent in specialist_order:
            if agent not in spoken_agents:
                return agent

        # All specialists done — if planner hasn't summarized (spoke only once), go to planner
        planner_turns = sum(1 for m in messages if getattr(m, "source", "") == PLANNER)
        if planner_turns < 2:
            return PLANNER

        # Planner has summarized — go to itinerary agent
        return ITINERARY_AGENT

    team = SelectorGroupChat(
        participants=[planner, user_proxy, flight_agent, hotel_agent, weather_agent, itinerary_agent],
        model_client=model_client,
        termination_condition=termination,
        selector_prompt=selector_prompt,
        selector_func=_selector_func,
    )

    return team

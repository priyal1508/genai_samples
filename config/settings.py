"""Application settings — loads .env and exposes typed config + prompt loader."""

from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

_PROMPTS_DIR = _PROJECT_ROOT / "prompts"


@dataclass(frozen=True)
class Settings:
    """Immutable application settings sourced from environment variables.

    Supports two providers:
        - ``groq``  — free Groq Cloud API (Llama 3.3, Mixtral, etc.)
        - ``azure`` — Azure OpenAI with Entra ID or API key auth
    """

    provider: str               # "groq" or "azure"
    model_name: str             # e.g. "llama-3.3-70b-versatile" or "gpt-4.1"
    api_key: str = ""           # Groq API key or Azure API key
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from the current environment."""
        provider = os.getenv("LLM_PROVIDER", "groq").lower()

        if provider == "groq":
            groq_key = os.getenv("GROQ_API_KEY", "")
            if not groq_key:
                raise EnvironmentError("Missing required env var: GROQ_API_KEY")
            model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
            return cls(provider="groq", model_name=model, api_key=groq_key)

        # Azure provider
        def _require(key: str, *alternates: str) -> str:
            value = os.getenv(key)
            if value:
                return value
            for alt in alternates:
                value = os.getenv(alt)
                if value:
                    return value
            raise EnvironmentError(f"Missing required env var: {key}")

        return cls(
            provider="azure",
            model_name=_require("AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_MODEL_NAME"),
            api_key=os.getenv("AZURE_OPENAI_KEY", ""),
            azure_openai_endpoint=_require("AZURE_OPENAI_ENDPOINT"),
            azure_openai_api_version=_require("AZURE_OPENAI_API_VERSION"),
        )


def load_prompt(name: str) -> str:
    """Read a prompt file from the prompts/ directory.

    Args:
        name: filename without extension, e.g. ``"planner"`` → ``prompts/planner.md``
    """
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()

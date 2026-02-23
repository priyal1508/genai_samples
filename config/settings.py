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
    """Immutable application settings sourced from environment variables."""

    azure_openai_endpoint: str
    azure_openai_deployment: str
    azure_openai_api_version: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from the current environment."""

        def _require(key: str) -> str:
            value = os.getenv(key)
            if not value:
                raise EnvironmentError(f"Missing required env var: {key}")
            return value

        return cls(
            azure_openai_endpoint=_require("AZURE_OPENAI_ENDPOINT"),
            azure_openai_deployment=_require("AZURE_OPENAI_DEPLOYMENT"),
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

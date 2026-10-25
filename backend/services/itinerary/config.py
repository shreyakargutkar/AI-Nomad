"""Single source of truth for itinerary service environment variables."""
import os

_here = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_here, "..", "..", ".."))
_ROOT_ENV = os.path.join(_PROJECT_ROOT, ".env")


def _bootstrap_env() -> None:
    """
    Load Groq/Tavily keys from project .env file only.
    override=True so file values beat a stale shell export.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    if os.path.isfile(_ROOT_ENV):
        load_dotenv(_ROOT_ENV, override=True)


_bootstrap_env()

GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()
print(GROQ_API_KEY[:15])
TAVILY_API_KEY = (os.getenv("TAVILY_API_KEY") or "").strip()
DEFAULT_PASSPORT_COUNTRY = os.getenv("DEFAULT_PASSPORT_COUNTRY", "India")

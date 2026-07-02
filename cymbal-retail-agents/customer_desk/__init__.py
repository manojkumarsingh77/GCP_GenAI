from dotenv import load_dotenv

# Load .env from the project root so RAG_CORPUS, MODEL, etc. are available
# before the agent modules import them.
load_dotenv()

from . import agent  # noqa: E402,F401  (exposes root_agent for `adk web`)

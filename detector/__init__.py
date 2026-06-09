"""crime-coins detector package."""
import os as _os


def _load_dotenv() -> None:
    """Load KEY=VALUE lines from a project-root .env into os.environ (no deps).
    Existing env vars win, so shell overrides still work. Loaded before any module
    that reads env at import time (e.g. enrich.CG_KEY)."""
    path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".env")
    if not _os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.lower().startswith("export "):
                    line = line[7:]
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in _os.environ:
                    _os.environ[k] = v
    except Exception:
        pass


_load_dotenv()

from .crime_score import Signals, Assessment, score  # noqa: F401,E402

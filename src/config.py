import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Copy .env.example to .env and fill in your credentials."
        )
    return val


class Config:
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    SPOTIFY_REDIRECT_URI: str = ""
    APPLE_TEAM_ID: str = ""
    APPLE_KEY_ID: str = ""
    # Inline key content (used in cloud deployments via fly secret)
    APPLE_PRIVATE_KEY: str = ""
    PORT: int = 8080

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        cfg.SPOTIFY_CLIENT_ID = _require("SPOTIFY_CLIENT_ID")
        cfg.SPOTIFY_CLIENT_SECRET = _require("SPOTIFY_CLIENT_SECRET")
        cfg.SPOTIFY_REDIRECT_URI = os.getenv(
            "SPOTIFY_REDIRECT_URI", "http://localhost:8080/spotify/callback"
        )
        cfg.APPLE_TEAM_ID = _require("APPLE_TEAM_ID")
        cfg.APPLE_KEY_ID = _require("APPLE_KEY_ID")
        cfg.APPLE_PRIVATE_KEY = cls._load_apple_key()
        cfg.PORT = int(os.getenv("PORT", "8080"))
        return cfg

    @staticmethod
    def _load_apple_key() -> str:
        # Prefer inline key content (set via `fly secret set APPLE_PRIVATE_KEY="$(cat AuthKey.p8)"`)
        inline = os.getenv("APPLE_PRIVATE_KEY", "")
        if inline:
            # Fly.io secrets replace newlines with literal \n — restore them
            return inline.replace("\\n", "\n")

        # Fall back to file path for local development
        path = os.getenv("APPLE_PRIVATE_KEY_PATH", "")
        if not path:
            raise EnvironmentError(
                "Missing Apple Music key: set APPLE_PRIVATE_KEY (inline) "
                "or APPLE_PRIVATE_KEY_PATH (file path)."
            )
        with open(path, "r") as f:
            return f.read()

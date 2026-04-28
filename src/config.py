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
    APPLE_PRIVATE_KEY_PATH: str = ""
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
        cfg.APPLE_PRIVATE_KEY_PATH = _require("APPLE_PRIVATE_KEY_PATH")
        cfg.PORT = int(os.getenv("PORT", "8080"))
        return cfg

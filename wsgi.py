"""Production WSGI entrypoint for gunicorn."""
import os
from src.config import Config
from src.spotify import SpotifyClient
from src.apple_music import AppleMusicClient
from src import server

cfg = Config.load()

spotify = SpotifyClient(
    client_id=cfg.SPOTIFY_CLIENT_ID,
    client_secret=cfg.SPOTIFY_CLIENT_SECRET,
    redirect_uri=cfg.SPOTIFY_REDIRECT_URI,
)
apple = AppleMusicClient(
    team_id=cfg.APPLE_TEAM_ID,
    key_id=cfg.APPLE_KEY_ID,
    private_key=cfg.APPLE_PRIVATE_KEY,
)

server.init(cfg, spotify, apple)
app = server.app

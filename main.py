#!/usr/bin/env python3
"""
Spotify → Apple Music Playlist Importer
Run: python main.py
"""
import os
import sys
import webbrowser

from src.config import Config
from src.spotify import SpotifyClient
from src.apple_music import AppleMusicClient
from src import server


def main() -> None:
    try:
        cfg = Config.load()
    except EnvironmentError as e:
        print(f"\n[Error] {e}\n", file=sys.stderr)
        sys.exit(1)

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

    url = f"http://localhost:{cfg.PORT}"
    print(f"\n  Spotify → Apple Music Importer")
    print(f"  --------------------------------")
    print(f"  Open your browser at: {url}")
    print(f"  Press Ctrl+C to stop\n")

    # Try to open the browser automatically
    try:
        webbrowser.open(url)
    except Exception:
        pass

    server.app.run(host="0.0.0.0", port=cfg.PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

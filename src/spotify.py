import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    title: str
    artist: str
    album: str
    isrc: Optional[str]
    spotify_id: str

    def __str__(self) -> str:
        return f"{self.artist} - {self.title}"


@dataclass
class Playlist:
    id: str
    name: str
    description: str
    owner: str
    tracks: list[Track]

    def __str__(self) -> str:
        return f"{self.name} ({len(self.tracks)} tracks)"


class SpotifyClient:
    SCOPES = "playlist-read-private playlist-read-collaborative"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self._auth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.SCOPES,
            cache_path=".spotify_token_cache",
            open_browser=False,
        )
        self._sp: Optional[spotipy.Spotify] = None

    def get_auth_url(self) -> str:
        return self._auth.get_authorize_url()

    def handle_callback(self, code: str) -> None:
        token_info = self._auth.get_access_token(code, as_dict=True)
        self._sp = spotipy.Spotify(auth=token_info["access_token"])

    def is_authenticated(self) -> bool:
        return self._sp is not None

    def get_playlists(self) -> list[dict]:
        assert self._sp, "Not authenticated"
        results = []
        response = self._sp.current_user_playlists(limit=50)
        while response:
            results.extend(response["items"])
            response = self._sp.next(response) if response["next"] else None
        return [
            {"id": p["id"], "name": p["name"], "owner": p["owner"]["display_name"]}
            for p in results
            if p
        ]

    def get_playlist(self, playlist_id: str) -> Playlist:
        assert self._sp, "Not authenticated"
        meta = self._sp.playlist(playlist_id, fields="id,name,description,owner")
        tracks = self._fetch_all_tracks(playlist_id)
        return Playlist(
            id=meta["id"],
            name=meta["name"],
            description=meta.get("description", ""),
            owner=meta["owner"]["display_name"],
            tracks=tracks,
        )

    def _fetch_all_tracks(self, playlist_id: str) -> list[Track]:
        assert self._sp, "Not authenticated"
        tracks: list[Track] = []
        response = self._sp.playlist_tracks(
            playlist_id,
            fields="items(track(id,name,artists,album(name),external_ids)),next",
            limit=100,
        )
        while response:
            for item in response["items"]:
                track_data = item.get("track")
                if not track_data or track_data.get("id") is None:
                    continue  # skip local/unavailable tracks
                artists = ", ".join(a["name"] for a in track_data["artists"])
                tracks.append(
                    Track(
                        title=track_data["name"],
                        artist=artists,
                        album=track_data["album"]["name"],
                        isrc=track_data.get("external_ids", {}).get("isrc"),
                        spotify_id=track_data["id"],
                    )
                )
            response = self._sp.next(response) if response["next"] else None
        return tracks

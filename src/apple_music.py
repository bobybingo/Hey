import time
import jwt
import requests
from dataclasses import dataclass
from typing import Optional

APPLE_MUSIC_API = "https://api.music.apple.com/v1"


@dataclass
class AppleTrack:
    id: str
    title: str
    artist: str
    album: str


class AppleMusicClient:
    def __init__(self, team_id: str, key_id: str, private_key_path: str):
        self._team_id = team_id
        self._key_id = key_id
        self._private_key = self._load_key(private_key_path)
        self._developer_token: Optional[str] = None
        self._user_token: Optional[str] = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _load_key(self, path: str) -> str:
        with open(path, "r") as f:
            return f.read()

    def get_developer_token(self) -> str:
        if self._developer_token:
            return self._developer_token
        now = int(time.time())
        payload = {
            "iss": self._team_id,
            "iat": now,
            "exp": now + 15_777_000,  # ~6 months, Apple max
        }
        self._developer_token = jwt.encode(
            payload,
            self._private_key,
            algorithm="ES256",
            headers={"kid": self._key_id},
        )
        return self._developer_token

    def set_user_token(self, token: str) -> None:
        self._user_token = token

    def is_authenticated(self) -> bool:
        return bool(self._user_token)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        headers = {"Authorization": f"Bearer {self.get_developer_token()}"}
        if self._user_token:
            headers["Music-User-Token"] = self._user_token
        return headers

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        resp = requests.get(
            f"{APPLE_MUSIC_API}{path}",
            headers=self._headers(),
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: dict) -> dict:
        resp = requests.post(
            f"{APPLE_MUSIC_API}{path}",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=body,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_track(self, title: str, artist: str, isrc: Optional[str] = None) -> Optional[AppleTrack]:
        # Try ISRC first — most precise match
        if isrc:
            result = self._search_by_isrc(isrc)
            if result:
                return result

        # Fall back to text search
        query = f"{title} {artist}"
        try:
            data = self._get(
                "/catalog/us/search",
                params={"term": query, "types": "songs", "limit": "5"},
            )
        except requests.HTTPError:
            return None

        songs = data.get("results", {}).get("songs", {}).get("data", [])
        if not songs:
            return None

        # Pick the best match: prefer exact title+artist match
        for song in songs:
            attrs = song.get("attributes", {})
            if (
                attrs.get("name", "").lower() == title.lower()
                and artist.lower() in attrs.get("artistName", "").lower()
            ):
                return self._song_to_track(song)

        # Return first result if no exact match
        return self._song_to_track(songs[0])

    def _search_by_isrc(self, isrc: str) -> Optional[AppleTrack]:
        try:
            data = self._get(
                "/catalog/us/songs",
                params={"filter[isrc]": isrc},
            )
        except requests.HTTPError:
            return None

        songs = data.get("data", [])
        if not songs:
            return None
        return self._song_to_track(songs[0])

    def _song_to_track(self, song: dict) -> AppleTrack:
        attrs = song.get("attributes", {})
        return AppleTrack(
            id=song["id"],
            title=attrs.get("name", ""),
            artist=attrs.get("artistName", ""),
            album=attrs.get("albumName", ""),
        )

    # ------------------------------------------------------------------
    # Library
    # ------------------------------------------------------------------

    def create_library_playlist(self, name: str, description: str, track_ids: list[str]) -> str:
        """Create a playlist in the user's Apple Music library. Returns playlist id."""
        body: dict = {
            "attributes": {"name": name, "description": description},
        }
        if track_ids:
            body["relationships"] = {
                "tracks": {
                    "data": [{"id": tid, "type": "songs"} for tid in track_ids]
                }
            }
        data = self._post("/me/library/playlists", body)
        return data["data"][0]["id"]

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: list[str]) -> None:
        """Append tracks to an existing library playlist."""
        body = {"data": [{"id": tid, "type": "songs"} for tid in track_ids]}
        requests.post(
            f"{APPLE_MUSIC_API}/me/library/playlists/{playlist_id}/tracks",
            headers={**self._headers(), "Content-Type": "application/json"},
            json=body,
            timeout=15,
        ).raise_for_status()

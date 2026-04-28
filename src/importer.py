from dataclasses import dataclass, field
from typing import Callable, Optional

from .spotify import Playlist, Track
from .apple_music import AppleMusicClient


@dataclass
class ImportResult:
    playlist_name: str
    total: int
    matched: int
    not_found: list[Track] = field(default_factory=list)
    apple_playlist_id: Optional[str] = None

    @property
    def match_rate(self) -> float:
        return (self.matched / self.total * 100) if self.total else 0.0

    def summary(self) -> str:
        return (
            f"'{self.playlist_name}': {self.matched}/{self.total} tracks imported "
            f"({self.match_rate:.0f}% match rate)"
        )


def import_playlist(
    playlist: Playlist,
    apple: AppleMusicClient,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> ImportResult:
    """
    Search each Spotify track on Apple Music and create a library playlist.
    progress_cb(current, total, track_str) is called for each track processed.
    """
    found_ids: list[str] = []
    not_found: list[Track] = []

    for i, track in enumerate(playlist.tracks):
        if progress_cb:
            progress_cb(i + 1, len(playlist.tracks), str(track))

        apple_track = apple.search_track(track.title, track.artist, track.isrc)
        if apple_track:
            found_ids.append(apple_track.id)
        else:
            not_found.append(track)

    apple_playlist_id: Optional[str] = None
    if found_ids:
        apple_playlist_id = apple.create_library_playlist(
            name=playlist.name,
            description=playlist.description or f"Imported from Spotify",
            track_ids=found_ids,
        )

    return ImportResult(
        playlist_name=playlist.name,
        total=len(playlist.tracks),
        matched=len(found_ids),
        not_found=not_found,
        apple_playlist_id=apple_playlist_id,
    )

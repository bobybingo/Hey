import threading
from flask import Flask, request, jsonify, render_template, redirect, url_for

from .config import Config
from .spotify import SpotifyClient
from .apple_music import AppleMusicClient
from .importer import import_playlist, ImportResult

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = "spotify-apple-music-importer"

# Populated by main.py before the server starts
_cfg: Config
_spotify: SpotifyClient
_apple: AppleMusicClient

# Import state shared across requests
_import_state: dict = {
    "running": False,
    "current": 0,
    "total": 0,
    "current_track": "",
    "result": None,
    "error": None,
}


def init(cfg: Config, spotify: SpotifyClient, apple: AppleMusicClient) -> None:
    global _cfg, _spotify, _apple
    _cfg = cfg
    _spotify = spotify
    _apple = apple


# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        spotify_auth_url=_spotify.get_auth_url(),
        spotify_authed=_spotify.is_authenticated(),
        apple_authed=_apple.is_authenticated(),
        developer_token=_apple.get_developer_token(),
    )


# ------------------------------------------------------------------
# Spotify OAuth
# ------------------------------------------------------------------

@app.route("/spotify/callback")
def spotify_callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error or not code:
        return render_template("index.html", error=f"Spotify auth failed: {error}"), 400
    _spotify.handle_callback(code)
    return redirect(url_for("index"))


# ------------------------------------------------------------------
# Apple Music user token
# ------------------------------------------------------------------

@app.route("/apple/token", methods=["POST"])
def apple_token():
    data = request.get_json(silent=True) or {}
    token = data.get("userToken", "")
    if not token:
        return jsonify({"error": "No token provided"}), 400
    _apple.set_user_token(token)
    return jsonify({"ok": True})


# ------------------------------------------------------------------
# Playlists
# ------------------------------------------------------------------

@app.route("/api/playlists")
def list_playlists():
    if not _spotify.is_authenticated():
        return jsonify({"error": "Not authenticated with Spotify"}), 401
    playlists = _spotify.get_playlists()
    return jsonify(playlists)


# ------------------------------------------------------------------
# Import
# ------------------------------------------------------------------

@app.route("/api/import", methods=["POST"])
def start_import():
    if not _spotify.is_authenticated():
        return jsonify({"error": "Not authenticated with Spotify"}), 401
    if not _apple.is_authenticated():
        return jsonify({"error": "Not authenticated with Apple Music"}), 401
    if _import_state["running"]:
        return jsonify({"error": "Import already running"}), 409

    data = request.get_json(silent=True) or {}
    playlist_id = data.get("playlistId", "")
    if not playlist_id:
        return jsonify({"error": "Missing playlistId"}), 400

    def run():
        _import_state["running"] = True
        _import_state["result"] = None
        _import_state["error"] = None
        try:
            playlist = _spotify.get_playlist(playlist_id)
            _import_state["total"] = len(playlist.tracks)

            def on_progress(current: int, total: int, track: str) -> None:
                _import_state["current"] = current
                _import_state["total"] = total
                _import_state["current_track"] = track

            result = import_playlist(playlist, _apple, progress_cb=on_progress)
            _import_state["result"] = {
                "playlistName": result.playlist_name,
                "total": result.total,
                "matched": result.matched,
                "matchRate": round(result.match_rate, 1),
                "notFound": [str(t) for t in result.not_found],
                "applePlaylistId": result.apple_playlist_id,
            }
        except Exception as exc:
            _import_state["error"] = str(exc)
        finally:
            _import_state["running"] = False

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return jsonify({"ok": True})


@app.route("/api/import/status")
def import_status():
    return jsonify({
        "running": _import_state["running"],
        "current": _import_state["current"],
        "total": _import_state["total"],
        "currentTrack": _import_state["current_track"],
        "result": _import_state["result"],
        "error": _import_state["error"],
    })

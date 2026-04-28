# Spotify → Apple Music Playlist Importer

Import your Spotify playlists into Apple Music with a clean web UI.

## Prerequisites

- Python 3.11+
- A [Spotify Developer App](https://developer.spotify.com/dashboard)
- An [Apple Developer account](https://developer.apple.com) with an active Apple Music subscription and a MusicKit key

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|---|---|
| `SPOTIFY_CLIENT_ID` | [Spotify Dashboard](https://developer.spotify.com/dashboard) → your app → Settings |
| `SPOTIFY_CLIENT_SECRET` | Same place |
| `SPOTIFY_REDIRECT_URI` | Must match one of your app's Redirect URIs — add `http://localhost:8080/spotify/callback` |
| `APPLE_TEAM_ID` | [Apple Developer → Membership](https://developer.apple.com/account/#/membership) |
| `APPLE_KEY_ID` | [Certificates, IDs & Profiles → Keys](https://developer.apple.com/account/resources/authkeys/list) |
| `APPLE_PRIVATE_KEY_PATH` | Path to the `.p8` file downloaded when creating the MusicKit key |

#### Creating a Spotify app
1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Under **Settings → Redirect URIs**, add `http://localhost:8080/spotify/callback`

#### Creating an Apple MusicKit key
1. Go to [developer.apple.com/account/resources/authkeys/list](https://developer.apple.com/account/resources/authkeys/list)
2. Click **+** to create a new key
3. Enable **MusicKit**
4. Download the `.p8` file and note your Key ID
5. Find your Team ID on your [Membership page](https://developer.apple.com/account/#/membership)

### 3. Run

```bash
python main.py
```

A browser window will open automatically at `http://localhost:8080`.

---

## Usage

1. **Connect Spotify** — click "Connect Spotify" and log in
2. **Connect Apple Music** — click "Connect Apple Music" and authorize in the popup
3. **Select a playlist** — choose a Spotify playlist from the dropdown
4. **Import** — click "Import" and watch the progress bar

After import, a new playlist appears in your Apple Music library. Tracks not found on Apple Music (e.g. region-locked or very rare tracks) are listed in the results.

---

## How matching works

1. **ISRC lookup** (most accurate) — each Spotify track carries an ISRC code; the importer queries Apple Music's catalog directly by ISRC first
2. **Text search fallback** — if no ISRC match, a `title + artist` search is performed and the best result is selected

---

## Notes

- Apple Music's API requires an active Apple Music subscription on the authorizing account
- The importer targets the `us` storefront for catalog search; edit `APPLE_MUSIC_API` in `src/apple_music.py` to change the region
- The Spotify token is cached locally in `.spotify_token_cache`; delete it to re-authenticate

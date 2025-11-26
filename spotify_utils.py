import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from models import db, Album

load_dotenv()

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
_sp = None

def get_spotify_client():
    global _sp
    if _sp:
        return _sp
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    _sp = spotipy.Spotify(auth_manager=auth_manager)
    return _sp

def fetch_top_albums():
    sp = get_spotify_client()
    if not sp:
        raise RuntimeError("Spotify credentials not configured")
    results = sp.new_releases(limit=50)

    for album_data in results['albums']['items']:
        album_id = album_data['id']

        if Album.query.filter_by(spotify_id=album_id).first():
            continue

        try:
            tracks_data = sp.album_tracks(album_id, limit=50)['items']
            tracklist = ','.join([t['name'] for t in tracks_data])
        except Exception as e:
            print(f"Skipping album {album_data['name']} due to track fetch error: {e}")
            continue

        album = Album(
            spotify_id=album_id,
            title=album_data['name'],
            artist=album_data['artists'][0]['name'],
            cover_url=album_data['images'][0]['url'] if album_data['images'] else '',
            tracklist=tracklist
        )
        db.session.add(album)

    db.session.commit()
    print("Fetched and added top albums from Spotify!")


def add_album_by_spotify_id(album_id):
    if Album.query.filter_by(spotify_id=album_id).first():
        raise ValueError("Album already exists")

    sp = get_spotify_client()
    if not sp:
        raise RuntimeError("Spotify credentials not configured")

    try:
        album_data = sp.album(album_id)
    except Exception as e:
        raise Exception(f"Failed to fetch album from Spotify: {e}")

    try:
        tracks_data = sp.album_tracks(album_id)['items']
        tracklist = ','.join([t['name'] for t in tracks_data])
    except Exception:
        tracklist = ''

    album = Album(
        spotify_id=album_id,
        title=album_data.get('name', 'Unknown'),
        artist=album_data['artists'][0]['name'] if album_data.get('artists') else '',
        cover_url=album_data['images'][0]['url'] if album_data.get('images') else '',
        tracklist=tracklist
    )
    db.session.add(album)
    db.session.commit()
    return album

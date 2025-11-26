# Spotify Album Rater

Hosted: https://spotify-album-rater.onrender.com

Spotify Album Rater is a Flask web application that lets users rate and review music albums using the Spotify Web API. It supports user accounts with roles and admin features.

**Features**
- **Accounts & auth:** Account creation with hashed passwords (`Werkzeug` + `Flask-Login`).
- **Roles:** `USER` and `ADMIN` roles; admins can remove ratings and albums.
- **Spotify integration:** Fetch albums with `spotipy`.
- **CRUD:** All CRUD operations implemented for albums and ratings.

**Tech stack**
- **Backend:** `Flask`, `Flask-Login`, `Flask-SQLAlchemy`
- **API:** `spotipy`
- **DB:** `SQLAlchemy`
- **Forms:** `Flask-WTF`, `WTForms`



from models import Album, db, User
from werkzeug.security import generate_password_hash


def test_add_album_route_creates_album(client, app, monkeypatch):
    with app.app_context():
        user = User(username='adder', password=generate_password_hash('p'), role='USER')
        db.session.add(user)
        db.session.commit()

    client.post('/login', data={'username': 'adder', 'password': 'p'}, follow_redirects=True)

    def fake_add(album_id):
        with app.app_context():
            alb = Album(spotify_id=album_id, title='Fake Title', artist='Fake Artist')
            db.session.add(alb)
            db.session.commit()
            return alb

    monkeypatch.setattr('spotify_utils.add_album_by_spotify_id', fake_add)

    resp = client.post('/add_album', data={'spotify_link': 'https://open.spotify.com/album/abc123'}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Album.query.filter_by(spotify_id='abc123').first() is not None

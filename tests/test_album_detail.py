from models import Album, User, db
from werkzeug.security import generate_password_hash


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_album_detail_requires_login(client):
    resp = client.get('/album/1')
    assert resp.status_code in (302, 301)


def test_album_detail_show_for_logged_in(client, app):
    with app.app_context():
        user = User(username='u1', password=generate_password_hash('p'), role='USER')
        db.session.add(user)
        a = Album(spotify_id='ad1', title='Detail Album', artist='X')
        db.session.add(a)
        db.session.commit()
        album_id = a.id

    login(client, 'u1', 'p')
    resp = client.get(f'/album/{album_id}')
    assert resp.status_code == 200
    assert b'Detail Album' in resp.data

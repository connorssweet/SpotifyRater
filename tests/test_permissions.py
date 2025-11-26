from models import User, Album, Rating, db
from werkzeug.security import generate_password_hash


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_non_owner_cannot_delete_rating(client, app):
    with app.app_context():
        owner = User(username='ownerx', password=generate_password_hash('p'), role='USER')
        other = User(username='otherx', password=generate_password_hash('q'), role='USER')
        db.session.add_all([owner, other])
        album = Album(spotify_id='perm1', title='P', artist='A')
        db.session.add(album)
        db.session.commit()
        rating = Rating(score=2, comment='meh', user_id=owner.id, album_id=album.id)
        db.session.add(rating)
        db.session.commit()
        rating_id = rating.id

    login(client, 'otherx', 'q')
    resp = client.post(f'/delete_rating/{rating_id}', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Rating.query.get(rating_id) is not None


def test_non_admin_cannot_delete_album(client, app):
    with app.app_context():
        u = User(username='notadmin', password=generate_password_hash('p1'), role='USER')
        db.session.add(u)
        album = Album(spotify_id='delperm', title='Del', artist='A')
        db.session.add(album)
        db.session.commit()
        album_id = album.id

    login(client, 'notadmin', 'p1')
    resp = client.post(f'/delete_album/{album_id}', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Album.query.get(album_id) is not None

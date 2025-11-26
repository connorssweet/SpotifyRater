from models import Album, User, Rating, db
from werkzeug.security import generate_password_hash


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_create_and_update_rating(client, app):
    with app.app_context():
        user = User(username='rater', password=generate_password_hash('p'), role='USER')
        db.session.add(user)
        album = Album(spotify_id='rid', title='R Album', artist='A')
        db.session.add(album)
        db.session.commit()
        album_id = album.id
        user_id = user.id

    login(client, 'rater', 'p')
    resp = client.post(f'/album/{album_id}', data={'score': '4', 'comment': 'nice'}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        r = Rating.query.filter_by(user_id=user_id, album_id=album_id).first()
        assert r is not None and r.score == 4 and r.comment == 'nice'

    resp = client.post(f'/album/{album_id}', data={'score': '5', 'comment': 'great'}, follow_redirects=True)
    with app.app_context():
        r = Rating.query.filter_by(user_id=user_id, album_id=album_id).first()
        assert r.score == 5 and r.comment == 'great'


def test_owner_can_delete_rating(client, app):
    with app.app_context():
        user = User(username='ownr', password=generate_password_hash('p2'), role='USER')
        db.session.add(user)
        album = Album(spotify_id='own1', title='Own Album', artist='B')
        db.session.add(album)
        db.session.commit()
        rating = Rating(score=3, comment='ok', user_id=user.id, album_id=album.id)
        db.session.add(rating)
        db.session.commit()
        rating_id = rating.id

    login(client, 'ownr', 'p2')
    resp = client.post(f'/delete_rating/{rating_id}', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Rating.query.get(rating_id) is None

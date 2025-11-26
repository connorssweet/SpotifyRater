from models import User, Album, Rating, db
from werkzeug.security import generate_password_hash
import uuid


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_admin_can_delete_rating_and_album(client, app):
    with app.app_context():
        user_name = f"normal_{uuid.uuid4().hex[:8]}"
        admin_name = f"admin_{uuid.uuid4().hex[:8]}"
        user = User(username=user_name, password=generate_password_hash('p1'), role='USER')
        admin = User(username=admin_name, password=generate_password_hash('adminpass'), role='ADMIN')
        db.session.add_all([user, admin])
        db.session.commit()

        album = Album(spotify_id='zzz', title='Z', artist='A')
        db.session.add(album)
        db.session.commit()
        rating = Rating(score=4, comment='ok', user_id=user.id, album_id=album.id)
        db.session.add(rating)
        db.session.commit()

        album_id = album.id
        rating_id = rating.id

    login(client, admin_name, 'adminpass')

    resp = client.post(f'/delete_rating/{rating_id}', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Rating.query.get(rating_id) is None

    resp = client.post(f'/delete_album/{album_id}', follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Album.query.get(album_id) is None

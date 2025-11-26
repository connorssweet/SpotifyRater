from models import Album, db


def test_index_shows_albums(client, app):
    with app.app_context():
        a = Album(spotify_id='i1', title='Index Album', artist='Artist')
        db.session.add(a)
        db.session.commit()

    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Index Album' in resp.data

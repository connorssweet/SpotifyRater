from models import User, db
from werkzeug.security import generate_password_hash


def test_signup_creates_user(client, app):
    resp = client.post('/signup', data={'username': 'tester', 'password': 'pass'}, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        u = User.query.filter_by(username='tester').first()
        assert u is not None


def test_login(client, app):
    with app.app_context():
        user = User(username='loginuser', password=generate_password_hash('pwd'), role='USER')
        db.session.add(user)
        db.session.commit()

    resp = client.post('/login', data={'username': 'loginuser', 'password': 'pwd'}, follow_redirects=True)
    assert resp.status_code == 200

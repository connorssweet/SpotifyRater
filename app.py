from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Album, Rating
import re
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///spotify_rater.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fake-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_db(interactive=True):
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role='ADMIN').first():
            admin_username = os.getenv('ADMIN_USERNAME')
            admin_password = os.getenv('ADMIN_PASSWORD')
            if not admin_username or not admin_password:
                if interactive:
                    print("No ADMIN user found. Create one now:")
                    admin_username = input("Admin username: ").strip()
                    admin_password = input("Admin password: ").strip()
            if admin_username and admin_password:
                admin = User(username=admin_username, password=generate_password_hash(admin_password), role='ADMIN')
                db.session.add(admin)
                db.session.commit()
                print(f"Admin user '{admin_username}' created.\n")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if not os.getenv('SKIP_DB_INIT') and 'PYTEST_CURRENT_TEST' not in os.environ:
    try:
        init_db(interactive=False)
        try:
            app.logger.info("Database initialized at import time")
        except Exception:
            print("Database initialized at import time")
    except Exception as e:
        try:
            app.logger.exception("Import-time DB init failed: %s", e)
        except Exception:
            print("Import-time DB init failed:", e)

    if os.getenv('FETCH_TOP_ALBUMS_ON_START') == '1' and 'PYTEST_CURRENT_TEST' not in os.environ:
        try:
            from spotify_utils import get_spotify_client, fetch_top_albums
            if get_spotify_client() is not None:
                try:
                    with app.app_context():
                        fetch_top_albums()
                    try:
                        app.logger.info("Fetched top albums from Spotify at startup")
                    except Exception:
                        print("Fetched top albums from Spotify at startup")
                except Exception as e:
                    try:
                        app.logger.exception("Failed to fetch top albums: %s", e)
                    except Exception:
                        print("Failed to fetch top albums:", e)
            else:
                try:
                    app.logger.info("Skipping fetch_top_albums: Spotify creds not configured")
                except Exception:
                    print("Skipping fetch_top_albums: Spotify creds not configured")
        except Exception as e:
            try:
                app.logger.exception("Error during fetch_top_albums startup: %s", e)
            except Exception:
                print("Error during fetch_top_albums startup:", e)
            
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for('signup'))
        new_user = User(username=username, password=password, role='USER')
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    albums = Album.query.all()
    return render_template('index.html', albums=albums)

@app.route('/album/<int:album_id>', methods=['GET', 'POST'])
@login_required
def album_detail(album_id):
    album = Album.query.get_or_404(album_id)
    if request.method == 'POST':
        score = int(request.form['score'])
        comment = request.form.get('comment')
        rating = Rating.query.filter_by(user_id=current_user.id, album_id=album_id).first()
        if rating:
            rating.score = score
            rating.comment = comment
        else:
            rating = Rating(score=score, comment=comment, user=current_user, album=album)
            db.session.add(rating)
        db.session.commit()
    return render_template('album_detail.html', album=album)

@app.route('/delete_rating/<int:rating_id>', methods=['POST'])
@login_required
def delete_rating(rating_id):
    rating = Rating.query.get_or_404(rating_id)

    if rating.user_id != current_user.id and not getattr(current_user, 'is_admin', False):
        flash("You cannot delete this rating")
        return redirect(url_for('index'))
    db.session.delete(rating)
    db.session.commit()
    return redirect(url_for('album_detail', album_id=rating.album_id))

@app.route('/delete_album/<int:album_id>', methods=['POST'])
@login_required
def delete_album(album_id):
    if not getattr(current_user, 'is_admin', False):
        flash("Admin privileges required")
        return redirect(url_for('index'))
    album = Album.query.get_or_404(album_id)

    Rating.query.filter_by(album_id=album.id).delete()
    db.session.delete(album)
    db.session.commit()
    flash("Album deleted")
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    albums = Album.query.filter(
        Album.title.ilike(f'%{query}%') | Album.artist.ilike(f'%{query}%')
    ).all()
    return render_template('search_results.html', albums=albums, query=query)

@app.route('/add_album', methods=['GET', 'POST'])
@login_required
def add_album():
    if request.method == 'POST':
        spotify_link = request.form.get('spotify_link', '').strip()
        # https://open.spotify.com/album/<id>
        # spotify:album:<id>
        m = re.search(r'(?:album[/:])([A-Za-z0-9]+)', spotify_link)
        if not m:
            m = re.search(r'spotify:album:([A-Za-z0-9]+)', spotify_link)
        if not m:
            flash("Invalid Spotify album link or URI")
            return redirect(url_for('add_album'))

        album_id = m.group(1)

        existing = Album.query.filter_by(spotify_id=album_id).first()
        if existing:
            flash("This album already exists on the site.")
            return redirect(url_for('album_detail', album_id=existing.id))

        try:
            from spotify_utils import add_album_by_spotify_id
            album = add_album_by_spotify_id(album_id)
            flash("Album added successfully.")
            return redirect(url_for('album_detail', album_id=album.id))
        except ValueError:
            flash("This album already exists on the site.")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Failed to add album: {e}")
            return redirect(url_for('add_album'))

    return render_template('add_album.html')

if __name__ == '__main__':
    init_db()
    app.run()

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# --- NAYA STRUCTURE (ERROR FIX) ---

# 1. Pehle App aur Config banao
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bidhan-yeh-key-bahut-secret-rakhna'

# Database URL config (Local aur Hosting dono ke liye)
DATABASE_URL = os.environ.get('DATABASE_URL') 
if DATABASE_URL:
    # Render (Hosting) ke liye
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Local computer ke liye
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gaya_map.db'

app.config['UPLOAD_FOLDER'] = 'static/uploads'


# 2. Ab 'db' ko import karo aur 'app' se jodo
from models import db
db.init_app(app)


# 3. Ab Login Manager ko jodo
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'


# 4. Ab jab sab connect ho gaya hai, TAB Models aur Forms ko import karo
from models import User, LocationPin
from forms import LoginForm, RegistrationForm

# --- FIX KHATAM ---


@login_manager.user_loader
def load_user(user_id):
    # === YEH LINE BADAL DI GAYI HAI ===
    return db.session.get(User, int(user_id))
    # === WARNING FIX HO GAYI ===

# --- Routes (Pages) ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check username and password.')

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('That username is already taken. Please choose a different one.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- API Routes (Data ke liye) ---

@app.route('/api/add_pin', methods=['POST'])
@login_required
def add_pin():
    name = request.form.get('name')
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    image = request.files.get('image')

    if not name or not lat or not lng:
         return jsonify({'error': 'Missing data'}), 400

    filename = None
    if image:
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

    new_pin = LocationPin(
        name=name, 
        lat=float(lat), 
        lng=float(lng), 
        image_filename=filename,
        author=current_user
    )
    db.session.add(new_pin)
    db.session.commit()
    
    return jsonify({
        'message': 'Pin added!',
        'pin': {
            'name': new_pin.name,
            'lat': new_pin.lat,
            'lng': new_pin.lng,
            'image_url': url_for('static', filename=f'uploads/{new_pin.image_filename}') if new_pin.image_filename else None,
            'author': new_pin.author.username
        }
    })

@app.route('/api/get_pins')
@login_required
def get_pins():
    pins = LocationPin.query.all()
    pin_list = []
    for pin in pins: # <-- Loop variable 'pin' hai
        pin_list.append({
            'name': pin.name,
            'lat': pin.lat,
            'lng': pin.lng,
            # === YEH LINE THEEK KAR DI GAYI HAI ===
            'image_url': url_for('static', filename=f'uploads/{pin.image_filename}') if pin.image_filename else None,
            # === 'new_pin' ko 'pin' kar diya hai ===
            'author': pin.author.username
        })
    return jsonify(pin_list)

# --- Server Start ---

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    with app.app_context():
        db.create_all() # Database tables banata hai
        
    app.run(debug=True)
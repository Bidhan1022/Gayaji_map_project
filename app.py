# app.py
print("DEBUG: File ke bilkul shuru mein")
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
print("DEBUG: Saare imports ho gaye")

# Files se import
from models import db, User, LocationPin
from forms import LoginForm, RegistrationForm # YAHAN import karein

# App Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bidhan-yeh-key-bahut-secret-rakhna'

# ✅ Database URL from environment (Render, Railway, etc.)
DATABASE_URL = os.environ.get('DATABASE_URL')

# ✅ Fix old-style URL "postgres://" to "postgresql://"
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ✅ Set final database URI
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL  # <-- Ye line missing thi!

# ✅ File upload folder
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ✅ Initialize SQLAlchemy properly
db = SQLAlchemy(app)


# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Agar login nahi hai toh 'login' page par bhejo
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes (Pages) ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index')) # Agar pehle se login hai toh map par bhejo

    form = LoginForm() # Form ko load karo
    if form.validate_on_submit(): # Agar form submit hua aur sahi hai
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user) # User ko login karo
            return redirect(url_for('index')) # Map page par bhejo
        else:
            flash('Login unsuccessful. Please check username and password.')

    return render_template('login.html', form=form) # Form ko HTML mein bhejo

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm() # Register form load karo
    if form.validate_on_submit():
        # Check karo user pehle se toh nahi hai
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('That username is already taken. Please choose a different one.')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Your account has been created! You can now log in.')
        return redirect(url_for('login')) # Login page par bhejo

    return render_template('register.html', form=form) # Form ko HTML mein bhejo

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

    # Naye pin ka data wapas bhejo taaki JS use turant add kar sake
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
    for pin in pins:
        pin_list.append({
            'name': pin.name,
            'lat': pin.lat,
            'lng': pin.lng,
            'image_url': url_for('static', filename=f'uploads/{pin.image_filename}') if pin.image_filename else None,
            'author': pin.author.username
        })
    return jsonify(pin_list)

print("DEBUG: 'if __name__' se thik pehle")
#if __name__ == '__main__' block ko aisa update karein
if __name__ == '__main__':
    print("DEBUG: 'if __name__' ke andar aa gaya") # <-- YEH ADD KAREIN
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER']) # Upload folder banao agar nahi hai
    
    # Naya tareeka: app context ke andar database create karein
    with app.app_context():
        db.create_all()
        print("DEBUG: Database create ho gaya") # <-- YEH BHI ADD KAREIN
    print("DEBUG: Ab server RUN hone wala hai...") # <-- YEH BHI ADD KAREIN
    app.run(debug=True) # Server ko start karein
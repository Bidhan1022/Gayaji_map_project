import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# --- 1. App aur Config Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'myreallystrongsecretkey12345'

# Sirf local database ka simple config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gaya_map.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# --- 2. Extensions ko App se Jodo ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# --- 3. Models (Database Tables) ---
# User model ko yahi define kar diya
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    # Relationship: User ne kitne Pin banaye
    pins = db.relationship('LocationPin', backref='author', lazy=True)

# LocationPin model ko yahi define kar diya
class LocationPin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    # Relationship: Pin kisne banaya (Foreign Key)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# --- 4. Forms (Login/Register Forms) ---
# RegistrationForm ko yahi define kar diya
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# LoginForm ko yahi define kar diya
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# --- 5. Login Manager ka Helper Function ---
@login_manager.user_loader
def load_user(user_id):
    # Aapka fix kiya hua code
    return db.session.get(User, int(user_id))

# --- 6. Routes (Pages) ---

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm() # Form ab upar defined hai
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

    form = RegistrationForm() # Form ab upar defined hai
    if form.validate_on_submit():
        # Ye check aapke original code mein tha, isliye rakha hai
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

# --- 7. API Routes (Data ke liye) ---

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
    for pin in pins: # Aapka fix kiya hua loop variable 'pin'
        pin_list.append({
            'name': pin.name,
            'lat': pin.lat,
            'lng': pin.lng,
            'image_url': url_for('static', filename=f'uploads/{pin.image_filename}') if pin.image_filename else None,
            'author': pin.author.username
        })
    return jsonify(pin_list)

# --- 8. Server Start ---

if __name__ == '__main__':
    # Check karo ki 'uploads' folder hai ya nahi
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # App ke context mein database create karo
    with app.app_context():
        db.create_all() # Database tables banata hai
        
    app.run(debug=True)
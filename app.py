import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = '/home/umbx/umbx2/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))

def get_user_upload_folder(user_id):
    return os.path.join(app.config['UPLOAD_FOLDER'], str(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return render_template('auth/index.html', error='Invalid credentials')
    return render_template('auth/index.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            return render_template('auth/register.html', error='Username exists')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        os.makedirs(get_user_upload_folder(new_user.id), exist_ok=True)
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    files = File.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', user=user, files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    
    filename = secure_filename(file.filename)
    user_folder = get_user_upload_folder(session['user_id'])
    
    # Create user directory if not exists
    os.makedirs(user_folder, exist_ok=True)  # <-- ADD THIS LINE
    
    file_path = os.path.join(user_folder, filename)
    file.save(file_path)
    
    new_file = File(filename=filename, user_id=session['user_id'])
    db.session.add(new_file)
    db.session.commit()
    
    return '', 204

@app.route('/delete/<int:file_id>')
def delete_file(file_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    file = File.query.get_or_404(file_id)
    if file.user_id != session['user_id']:
        return 'Unauthorized', 403
    
    user_folder = get_user_upload_folder(session['user_id'])
    file_path = os.path.join(user_folder, file.filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(file)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/direct/<uuid>')
def direct_download(uuid):
    file = File.query.filter_by(uuid=uuid).first_or_404()
    user_folder = get_user_upload_folder(file.user_id)
    return send_from_directory(user_folder, file.filename, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

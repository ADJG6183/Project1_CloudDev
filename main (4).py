import os
from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from google.cloud import storage
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__)

# ✅ Step 1: Load credentials dynamically
DEFAULT_CREDENTIALS_PATH = "/home/aarongreen6183/myproject-1-450903-08a71306aee3.json"
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", DEFAULT_CREDENTIALS_PATH)

if not os.path.exists(credentials_path):
    raise FileNotFoundError(
        f" Google Cloud credentials not found at: {credentials_path}\n"
        "\n FIX: Ensure the credentials file is at the expected path or set the environment variable:\n"
        "export GOOGLE_APPLICATION_CREDENTIALS='/absolute/path/to/your-credentials.json'"
    )

# ✅ Step 2: Initialize Firebase and Google Cloud Storage client
cred = credentials.Certificate(credentials_path)
firebase_admin.initialize_app(cred)
storage_client = storage.Client.from_service_account_json(credentials_path)

bucket_name = "project-1-bukket"
bucket = storage_client.bucket(bucket_name)

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# ✅ Step 3: Authentication decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ✅ Step 4: Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            auth.create_user(email=email, password=password)
            flash("Signup successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(str(e), "danger")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.get_user_by_email(email)
            session['user_email'] = email
            flash("Login successful!", "success")
            return redirect(url_for('gallery'))
        except Exception:
            flash("Invalid credentials. Try again.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash("No file part", "danger")
            return redirect(request.url)
        file = request.files['image']
        if file.filename == '':
            flash("No selected file", "danger")
            return redirect(request.url)
        if file:
            blob = bucket.blob(file.filename)
            blob.upload_from_file(file, content_type=file.content_type)
            flash("Image uploaded successfully!", "success")
            return redirect(url_for('gallery'))
    return render_template('upload_image.html')

@app.route('/gallery')
@login_required
def gallery():
    blobs = bucket.list_blobs()
    image_urls = [blob.public_url for blob in blobs]
    return render_template('gallery.html', images=image_urls)

# ✅ Step 5: Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=True)
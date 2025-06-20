from flask import Flask, request, render_template, redirect
import pandas as pd
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import jsonify
from flask_mail import Mail, Message
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret'

# 🔹 Define your fake database here:
# users_db = {}

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["SE_mentalhealth"]
collection = db["user_data_1"]
register_db = db["register_details"]
login_db = db["user_login"]


# Feature columns
features = [
    "age", "self_esteem", "mental_health_history", "depression", "headache", "blood_pressure",
    "sleep_quality", "breathing_problem", "noise_level", "future_career_concerns", 
    "social_support", "peer_pressure"
]

# Features used for anxiety level calculation
anxiety_features = [
    "self_esteem", "mental_health_history", "depression", "headache", "blood_pressure",
    "sleep_quality", "breathing_problem", "noise_level", "future_career_concerns",
    "social_support", "peer_pressure"
]

def get_anxiety_severity(average_score):
    """Determine severity based on average score."""
    if average_score < 6:
        return "Healthy"
    elif 6 <= average_score <= 8:
        return "Medium"
    else:
        return "High"

@app.route("/")
def home_redirect():
    return redirect("/login")  # Redirect to home.html

@app.route("/home")
def home():
    if 'user' not in session:
        flash("Please log in to access the dashboard.", "warning")
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    return render_template("home.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        print("Login attempt:", email)

        user = db.users.find_one({'email': email})
        if user:
            print("User found in DB:", user['email'])
        else:
            print("User not found.")

        if user and check_password_hash(user['password'], password):
            session['user'] = email  # Store the email in the session
            session['name'] = user['name']
            flash("Login successful!", "success")
            print("Session set for:", session['user'])
            return redirect(url_for('home'))  # Redirect to index page after successful login
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))  # Redirect back to login page on error

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("🔥 Inside /signup route")  # Add this!

    if request.method == 'POST':
        print("🚀 Received POST request!")

        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        print(f"📩 Data: {name}, {username}, {email}")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('signup'))

        if db.users.find_one({'email': email}):
            flash("Email already registered.", "danger")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        db.users.insert_one({
            'name': name,
            'username': username,
            'email': email,
            'password': hashed_password
        })

        print("✅ User inserted!")

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')




@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        if email in login_db:
            flash('Password reset link sent to your email! (Simulated)', 'info')
            return redirect(url_for('reset_success'))
        else:
            flash('Email not found', 'danger')
    return render_template('forgot_password.html')

@app.route('/reset-success')
def reset_success():
    return render_template('reset_success.html')

@app.route("/breathing")
def breathing():
    return render_template("breathing.html")

@app.route("/yoga")
def yoga():
    return render_template("yoga.html")

@app.route("/appointment_high")
def appointment_high():
    return render_template("appointment_high.html")

@app.route("/appointment_child")
def appointment_child():
    return render_template("appointment_child.html")

@app.route("/appointment_low_medium")
def appointment_low_medium():
    return render_template("appointment_low_medium.html")

@app.route("/form", methods=["GET"])
def form():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])

@app.route("/submit", methods=["POST"])
def submit():
    try:
        # Extract user input safely
        user_data_1 = {}
        for feature in features:
            value = request.form.get(feature, "0")  # Default to "0" if missing
            try:
                user_data_1[feature] = int(value) if feature == "age" else float(value)
            except ValueError:
                user_data_1[feature] = 0  # Default to 0 if conversion fails

        print("User Data:", user_data_1)  # Debugging: Check the extracted data

        # Insert into MongoDB
        insert_result = collection.insert_one(user_data_1)
        print("MongoDB Inserted ID:", insert_result.inserted_id)  # Debugging

        # Calculate anxiety score
        anxiety_scores = [user_data_1[feature] for feature in anxiety_features]
        avg_score = round(sum(anxiety_scores) / len(anxiety_features))

        # Determine severity
        severity = get_anxiety_severity(avg_score)

        # Pass age to results.html
        return render_template("results.html", prediction=avg_score, severity=severity, age=user_data_1["age"])

    except Exception as e:
        return f"Error: {str(e)}"

@app.route("/logout")
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))  # Redirect to login page after logout

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


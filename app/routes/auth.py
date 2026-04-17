from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.dbconfig.models import User
from app.dbconfig.extensions import db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    return render_template("auth/landing.html")

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    # FIX: Send logged-in users to the REAL dashboard, not the info page
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard')) 

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Query the database for the user
        user = User.query.filter_by(email=email).first()

        # Check if user exists AND the hashed password matches
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.name
            
            # FIX: Send to the REAL dashboard
            return redirect(url_for('dashboard.dashboard')) 
        else:
            flash('Invalid email or password. Please try again.', 'error')

    return render_template("auth/login.html")

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    # FIX: Send logged-in users to the REAL dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard')) 

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return redirect(url_for('auth.register'))

        new_user = User(email=email, name=name)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        session.clear()
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['user_name'] = new_user.name
        
        # FIX: Send to the REAL dashboard
        return redirect(url_for('dashboard.dashboard'))

    return render_template("auth/register.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.index'))

@auth_bp.route("/features")
def features():
    return render_template("auth/features.html")

@auth_bp.route("/dashboard-info")
def dashboard_info():
    return render_template("auth/dashboard_info.html")

@auth_bp.route("/compare-info")
def compare_info():
    return render_template("auth/compare_info.html")

@auth_bp.route("/about")
def about():
    return render_template("auth/about.html")
"""
Authentication routes for Flask application
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from forms import LoginForm, PatientRegistrationForm
from db_utils import fetch_one, execute_insert
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login view"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Query user using raw SQL
        user_data = fetch_one(
            "SELECT * FROM core_customuser WHERE username = %s",
            (username,)
        )
        
        if user_data:
            # Create User object from data
            user = User.query.get(user_data['id'])
            if not user:
                # If user not in SQLAlchemy session, create it
                user = User()
                for key, value in user_data.items():
                    setattr(user, key, value)
            
            # Check password
            if user.check_password(password):
                login_user(user, remember=True)
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(url_for('auth.dashboard'))
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout view"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Route to appropriate dashboard based on user role"""
    if current_user.role == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
    elif current_user.role == 'DOCTOR':
        return redirect(url_for('doctor.dashboard'))
    elif current_user.role == 'PATIENT':
        return redirect(url_for('patient.dashboard'))
    else:
        flash('Invalid user role.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def patient_registration():
    """Patient registration view"""
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    form = PatientRegistrationForm()
    
    # Populate form choices dynamically (if needed)
    # For now, form fields are static
    
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = fetch_one(
            "SELECT id FROM core_customuser WHERE username = %s",
            (form.username.data,)
        )
        if existing_user:
            flash('Username already exists.', 'error')
            return render_template('patient/registration.html', form=form)
        
        # Check if national_id already exists
        existing_patient = fetch_one(
            "SELECT patient_id FROM core_patient WHERE national_id = %s",
            (form.national_id.data,)
        )
        if existing_patient:
            flash('National ID already registered.', 'error')
            return render_template('patient/registration.html', form=form)
        
        # Create user account
        from werkzeug.security import generate_password_hash
        from datetime import datetime
        
        user_sql = """INSERT INTO core_customuser 
                     (username, password, email, first_name, last_name, is_active, 
                      is_staff, is_superuser, date_joined, role, hospital_id)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        # Split full_name into first and last
        name_parts = form.full_name.data.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        hashed_password = generate_password_hash(form.password.data)
        user_id = execute_insert(
            user_sql,
            (form.username.data, hashed_password, form.email.data, first_name, last_name,
             True, False, False, datetime.utcnow(), 'PATIENT', None)
        )
        
        # Create patient record
        patient_sql = """INSERT INTO core_patient 
                        (national_id, full_name, date_of_birth, gender, phone, email, address,
                         blood_type, occupation, marital_status, birth_place, father_name, mother_name, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        patient_id = execute_insert(
            patient_sql,
            (form.national_id.data, form.full_name.data, form.date_of_birth.data,
             form.gender.data, form.phone.data, form.email.data, form.address.data,
             form.blood_type.data, form.occupation.data or None, form.marital_status.data,
             form.birth_place.data, form.father_name.data, form.mother_name.data, user_id)
        )
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('patient/registration.html', form=form)


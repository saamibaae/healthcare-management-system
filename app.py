"""
Flask application entry point
"""
from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.doctor import doctor_bp
from routes.patient import patient_bp
from commands.load_data import register_command

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login"""
    from db_utils import fetch_one
    user_data = fetch_one(
        "SELECT * FROM core_customuser WHERE id = %s",
        (int(user_id),)
    )
    if user_data:
        user = User()
        for key, value in user_data.items():
            setattr(user, key, value)
        return user
    return None


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(patient_bp, url_prefix='/patient')
    
    # Register CLI commands
    register_command(app)
    
    # Create database tables (if they don't exist)
    # Note: We're using existing tables, so this is mainly for SQLAlchemy mapping
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            # Tables already exist, which is fine
            pass
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)


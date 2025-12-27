"""
Flask configuration settings
"""
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'flask-insecure-9!jhht%fxk^#^r5a6*i#pm#hzajr5!k%gw2!s9*oomxq9n+p16'
    DEBUG = True
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = int(os.environ.get('DB_PORT') or 3306)
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    DB_NAME = os.environ.get('DB_NAME') or 'healthcare_db'
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Flask-Login configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Static files
    STATIC_FOLDER = BASE_DIR / 'static'
    STATIC_URL_PATH = '/static'
    TEMPLATE_FOLDER = BASE_DIR / 'templates'
    
    # Media files
    MEDIA_FOLDER = BASE_DIR / 'media'
    MEDIA_URL_PATH = '/media'
    
    # Timezone
    TIMEZONE = 'Asia/Dhaka'
    
    # Login URLs
    LOGIN_URL = 'auth.login'
    LOGIN_REDIRECT_URL = 'auth.dashboard'
    LOGOUT_REDIRECT_URL = 'auth.login'


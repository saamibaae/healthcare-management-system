"""
Flask decorators for role-based access control
"""
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def role_required(role):
    """
    Decorator to restrict access based on user role.
    Usage: @role_required('ADMIN') or @role_required('DOCTOR') or @role_required('PATIENT')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('You must be logged in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.role != role:
                flash(f'Access denied. This page is only for {role.lower()}s.', 'error')
                return redirect(url_for('auth.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def hospital_staff_required(f):
    """
    Decorator to ensure user is hospital staff (Admin or Doctor).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('You must be logged in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if current_user.role not in ['ADMIN', 'DOCTOR']:
            flash('Access denied. This page is only for hospital staff.', 'error')
            return redirect(url_for('auth.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


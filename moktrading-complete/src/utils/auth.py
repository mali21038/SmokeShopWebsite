from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not session.get('is_admin', False):
            if request.is_json:
                return jsonify({'error': 'Admin privileges required'}), 403
            flash('Admin privileges required to access this page.', 'error')
            return redirect(url_for('customer.home'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user from session"""
    from src.models.unified_models import User
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None

def login_user(user):
    """Log in a user by setting session variables"""
    session['user_id'] = user.id
    session['username'] = user.username
    session['is_admin'] = user.is_admin
    session['full_name'] = user.full_name

def logout_user():
    """Log out the current user by clearing session"""
    session.clear()

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def is_admin():
    """Check if current user is admin"""
    return session.get('is_admin', False)


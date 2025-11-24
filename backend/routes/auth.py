"""
Authentication routes for user registration and login
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from database.models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        payload = User.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated

def role_required(*roles):
    """Decorator to restrict access by role"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.user['role'] not in roles:
                return jsonify({'error': 'Access denied'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        full_name = data.get('full_name', '').strip()
        
        # Validate username
        if len(username) < 3 or len(username) > 50:
            return jsonify({'error': 'Username must be 3-50 characters'}), 400
        
        # Validate password
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.get_user_by_email(email):
            return jsonify({'error': 'Email already registered'}), 409
        
        if User.get_user_by_username(username):
            return jsonify({'error': 'Username already taken'}), 409
        
        # Create user
        user = User.create_user(
            username=username,
            email=email,
            password=password,
            full_name=full_name if full_name else None
        )
        
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
        
        # Generate token
        token = User.generate_token(user)
        
        logger.info(f"✓ New user registered: {username} ({email})")
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': str(user['id']),
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"✗ Signup error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Authenticate user
        user = User.authenticate(email, password)
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate token
        token = User.generate_token(user)
        
        logger.info(f"✓ User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['id']),
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current authenticated user's profile"""
    try:
        user = User.get_user_by_id(request.user['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': str(user['id']),
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                'last_login': user['last_login'].isoformat() if user['last_login'] else None
            }
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Get current user error: {e}")
        return jsonify({'error': 'Failed to get user profile'}), 500

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user': {
            'id': request.user['user_id'],
            'username': request.user['username'],
            'email': request.user['email'],
            'role': request.user['role']
        }
    }), 200

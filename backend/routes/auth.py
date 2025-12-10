"""
Authentication routes for user registration and login
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import logging
import re
from database.models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    """
    Validate password strength
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[ !@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False, "Password must contain at least one special character"
    return True, ""

def validate_username(username):
    """
    Validate username format
    - 3-20 characters
    - Alphanumeric and underscores only
    """
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return False, "Username must be 3-20 characters and contain only letters, numbers, and underscores"
    return True, ""

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
        
        # Pass current_user as a keyword argument if the function expects it
        import inspect
        sig = inspect.signature(f)
        if 'current_user' in sig.parameters:
            kwargs['current_user'] = payload
            
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

import re

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
        birth_date = data.get('birth_date')
        country = data.get('country', '').strip()
        phone_number = data.get('phone_number', '').strip()
        
        # Validate username
        is_valid_username, username_error = validate_username(username)
        if not is_valid_username:
            return jsonify({'error': username_error}), 400
        
        # Validate password
        is_valid_password, password_error = validate_password(password)
        if not is_valid_password:
            return jsonify({'error': password_error}), 400

        # Validate email format
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return jsonify({'error': 'Invalid email format'}), 400
        
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
            full_name=full_name if full_name else None,
            birth_date=birth_date if birth_date else None,
            country=country if country else None,
            phone_number=phone_number if phone_number else None
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
            'user': user
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Get current user error: {e}")
        return jsonify({'error': 'Failed to get user profile'}), 500

import os
from werkzeug.utils import secure_filename

# ... existing imports ...

# Configure upload folder for profile pictures
UPLOAD_FOLDER = 'uploads/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user_id = request.user['user_id']
        
        updated_user = User.update_user(user_id, data)
        
        if not updated_user:
            return jsonify({'error': 'Failed to update profile'}), 400
            
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user
        }), 200
        
    except Exception as e:
        logger.error(f"✗ Update profile error: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """Verify if token is valid"""
    # Fetch full user details from DB
    user = User.get_user_by_id(request.user['user_id'])
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    return jsonify({
        'valid': True,
        'user': user
    }), 200

def validate_image_header(stream):
    """Validate image file header (magic numbers)"""
    header = stream.read(512)
    stream.seek(0)
    
    if header.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif header.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
        return 'gif'
    return None

@auth_bp.route('/profile-picture', methods=['POST'])
@token_required
def upload_profile_picture():
    """Upload user profile picture"""
    try:
        if 'profile_picture' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['profile_picture']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            # Validate image content
            if not validate_image_header(file.stream):
                return jsonify({'error': 'Invalid image file content'}), 400

            filename = secure_filename(file.filename)
            # Add timestamp to filename to avoid caching/collisions
            import time
            filename = f"{int(time.time())}_{filename}"
            
            # Save to uploads directory
            # Ensure uploads directory exists
            upload_dir = os.path.join('uploads', 'profile_pictures')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            file.save(os.path.join(upload_dir, filename))
            
            # Update user in database
            user_id = request.user['user_id']
            # Store path relative to uploads folder
            db_filename = f"profile_pictures/{filename}"
            User.update_user(user_id, {'profile_picture': db_filename})
            
            return jsonify({
                'message': 'Profile picture uploaded successfully',
                'filename': db_filename
            }), 200
            
        return jsonify({'error': 'File type not allowed'}), 400
        
    except Exception as e:
        logger.error(f"✗ Upload profile picture error: {e}")
        return jsonify({'error': 'Failed to upload profile picture'}), 500

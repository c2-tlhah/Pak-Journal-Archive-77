"""
User model and authentication functions
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from database.db_config import get_db_cursor

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = 'your-secret-key-change-in-production'  # Change this!
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class User:
    """User model for authentication and authorization"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create_user(username: str, email: str, password: str, full_name: str = None, role: str = 'user') -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            password_hash = User.hash_password(password)
            
            with get_db_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, full_name, role)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, username, email, full_name, role, created_at
                """, (username, email, password_hash, full_name, role))
                
                user = cursor.fetchone()
                logger.info(f"✓ User created: {username} ({email})")
                return dict(user)
        except Exception as e:
            logger.error(f"✗ Failed to create user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT id, username, email, password_hash, full_name, role, is_active, last_login
                    FROM users WHERE email = %s
                """, (email,))
                
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"✗ Failed to get user by email: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT id, username, email, password_hash, full_name, role, is_active, last_login
                    FROM users WHERE username = %s
                """, (username,))
                
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"✗ Failed to get user by username: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            with get_db_cursor(commit=False) as cursor:
                cursor.execute("""
                    SELECT id, username, email, full_name, role, is_active, created_at, last_login
                    FROM users WHERE id = %s
                """, (user_id,))
                
                user = cursor.fetchone()
                return dict(user) if user else None
        except Exception as e:
            logger.error(f"✗ Failed to get user by ID: {e}")
            return None
    
    @staticmethod
    def update_last_login(user_id: str):
        """Update user's last login timestamp"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (user_id,))
                logger.info(f"✓ Updated last login for user: {user_id}")
        except Exception as e:
            logger.error(f"✗ Failed to update last login: {e}")
    
    @staticmethod
    def authenticate(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        user = User.get_user_by_email(email)
        
        if not user:
            logger.warning(f"✗ Authentication failed: User not found ({email})")
            return None
        
        if not user['is_active']:
            logger.warning(f"✗ Authentication failed: User inactive ({email})")
            return None
        
        if not User.verify_password(password, user['password_hash']):
            logger.warning(f"✗ Authentication failed: Invalid password ({email})")
            return None
        
        # Update last login
        User.update_last_login(user['id'])
        
        # Remove password hash from response
        user.pop('password_hash', None)
        logger.info(f"✓ User authenticated: {email}")
        return user
    
    @staticmethod
    def generate_token(user: Dict[str, Any]) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': str(user['id']),
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("✗ Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("✗ Invalid token")
            return None

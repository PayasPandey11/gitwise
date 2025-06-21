"""Authentication module for user login and session management."""

import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class AuthManager:
    """Manages user authentication and JWT tokens."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = timedelta(hours=24)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return self.hash_password(password) == hashed
    
    def generate_token(self, user_id: str, email: str) -> str:
        """Generate a JWT token for authenticated user."""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + self.token_expiry
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

def login_user(username: str, password: str, auth_manager: AuthManager) -> Optional[str]:
    """Authenticate user and return token if successful."""
    # In real implementation, this would check against database
    mock_users = {
        'admin': 'hashed_admin_password',
        'user': 'hashed_user_password'
    }
    
    if username in mock_users:
        if auth_manager.verify_password(password, mock_users[username]):
            return auth_manager.generate_token(username, f"{username}@example.com")
    
    return None 
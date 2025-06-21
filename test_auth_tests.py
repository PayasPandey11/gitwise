"""Unit tests for authentication module and middleware."""

import unittest
from unittest.mock import patch, MagicMock
from test_auth import AuthManager, login_user
from test_middleware import AuthMiddleware

class TestAuthManager(unittest.TestCase):
    """Test cases for AuthManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_manager = AuthManager("test_secret_key")
    
    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "test_password"
        hashed = self.auth_manager.hash_password(password)
        
        # Hash should be deterministic
        self.assertEqual(hashed, self.auth_manager.hash_password(password))
        
        # Different passwords should produce different hashes
        different_hash = self.auth_manager.hash_password("different_password")
        self.assertNotEqual(hashed, different_hash)
    
    def test_password_verification(self):
        """Test password verification against hash."""
        password = "test_password"
        hashed = self.auth_manager.hash_password(password)
        
        # Correct password should verify
        self.assertTrue(self.auth_manager.verify_password(password, hashed))
        
        # Incorrect password should not verify
        self.assertFalse(self.auth_manager.verify_password("wrong_password", hashed))
    
    def test_token_generation_and_verification(self):
        """Test JWT token generation and verification."""
        user_id = "test_user"
        email = "test@example.com"
        
        # Generate token
        token = self.auth_manager.generate_token(user_id, email)
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)
        
        # Verify token
        payload = self.auth_manager.verify_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], user_id)
        self.assertEqual(payload['email'], email)
    
    def test_invalid_token_verification(self):
        """Test verification of invalid tokens."""
        # Invalid token should return None
        invalid_payload = self.auth_manager.verify_token("invalid_token")
        self.assertIsNone(invalid_payload)

class TestLoginFunction(unittest.TestCase):
    """Test cases for login functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_manager = AuthManager("test_secret_key")
    
    def test_successful_login(self):
        """Test successful user login."""
        # Mock the password verification to succeed
        with patch.object(self.auth_manager, 'verify_password', return_value=True):
            token = login_user("admin", "correct_password", self.auth_manager)
            self.assertIsNotNone(token)
            
            # Verify the token contains correct user info
            payload = self.auth_manager.verify_token(token)
            self.assertEqual(payload['user_id'], "admin")
            self.assertEqual(payload['email'], "admin@example.com")
    
    def test_failed_login_wrong_password(self):
        """Test login failure with wrong password."""
        with patch.object(self.auth_manager, 'verify_password', return_value=False):
            token = login_user("admin", "wrong_password", self.auth_manager)
            self.assertIsNone(token)
    
    def test_failed_login_unknown_user(self):
        """Test login failure with unknown username."""
        token = login_user("unknown_user", "any_password", self.auth_manager)
        self.assertIsNone(token)

class TestAuthMiddleware(unittest.TestCase):
    """Test cases for authentication middleware."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.auth_manager = AuthManager("test_secret_key")
        self.middleware = AuthMiddleware(self.auth_manager)
    
    def test_require_auth_decorator(self):
        """Test the require_auth decorator."""
        @self.middleware.require_auth
        def protected_function(message, current_user=None):
            return f"Hello {current_user['user_id']}: {message}"
        
        # Mock token extraction and verification
        with patch.object(self.middleware, '_extract_token_from_request', return_value="valid_token"):
            with patch.object(self.auth_manager, 'verify_token', return_value={'user_id': 'test_user'}):
                result = protected_function("test message")
                self.assertEqual(result, "Hello test_user: test message")
    
    def test_require_auth_missing_token(self):
        """Test require_auth with missing token."""
        @self.middleware.require_auth
        def protected_function():
            return "Should not reach here"
        
        with patch.object(self.middleware, '_extract_token_from_request', return_value=None):
            result, status_code = protected_function()
            self.assertEqual(status_code, 401)
            self.assertIn('Missing authentication token', result['error'])

if __name__ == '__main__':
    unittest.main() 
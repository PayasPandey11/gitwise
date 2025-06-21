"""Middleware for handling authentication in web requests."""

from functools import wraps
from typing import Callable, Any
from test_auth import AuthManager

class AuthMiddleware:
    """Middleware for protecting routes with authentication."""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
    
    def require_auth(self, f: Callable) -> Callable:
        """Decorator to require authentication for a route."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract token from request headers
            token = self._extract_token_from_request()
            
            if not token:
                return {'error': 'Missing authentication token'}, 401
            
            payload = self.auth_manager.verify_token(token)
            if not payload:
                return {'error': 'Invalid or expired token'}, 401
            
            # Add user info to kwargs
            kwargs['current_user'] = payload
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_role(self, required_role: str):
        """Decorator to require specific role for access."""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Check if user has required role
                current_user = kwargs.get('current_user', {})
                user_role = current_user.get('role', 'user')
                
                if user_role != required_role and required_role != 'user':
                    return {'error': 'Insufficient permissions'}, 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    def _extract_token_from_request(self) -> str:
        """Extract JWT token from request headers."""
        # Mock implementation - in real app would get from request object
        # return request.headers.get('Authorization', '').replace('Bearer ', '')
        return "mock_token_for_testing"

def protected_route(auth_middleware: AuthMiddleware):
    """Example of a protected route using the middleware."""
    @auth_middleware.require_auth
    def get_user_profile(user_id: str, current_user: dict = None):
        """Get user profile - requires authentication."""
        return {
            'user_id': user_id,
            'profile': f"Profile for {current_user['email']}"
        }
    
    return get_user_profile

def admin_route(auth_middleware: AuthMiddleware):
    """Example of an admin-only route."""
    @auth_middleware.require_auth
    @auth_middleware.require_role('admin')
    def admin_dashboard(current_user: dict = None):
        """Admin dashboard - requires admin role."""
        return {
            'message': 'Welcome to admin dashboard',
            'admin_user': current_user['email']
        }
    
    return admin_dashboard 
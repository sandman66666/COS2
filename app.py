# app.py
"""
Strategic Intelligence System - Main Application
===============================================
Multi-tenant Strategic Intelligence System with Gmail integration,
contact analysis, and intelligence generation.
"""

import os
import asyncio
from datetime import timedelta
from dotenv import load_dotenv

from flask import Flask, session, g, render_template, send_from_directory, jsonify, request, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from api.auth_routes import auth_bp
from api.routes import api_bp
from api.alerts_routes_flask import alerts_bp
# from routes.contacts import contacts_bp  # Removed - module doesn't exist
from middleware.auth_middleware import get_current_user, require_auth
from storage.storage_manager import initialize_storage_manager
from utils.logging import structured_logger as logger

# Load environment variables
load_dotenv()

def create_app(config=None):
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Basic configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev_secret_key'),
        PERMANENT_SESSION_LIFETIME=timedelta(days=1),
        SESSION_COOKIE_SECURE=os.getenv('ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        TEMPLATES_AUTO_RELOAD=True
    )
    
    # Override config if provided
    if config:
        app.config.update(config)
    
    # Setup rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(alerts_bp)
    
    # Dashboard route - requires authentication
    @app.route('/dashboard')
    @require_auth
    def dashboard():
        """Serve the dashboard - requires Google OAuth authentication"""
        user = get_current_user()
        logger.info(f"🏠 Dashboard access attempt by user: {user}")
        
        if not user or not user.get('authenticated'):
            # Redirect to login for real OAuth authentication
            logger.warning("🚫 Dashboard access denied - redirecting to login")
            return redirect('/login')
        
        logger.info(f"✅ Dashboard access granted to {user.get('email')}")
        return send_from_directory('static', 'dashboard.html')
    
    # Login route - serves login page
    @app.route('/login')
    def login_page():
        """Serve the login page or redirect to dashboard if already authenticated"""
        # Check if user is already authenticated
        user = get_current_user()
        
        if user and user.get('authenticated'):
            logger.info(f"🔄 User {user.get('email')} already authenticated, redirecting to dashboard")
            return redirect('/dashboard')
        
        logger.info("🔑 Login page requested - user not authenticated")
        return send_from_directory('static', 'login.html')
    
    # Root route redirects to dashboard
    @app.route('/')
    @require_auth
    def index():
        """Serve dashboard if authenticated, otherwise login"""
        user = get_current_user()
        logger.info(f"🏠 Root access attempt by user: {user}")
        
        if not user or not user.get('authenticated'):
            logger.warning("🚫 Root access denied - redirecting to login")
            return redirect('/login')
        
        logger.info(f"✅ Root access granted to {user.get('email')}")
        return send_from_directory('static', 'dashboard.html')
    
    # Debug route to check session status
    @app.route('/debug/auth')
    def debug_auth():
        """Debug authentication status"""
        if os.getenv('ENV') == 'production':
            return jsonify({'error': 'Debug not available in production'}), 403
        
        user = get_current_user()
        return jsonify({
            'authenticated': bool(user and user.get('authenticated')),
            'user': user,
            'session': dict(session),
            'session_keys': list(session.keys())
        })
    
    # Test route to manually set authentication (DEVELOPMENT ONLY)
    @app.route('/debug/set-auth')
    def set_test_auth():
        """Set test authentication for development"""
        if os.getenv('ENV') == 'production':
            return jsonify({'error': 'Not available in production'}), 403
        
        # Use the user's actual email for test authentication
        user_email = 'Sandman@session-42.com'
        
        # Set test session data with real user email
        session['user_id'] = user_email
        session['user_email'] = user_email
        session['authenticated'] = True
        session['session_id'] = 'sandman_session_123'
        session['oauth_credentials'] = {
            'access_token': 'test_access_token_for_development_only',
            'refresh_token': 'test_refresh_token',
            'scopes': ['email', 'profile', 'gmail']
        }
        session.permanent = True
        
        logger.info(f"🧪 Test authentication set for development user: {user_email}")
        return jsonify({
            'success': True,
            'message': 'Test authentication set',
            'user_email': user_email,
            'redirect_to': '/dashboard'
        })
    
    # Health check route - NO AUTH REQUIRED
    @app.route('/api/health')
    def simple_health():
        """Simple health check - No auth required"""
        return jsonify({
            'status': 'healthy',
            'service': 'strategic_intelligence_api',
            'mode': 'development',
            'dashboard_url': '/dashboard'
        })
    
    # Initialize storage manager when the app context is available
    storage_initialized = False
    
    @app.before_request
    def initialize_app():
        """Initialize app components on first request"""
        nonlocal storage_initialized
        if not storage_initialized:
            logger.info("Initializing application components")
            storage_initialized = True
            # Initialize storage in background (non-blocking)
            try:
                asyncio.run(initialize_storage_manager())
            except Exception as e:
                logger.error(f"Storage initialization failed: {e}")
        
    # Set current user for each request (optional for dashboard)
    @app.before_request
    def set_current_user():
        """Set current user for request context"""
        try:
            g.user = get_current_user()
        except Exception as e:
            logger.warning(f"Failed to get current user: {e}")
            g.user = None
        
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({'error': 'Page not found'}), 404
        
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
        
    # Enable CORS for development
    if os.getenv('ENV') != 'production':
        @app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response
    
    logger.info(f"Application created in {os.getenv('ENV', 'development')} mode")
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment - use 8080 as default for Google Cloud Console
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 8080))  # Changed default to 8080
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    print("\n🚀 Strategic Intelligence System")
    print("=" * 50)
    print(f"📊 Dashboard: http://localhost:{port}/dashboard")
    print(f"🔍 Health Check: http://localhost:{port}/api/health")
    print(f"🌐 Google Cloud Console port: {port}")
    print("🔓 Dashboard accessible for testing")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=debug)

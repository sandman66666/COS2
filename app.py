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
    
    # Dashboard route - requires authentication
    @app.route('/dashboard')
    @require_auth
    def dashboard():
        """Serve the dashboard - requires Google OAuth authentication"""
        user = get_current_user()
        if not user or not user.get('authenticated'):
            # Redirect to login for real OAuth authentication
            return redirect(url_for('auth.login'))
        
        return send_from_directory('static', 'dashboard.html')
    
    # Root route redirects to dashboard
    @app.route('/')
    @require_auth
    def index():
        """Serve dashboard if authenticated, otherwise login"""
        user = get_current_user()
        if not user or not user.get('authenticated'):
            return redirect(url_for('auth.login'))
        
        return send_from_directory('static', 'dashboard.html')
    
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

# app.py
"""
Strategic Intelligence System - Main Application
===============================================
Multi-tenant Strategic Intelligence System with Gmail integration,
contact analysis, and intelligence generation.
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, request, session, render_template, jsonify, send_from_directory
from flask_cors import CORS
import sys
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.auth_routes import auth_bp
from api.routes_sync import api_sync_bp
from api.logging_routes_sync import logging_bp
from api.intelligence_routes_with_logging import intelligence_logging_bp
# from api.alerts_routes_flask import alerts_bp  # Temporarily disabled - uses async routes
# from routes.contacts import contacts_bp  # Removed - module doesn't exist
from middleware.auth_middleware import get_current_user, require_auth
from storage.storage_manager_sync import initialize_storage_manager_sync
from utils.logging import structured_logger as logger
from config.settings import API_SECRET_KEY, API_DEBUG, API_HOST, API_PORT, IS_HEROKU, FORCE_DOMAIN

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    
    # Configure Flask
    app.secret_key = API_SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = not API_DEBUG  # Secure cookies in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # Enable CORS for development
    CORS(app, supports_credentials=True, origins=['http://localhost:8080', 'http://127.0.0.1:8080'])
    
    # Setup logging with the custom StructuredLogger 
    # (Note: StructuredLogger doesn't have handlers like standard Python logging)
    app.logger.setLevel(logging.INFO)
    
    # Initialize sync storage manager (no async/await needed)
    try:
        storage_status = initialize_storage_manager_sync()
        logger.info("Storage manager initialized (synchronous)", status=storage_status)
    except Exception as e:
        logger.error(f"Failed to initialize storage manager: {e}")
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_sync_bp)  # Use sync API routes
    app.register_blueprint(logging_bp)  # Add logging analysis routes
    app.register_blueprint(intelligence_logging_bp)  # Add intelligence logging routes
    
    # Domain redirect middleware for OAuth consistency
    @app.before_request
    def force_domain_redirect():
        """Redirect short domain to full domain to maintain OAuth session consistency"""
        if FORCE_DOMAIN and request.host != FORCE_DOMAIN:
            # Only redirect if coming from a different domain
            if request.url.startswith('http://'):
                new_url = request.url.replace('http://', 'https://').replace(request.host, FORCE_DOMAIN)
            else:
                new_url = request.url.replace(request.host, FORCE_DOMAIN)
            
            logger.info("Redirecting for domain consistency", 
                       from_host=request.host, to_host=FORCE_DOMAIN, url=new_url)
            
            from flask import redirect
            return redirect(new_url, 301)
    
    # Main dashboard route
    @app.route('/')
    def index():
        """Serve the main dashboard"""
        return render_template('dashboard_new.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard route that serves the main dashboard"""
        return render_template('dashboard_new.html')
    
    @app.route('/react')
    def react_dashboard():
        """Serve the React dashboard"""
        return send_from_directory('static/react', 'index.html')
    
    @app.route('/login')
    def login_page():
        """Serve login page"""
        return render_template('login.html')
    
    @app.route('/knowledge-tree')
    def knowledge_tree():
        """Serve knowledge tree visualization page"""
        return render_template('knowledge_tree.html')
    
    @app.route('/health')
    def health_check():
        """Basic health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'mode': 'synchronous'
        })
    
    # Request logging middleware
    @app.before_request
    def log_request():
        """Log incoming requests"""
        if request.endpoint not in ['static', 'health_check']:
            logger.info(
                "Incoming request",
                method=request.method,
                endpoint=request.endpoint,
                path=request.path,
                user_agent=request.headers.get('User-Agent', ''),
                remote_addr=request.remote_addr
            )
    
    # Response logging middleware
    @app.after_request
    def log_response(response):
        """Log outgoing responses"""
        if request.endpoint not in ['static', 'health_check']:
            logger.info(
                "Outgoing response",
                status_code=response.status_code,
                endpoint=request.endpoint,
                path=request.path
            )
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    # Development server
    logger.info("Starting Strategic Intelligence System (Synchronous Mode)")
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('API_PORT', 8080)),
        debug=os.getenv('ENVIRONMENT') != 'production'
    )

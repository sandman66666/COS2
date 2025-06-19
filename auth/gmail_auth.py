# auth/gmail_auth.py
"""
Gmail OAuth Authentication Manager
=================================
Handles Google OAuth flow for Gmail access, manages credentials, and provides
user authentication functionality for the Strategic Intelligence System.
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any

import requests
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

from config.settings import (
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET, 
    GOOGLE_REDIRECT_URI
)
from utils.logging import structured_logger as logger
from models.user import User, UserCreate

class GmailAuthManager:
    """Gmail OAuth authentication manager for multi-tenant systems"""
    
    def __init__(self):
        """Initialize with Google OAuth configuration"""
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        
        # OAuth scopes for Gmail and user data
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',  # Read Gmail messages
            'https://www.googleapis.com/auth/gmail.send',      # Send emails
            'https://www.googleapis.com/auth/userinfo.email',  # Get user email
            'https://www.googleapis.com/auth/userinfo.profile', # Get user profile
            'https://www.googleapis.com/auth/calendar.readonly', # Calendar access (Google adds this)
            'openid'                                           # OpenID Connect
        ]
    
    def get_authorization_url(self, user_id: str = None, state: str = None) -> Tuple[str, str]:
        """
        Generate Google OAuth authorization URL
        
        Args:
            user_id: Optional user identifier to associate with the flow
            state: Optional state parameter to protect against CSRF
            
        Returns:
            Tuple of (authorization URL, state parameter)
        """
        try:
            # Create OAuth flow with Google client config
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [self.redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=self.scopes
            )
            
            flow.redirect_uri = self.redirect_uri
            
            # Generate authorization URL with offline access for refresh tokens
            auth_url, state = flow.authorization_url(
                access_type='offline',         # Enable refresh tokens
                include_granted_scopes='true', # Include previously granted scopes
                prompt='consent',              # Always show consent screen for multi-tenant security
                state=state or f"cos_{int(time.time())}"  # State parameter for CSRF protection
            )
            
            logger.info("Generated OAuth authorization URL", state=state)
            return auth_url, state
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise
    
    def handle_oauth_callback(self, authorization_code: str, state: str = None) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange code for tokens
        
        Args:
            authorization_code: The code received from Google OAuth redirect
            state: Optional state parameter to validate
            
        Returns:
            Dict with success status, user info, and credentials
        """
        try:
            # Create OAuth flow with the exact same configuration as authorization
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uris": [self.redirect_uri],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                scopes=self.scopes  # Use our original scopes
            )
            
            flow.redirect_uri = self.redirect_uri
            
            # The key fix: Use the exact redirect URI that was used in authorization
            # This prevents redirect_uri_mismatch errors
            
            try:
                # Exchange authorization code for tokens
                flow.fetch_token(code=authorization_code)
                credentials = flow.credentials
                
            except Exception as token_error:
                logger.error(f"Initial token exchange failed: {str(token_error)}")
                
                # If the Google library fails due to scope changes, do direct token exchange
                # This handles cases where Google adds additional scopes like calendar
                token_data = {
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'code': authorization_code,
                    'grant_type': 'authorization_code',
                    'redirect_uri': self.redirect_uri
                }
                
                response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
                
                if response.status_code != 200:
                    error_details = response.text
                    logger.error(f"Direct token exchange failed: {error_details}")
                    raise Exception(f"Token exchange failed: {error_details}")
                
                token_response = response.json()
                
                # Create credentials from direct response
                credentials = Credentials(
                    token=token_response.get('access_token'),
                    refresh_token=token_response.get('refresh_token'),
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=token_response.get('scope', '').split() if token_response.get('scope') else self.scopes
                )
                
                # Set expiry if available
                if token_response.get('expires_in'):
                    credentials.expiry = datetime.utcnow() + timedelta(seconds=int(token_response['expires_in']))
            
            # Get user profile information
            user_info = self._get_user_info(credentials.token)
            
            if not user_info:
                return {
                    'success': False,
                    'error': 'Failed to retrieve user information'
                }
            
            # Log successful authentication
            email = user_info.get('email')
            logger.info(f"✅ OAuth successful for user", email=email)
            
            # Calculate token expiry timestamp
            expiry_time = None
            if credentials.expiry:
                expiry_time = credentials.expiry.timestamp()
            
            return {
                'success': True,
                'user_info': {
                    'email': email,
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'google_id': user_info.get('id'),
                    'locale': user_info.get('locale')
                },
                'credentials': {
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'expiry': expiry_time,
                    'token_uri': credentials.token_uri,
                    'scopes': credentials.scopes or []
                }
            }
                
        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile information using access token
        
        Args:
            access_token: Valid Google access token
            
        Returns:
            Dict with user profile information or None if failed
        """
        try:
            # Make request to Google's userinfo endpoint
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user info: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
    async def get_valid_credentials(self, user_id: int, storage_manager) -> Optional[Credentials]:
        """
        Get valid credentials for a user, refreshing if necessary
        
        Args:
            user_id: ID of the user
            storage_manager: Storage manager instance for DB access
            
        Returns:
            Valid Credentials object or None
        """
        try:
            # Try to get credentials from cache first
            cached_creds = storage_manager.cache.get_value(f"oauth_creds:{user_id}")
            if cached_creds:
                credentials = Credentials(
                    token=cached_creds['access_token'],
                    refresh_token=cached_creds['refresh_token'],
                    token_uri=cached_creds.get('token_uri', "https://oauth2.googleapis.com/token"),
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=cached_creds.get('scopes', self.scopes)
                )
                
                # Set expiry if available
                if cached_creds.get('expiry'):
                    credentials.expiry = datetime.fromtimestamp(cached_creds['expiry'])
                
                # If not expired, return credentials
                if not credentials.expired:
                    return credentials
            
            # If no valid cached credentials, get from database
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                creds_row = await conn.fetchrow("""
                    SELECT access_token, refresh_token, token_expiry, token_uri, scopes
                    FROM oauth_credentials 
                    WHERE user_id = $1 AND provider = 'google'
                """, user_id)
                
                if not creds_row or not creds_row['access_token']:
                    logger.warning(f"No stored credentials for user ID: {user_id}")
                    return None
                
                # Create credentials object
                credentials = Credentials(
                    token=creds_row['access_token'],
                    refresh_token=creds_row['refresh_token'],
                    token_uri=creds_row.get('token_uri') or "https://oauth2.googleapis.com/token",
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scopes=creds_row.get('scopes') or self.scopes
                )
                
                # Set expiry if available
                if creds_row.get('token_expiry'):
                    credentials.expiry = creds_row['token_expiry']
            
            # Check if credentials are expired and refresh if possible
            if credentials.expired and credentials.refresh_token:
                logger.info(f"Refreshing expired credentials for user ID: {user_id}")
                credentials.refresh(Request())
                
                # Update stored credentials in database
                await self._save_refreshed_credentials(user_id, credentials, storage_manager)
                
            elif credentials.expired:
                logger.warning(f"Credentials expired and no refresh token for user ID: {user_id}")
                return None
            
            # Cache the valid credentials
            storage_manager.cache.set_value(
                f"oauth_creds:{user_id}", 
                {
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'expiry': credentials.expiry.timestamp() if credentials.expiry else None,
                    'token_uri': credentials.token_uri,
                    'scopes': credentials.scopes
                },
                3600  # Cache for 1 hour
            )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get valid credentials for user ID {user_id}: {str(e)}")
            return None
    
    async def _save_refreshed_credentials(self, user_id: int, credentials: Credentials, storage_manager):
        """Save refreshed credentials to database"""
        try:
            async with storage_manager.postgres.conn_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE oauth_credentials
                    SET access_token = $1, 
                        refresh_token = $2,
                        token_expiry = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $4 AND provider = 'google'
                """, 
                credentials.token,
                credentials.refresh_token,
                credentials.expiry,
                user_id
                )
        except Exception as e:
            logger.error(f"Error saving refreshed credentials: {str(e)}")

# Global instance
gmail_auth = GmailAuthManager()

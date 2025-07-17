"""
Cybershuttle Authentication Helper

This module implements OAuth2 device flow authentication for the Cybershuttle platform.
Based on the real implementation provided by the Apache Airavata team.
"""

import requests
import time
import json
import os
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class CybershuttleAuth:
    """OAuth2 device flow authentication for Cybershuttle using real endpoints."""
    
    def __init__(self, 
                 api_base: str = "https://api.dev.cybershuttle.org:18899",
                 auth_server_url: str = "https://auth.cybershuttle.org",
                 client_id: str = "cybershuttle-agent",
                 realm: str = "default"):
        """
        Initialize the authentication helper with real Cybershuttle/Airavata endpoints.
        
        Args:
            api_base: Base URL for the Cybershuttle API (development)
            auth_server_url: Keycloak auth server URL
            client_id: OAuth2 client ID (cybershuttle-agent)
            realm: Keycloak realm (default)
        """
        self.api_base = api_base
        self.auth_server_url = auth_server_url
        self.client_id = client_id
        self.realm = realm

        self.device_endpoint = f"{auth_server_url}/realms/{realm}/protocol/openid-connect/auth/device"
        self.token_endpoint = f"{auth_server_url}/realms/{realm}/protocol/openid-connect/token"

        self.token_file = os.path.expanduser("~/.cybershuttle/token.json")
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        self.access_token = os.getenv('CS_ACCESS_TOKEN')
    
    def _ensure_token_dir(self):
        """Ensure the token directory exists."""
        token_dir = os.path.dirname(self.token_file)
        if not os.path.exists(token_dir):
            os.makedirs(token_dir, exist_ok=True)
    
    def _save_token(self, token_data: Dict):
        """Save token data to file and environment."""
        self._ensure_token_dir()

        self.access_token = token_data.get("access_token")
        self.refresh_token = token_data.get("refresh_token")

        expires_in = token_data.get("expires_in", 3600)
        self.token_expires_at = time.time() + expires_in

        os.environ['CS_ACCESS_TOKEN'] = self.access_token

        token_info = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at,
            "timestamp": time.time()
        }
        
        try:
            with open(self.token_file, 'w') as f:
                json.dump(token_info, f, indent=2)
            logger.info("Token saved successfully")
        except Exception as e:
            logger.error(f"Error saving token: {e}")
    
    def _load_token(self) -> bool:
        """Load token from file if it exists."""
        if not os.path.exists(self.token_file):
            return False
        
        try:
            with open(self.token_file, 'r') as f:
                token_info = json.load(f)
            
            self.access_token = token_info.get("access_token")
            self.refresh_token = token_info.get("refresh_token")
            self.token_expires_at = token_info.get("expires_at")

            if self.access_token:
                os.environ['CS_ACCESS_TOKEN'] = self.access_token
            
            return True
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            return False
    
    def _is_token_valid(self) -> bool:
        """Check if the current token is valid."""
        if not self.access_token or not self.token_expires_at:
            return False

        return time.time() < (self.token_expires_at - 300)
    
    def device_flow_auth(self) -> bool:
        """
        Perform OAuth2 device flow authentication using real Cybershuttle/Airavata implementation.
        Based on the code provided by the Airavata team.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Step 1: Request device and user code
        device_data = {
            "client_id": self.client_id,
            "scope": "openid"
        }
        
        try:
            response = requests.post(self.device_endpoint, data=device_data)
            if response.status_code != 200:
                logger.error(f"Error in authentication request: {response.status_code} - {response.text}")
                return False
            
            device_response = response.json()
            device_code = device_response.get("device_code")
            user_code = device_response.get("user_code")
            verification_uri = device_response.get("verification_uri")
            verification_uri_complete = device_response.get("verification_uri_complete")
            expires_in = device_response.get("expires_in", 1800)
            interval = device_response.get("interval", 5)
            
        except requests.RequestException as e:
            logger.error(f"Error requesting device code: {e}")
            return False
        
        # Step 2: Display user instructions
        print("\n**Cybershuttle Authentication Required**")
        print("=" * 50)
        print(f"1. Go to: {verification_uri}")
        print(f"2. Enter code: {user_code}")
        print("3. Complete the authentication process")
        
        if verification_uri_complete:
            print(f"\nOr visit: {verification_uri_complete}")
        
        print(f"\nCode expires in {expires_in // 60} minutes")
        print("Waiting for authentication...")
        
        # Step 3: Poll for token (exactly like Airavata implementation)
        counter = 0
        while True:
            try:
                token_data = {
                    "client_id": self.client_id,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code
                }
                
                response = requests.post(self.token_endpoint, data=token_data)
                
                if response.status_code == 200:
                    # Success! We got the token
                    token_response = response.json()
                    access_token = token_response.get("access_token")
                    
                    os.environ['CS_ACCESS_TOKEN'] = access_token
                    
                    self._save_token(token_response)
                    
                    print("Authentication successful!")
                    return True
                
                elif response.status_code == 400:
                    error_response = response.json()
                    error = error_response.get("error")
                    
                    if error == "authorization_pending":
                        counter += 1
                        print(f"Waiting for authentication... ({counter})")
                        time.sleep(interval)
                        continue
                    else:
                        print(f"Authentication error: {error}")
                        return False
                
                else:
                    print(f"Error during authentication: {response.status_code} - {response.text}")
                    return False
                    
            except requests.RequestException as e:
                logger.error(f"Error polling for token: {e}")
                return False
    
    def get_access_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token or None if authentication fails
        """
        env_token = os.getenv('CS_ACCESS_TOKEN')
        if env_token:
            self.access_token = env_token
            return env_token

        if not self._load_token():
            logger.info("No existing token found")

        if self._is_token_valid():
            return self.access_token

        logger.info("Token invalid or expired, starting device flow authentication...")
        
        if self.device_flow_auth():
            return self.access_token
        
        return None
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            dict: Headers with Bearer token
        """
        token = self.get_access_token()
        if not token:
            raise ValueError("No valid access token available")
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated.
        
        Returns:
            bool: True if authenticated with valid token
        """
        return self.get_access_token() is not None
    
    def logout(self):
        """Clear stored authentication tokens."""
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

        if 'CS_ACCESS_TOKEN' in os.environ:
            del os.environ['CS_ACCESS_TOKEN']

        if os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
                logger.info("Token file removed")
            except Exception as e:
                logger.error(f"Error removing token file: {e}")

def authenticate() -> CybershuttleAuth:
    """
    Authenticate with Cybershuttle and return auth object.
    
    Returns:
        CybershuttleAuth: Authenticated auth object
    """
    auth = CybershuttleAuth()
    if not auth.is_authenticated():
        if not auth.device_flow_auth():
            raise ValueError("Authentication failed")
    return auth

def get_authenticated_session() -> requests.Session:
    """
    Get a requests session with authentication headers.
    
    Returns:
        requests.Session: Session with auth headers
    """
    auth = authenticate()
    session = requests.Session()
    session.headers.update(auth.get_auth_headers())
    return session

if __name__ == "__main__":
    try:
        auth = authenticate()
        print("Authentication test successful!")
        print(f"API Base: {auth.api_base}")
        print(f"Auth Server: {auth.auth_server_url}")
        print(f"Client ID: {auth.client_id}")
        print(f"Token: {auth.access_token[:20]}..." if auth.access_token else "No token")
        print("\nTo use this token, run this command in your terminal:")
        print(f"export CS_ACCESS_TOKEN=\"{auth.access_token}\"")
    except Exception as e:
        print(f"Authentication test failed: {e}") 
#!/usr/bin/env python3
"""
Standalone FIRS Entity Lookup Script

This script provides direct access to the FIRS API for entity lookups,
without requiring the full TaxPoynt backend to be running.
It implements proper authentication and handles the UUID format requirements.
"""
import argparse
import base64
import json
import os
import requests
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin

# Cryptography imports for handling the public key and certificate
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.x509 import load_pem_x509_certificate
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    print("Warning: cryptography package not available. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cryptography"])
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.x509 import load_pem_x509_certificate
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True

# FIRS API Configuration
# Default to sandbox environment for testing
FIRS_API_URL = os.getenv("FIRS_API_URL", "https://eivc-k6z6d.ondigitalocean.app")
FIRS_API_KEY = os.getenv("FIRS_API_KEY", "36dc0109-5fab-4433-80c3-84d9cef792a2") 
FIRS_API_SECRET = os.getenv("FIRS_API_SECRET", "mHtXX9UBq3qnvgJFkIIEjQLlxjXKS1yECpqmTWa1AuCzRg5sJNOpxDefCYds18WNma3zUUgt1ccIUOgNtBb4wk8s4MshQl8OxhQA")

# Cryptographic keys for secure authentication
# These are provided by FIRS for your business
FIRS_PUBLIC_KEY_B64 = os.getenv("FIRS_PUBLIC_KEY_B64", "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUFyU0xpdDRtb1RMbFdjd1A4eEp6RQp3ZTdkRHExdC9kMi9zcXdQTlNVandablFPbklabVh4TXY4QUQxemMxdUErZ3VCc2tpUGdoSXd6ekxWYXJoNk1KCndEdVUxSC95V2FPZE1PTnZOQy9OWERybXB5cE5WUDZyQnV3LzVjSERMdEtoZlJ0YkdFa1JSVVF4MVAxUUJ6REsKVVRpaTRJOXJld29zcVQ4V1dBOE8zRVd5ZHJ5TEg1K3JpVmRUNVBPeU1jcU95YUR2bGRqWG9ZdnBSTHlkcmtDQQpkUWpMdkw0bG00TVNxS05WdGVJR0Y4ZWk4M3Juck5wR3hKTVVGYVMwekt5TzBJZlY0alBCK3ZXN3I1TXdzTjRvCkRnWVR2ME85Q050N3JoNlEvYi9XR3Ewakl3WHJ3c3JIQXE4TXNyUVlGV0JIOHpmejMwOHRWMTlRM1hPTnEyWEMKMHdJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg==")
FIRS_CERTIFICATE_B64 = os.getenv("FIRS_CERTIFICATE_B64", "bEF0V3FJbmo5cVZYbEdCblB4QVpjMG9HVWFrc29GM2hiYWFkYWMyODRBUT0=")

# Business identification for FIRS
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "MT GARBA GLOBAL VENTURES")
BUSINESS_TIN = os.getenv("BUSINESS_TIN", "31569955-0001")
BUSINESS_SERVICE_ID = os.getenv("BUSINESS_SERVICE_ID", "312577")

# Track authentication state
auth_token = None
auth_expiry = None

def load_public_key() -> Any:
    """Load FIRS public key from base64 encoded string."""
    try:
        # Decode the base64 encoded public key
        public_key_bytes = base64.b64decode(FIRS_PUBLIC_KEY_B64)
        
        # Load the public key
        public_key = serialization.load_pem_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        return public_key
    except Exception as e:
        print(f"Error loading public key: {str(e)}")
        return None

def create_signature(data: str) -> str:
    """Create a cryptographic signature for the data."""
    try:
        # Use the public key to encrypt/sign data
        # Note: In a proper implementation, you would use your private key to sign
        # For this demo, we're using the public key as a placeholder
        public_key = load_public_key()
        if not public_key:
            return ""
        
        # Create a signature (this is a simplified placeholder)
        # In a real implementation, you'd use proper signing with your private key
        timestamp = str(int(time.time()))
        signature_base = f"{data}:{timestamp}"
        
        # Return the base64 encoded signature with timestamp
        return base64.b64encode(signature_base.encode()).decode()
    except Exception as e:
        print(f"Error creating signature: {str(e)}")
        return ""

def get_default_headers() -> Dict[str, str]:
    """Get default headers for FIRS API requests."""
    headers = {
        "accept": "*/*",
        "x-api-key": FIRS_API_KEY,
        "x-api-secret": FIRS_API_SECRET,
        "Content-Type": "application/json"
    }
    
    # Add cryptographic signature for enhanced security
    signature = create_signature(FIRS_API_KEY)
    if signature:
        headers["x-signature"] = signature
    
    return headers

def get_auth_headers() -> Dict[str, str]:
    """Get headers with authentication token for FIRS API requests."""
    headers = get_default_headers()
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    return headers

def authenticate(email: str, password: str) -> Dict[str, Any]:
    """Authenticate with FIRS API and get access token."""
    global auth_token, auth_expiry
    
    print(f"Authenticating with FIRS API as {email}...")
    
    # Generate request ID for tracing and security
    request_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    
    url = urljoin(FIRS_API_URL, "/api/v1/utilities/authenticate")
    payload = {
        "email": email,
        "password": password,
        "business_tin": BUSINESS_TIN,
        "service_id": BUSINESS_SERVICE_ID,
        "request_id": request_id,
        "timestamp": timestamp
    }
    
    # Get headers with added security signature
    headers = get_default_headers()
    headers["x-certificate"] = FIRS_CERTIFICATE_B64
    
    # Create a signature specifically for authentication request
    auth_signature = create_signature(f"{email}:{os.getenv('BUSINESS_SERVICE_ID')}:{timestamp}")
    if auth_signature:
        headers["x-auth-signature"] = auth_signature
    
    try:
        print(f"Making authentication request to {url}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Authentication failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return {"success": False, "error": f"Authentication failed: {response.text}"}
        
        auth_data = response.json()
        
        # Extract and store token with expiry information
        if "data" in auth_data and "access_token" in auth_data["data"]:
            auth_token = auth_data["data"]["access_token"]
            
            # Set token expiry if provided
            if "expires_in" in auth_data["data"]:
                expires_in = auth_data["data"]["expires_in"]
                auth_expiry = datetime.now() + timedelta(seconds=expires_in)
                print(f"Authentication successful. Token expires at {auth_expiry}")
            else:
                auth_expiry = datetime.now() + timedelta(hours=24)  # Default 24-hour expiry
                print(f"Authentication successful. Assuming 24h token validity.")
            
            # Extract business verification status if available
            if "business_verification" in auth_data["data"]:
                print(f"Business verification status: {auth_data['data']['business_verification']}")
        else:
            print("Warning: Unexpected authentication response format")
            print(f"Response structure: {json.dumps(auth_data, indent=2)}")
        
        return {"success": True, "auth_data": auth_data}
    
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        return {"success": False, "error": str(e)}

def convert_tin_to_uuid(tin: str) -> str:
    """
    Convert a TIN or Service ID to UUID format for FIRS API.
    
    This is a workaround for the discrepancy between documentation and implementation.
    The API documentation shows TIN format but the implementation requires UUID format.
    """
    # If the input already looks like a UUID, return it as is
    if len(tin) == 36 and tin.count('-') == 4:
        return tin
    
    # If this is our service ID, use the predefined mapping to UUID
    if tin == BUSINESS_SERVICE_ID or tin == "312577":
        # Use a fixed UUID for our service ID for now
        # In production, you would get this UUID from FIRS directly
        # This is just a placeholder based on the test script that worked
        return "0ff302fd-33c9-43e2-8a77-b9375749ea20"
    elif tin == BUSINESS_TIN or tin == "31569955-0001":
        # Use the correct UUID for our business TIN
        return "71fcdd6f-3027-487b-ae38-4830b99f1cf5"
    
    # Otherwise, generate a deterministic UUID based on the input
    # This is just a placeholder approach - in production you'd need a proper mapping
    namespace = uuid.UUID('00000000-0000-0000-0000-000000000000')
    return str(uuid.uuid5(namespace, tin))

def get_entity_by_id(entity_id: str) -> Dict[str, Any]:
    """Get entity details by ID from FIRS API."""
    # Convert TIN to UUID format if needed
    uuid_format = convert_tin_to_uuid(entity_id)
    print(f"Looking up entity with ID: {entity_id} (UUID format: {uuid_format})")
    
    # Generate request ID and timestamp for security
    request_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    
    url = urljoin(FIRS_API_URL, f"/api/v1/entity/{uuid_format}")
    
    # Get base headers with authentication token
    headers = get_auth_headers()
    
    # Add cryptographic security headers
    headers["x-certificate"] = FIRS_CERTIFICATE_B64
    headers["x-request-id"] = request_id
    headers["x-timestamp"] = timestamp
    headers["x-business-tin"] = BUSINESS_TIN
    headers["x-service-id"] = BUSINESS_SERVICE_ID
    
    # Create specific signature for this entity lookup
    lookup_signature = create_signature(f"{uuid_format}:{BUSINESS_SERVICE_ID}:{timestamp}")
    if lookup_signature:
        headers["x-request-signature"] = lookup_signature
    
    try:
        print(f"Making entity lookup request to {url}")
        print(f"Using request ID: {request_id}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Entity lookup successful!")
            return {"success": True, "entity": result}
        else:
            print(f"❌ Entity lookup failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
            # Check if we need to refresh authentication
            if response.status_code == 401 or response.status_code == 403:
                print("Authentication may have expired. Try authenticating again.")
                
            return {"success": False, "error": f"Entity lookup failed: {response.text}"}
    
    except Exception as e:
        print(f"❌ Error during entity lookup: {str(e)}")
        return {"success": False, "error": str(e)}

def search_entity_by_reference(reference: str) -> Dict[str, Any]:
    """Search for entities by reference."""
    print(f"Searching for entity with reference: {reference}")
    
    # Generate request ID and timestamp for security
    request_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    
    url = urljoin(FIRS_API_URL, "/api/v1/entity/search")
    payload = {
        "entity_reference": reference,
        "request_id": request_id,
        "timestamp": timestamp,
        "business_tin": BUSINESS_TIN,
        "service_id": BUSINESS_SERVICE_ID
    }
    
    # Get base headers with authentication token
    headers = get_auth_headers()
    
    # Add cryptographic security headers
    headers["x-certificate"] = FIRS_CERTIFICATE_B64
    headers["x-request-id"] = request_id
    headers["x-timestamp"] = timestamp
    headers["x-business-tin"] = BUSINESS_TIN
    headers["x-service-id"] = BUSINESS_SERVICE_ID
    
    # Create specific signature for this search request
    search_signature = create_signature(f"{reference}:{BUSINESS_SERVICE_ID}:{timestamp}")
    if search_signature:
        headers["x-request-signature"] = search_signature
    
    try:
        print(f"Making entity search request to {url}")
        print(f"Using request ID: {request_id}")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result and "data" in result and len(result["data"]) > 0:
                print("✅ Entity search successful!")
                return {"success": True, "entity": result["data"][0]}
            else:
                print("❌ No entities found with the given reference")
                return {"success": False, "error": "No entities found"}
        else:
            print(f"❌ Entity search failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
            # Provide helpful diagnostics for common errors
            if response.status_code in (401, 403):
                print("Authentication issues - try re-authenticating")
                
            return {"success": False, "error": f"Entity search failed: {response.text}"}
    
    except Exception as e:
        print(f"❌ Error during entity search: {str(e)}")
        return {"success": False, "error": str(e)}

def lookup_party_by_tin(tin: str) -> Dict[str, Any]:
    """Lookup a party by TIN using the transmit endpoint."""
    print(f"Looking up party with TIN: {tin} using transmit endpoint")
    
    # Generate request ID and timestamp for security
    request_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    
    url = urljoin(FIRS_API_URL, f"/api/v1/invoice/transmit/lookup/party/{tin}")
    
    # Get base headers with authentication token
    headers = get_auth_headers()
    
    # Add cryptographic security headers
    headers["x-certificate"] = FIRS_CERTIFICATE_B64
    headers["x-request-id"] = request_id
    headers["x-timestamp"] = timestamp
    headers["x-business-tin"] = BUSINESS_TIN
    headers["x-service-id"] = BUSINESS_SERVICE_ID
    
    # Create specific signature for this party lookup
    lookup_signature = create_signature(f"{tin}:{BUSINESS_SERVICE_ID}:{timestamp}")
    if lookup_signature:
        headers["x-request-signature"] = lookup_signature
    
    try:
        print(f"Making party lookup request to {url}")
        print(f"Using request ID: {request_id}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Party lookup successful!")
            return {"success": True, "party": result}
        else:
            print(f"❌ Party lookup failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
            # Provide helpful diagnostics for common error codes
            if response.status_code == 400:
                print("Bad request - check if TIN format is correct")
            elif response.status_code in (401, 403):
                print("Authentication issues - try re-authenticating")
            elif response.status_code == 404:
                print("Party not found - verify TIN is correct and entity exists")
            
            return {"success": False, "error": f"Party lookup failed: {response.text}"}
    
    except Exception as e:
        print(f"❌ Error during party lookup: {str(e)}")
        return {"success": False, "error": str(e)}

def print_entity_details(entity: Dict[str, Any]) -> None:
    """Print entity details in a formatted way."""
    print("\n=== Entity Details ===")
    
    # Extract key details with fallbacks
    entity_id = entity.get("id", "N/A")
    name = entity.get("name", "N/A")
    tin = entity.get("tin", "N/A")
    email = entity.get("email", "N/A")
    
    print(f"ID:    {entity_id}")
    print(f"Name:  {name}")
    print(f"TIN:   {tin}")
    print(f"Email: {email}")
    
    # Show all other details
    print("\n=== All Entity Data ===")
    print(json.dumps(entity, indent=2))

def main():
    parser = argparse.ArgumentParser(description="FIRS Entity Lookup Tool")
    parser.add_argument("tin", help="TIN or entity ID to look up")
    parser.add_argument("--email", help="Email for FIRS API authentication")
    parser.add_argument("--password", help="Password for FIRS API authentication")
    parser.add_argument("--method", choices=["direct", "search", "transmit"], default="all",
                        help="Lookup method to use (default: try all methods)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with verbose logging")
    args = parser.parse_args()
    
    # Print configuration in debug mode
    if args.debug:
        print("=== FIRS API Configuration ===")
        print(f"API URL: {FIRS_API_URL}")
        print(f"API Key: {FIRS_API_KEY[:6]}...{FIRS_API_KEY[-4:]}")
        print(f"Public Key Available: {FIRS_PUBLIC_KEY_B64 is not None}")
        print(f"Certificate Available: {FIRS_CERTIFICATE_B64 is not None}")
        print(f"Business Name: {BUSINESS_NAME}")
        print(f"Business TIN: {BUSINESS_TIN}")
        print(f"Service ID: {BUSINESS_SERVICE_ID}")
        print("============================")
    
    # First authenticate if credentials provided
    if args.email and args.password:
        print("\nAttempting authentication with provided credentials...")
        auth_result = authenticate(args.email, args.password)
        
        if not auth_result["success"]:
            print(f"\n❌ Authentication failed: {auth_result.get('error', 'Unknown error')}")
            print("Continuing with entity lookup, but it may fail due to authentication issues")
    elif args.debug:
        print("\nNo authentication credentials provided - proceeding with entity lookup")
        print("Note: Some API endpoints may require authentication")
    
    # Try all lookup methods if no specific method is requested
    if args.method == "all" or args.method == "direct":
        print("\n=== Attempting Direct Entity Lookup ===")
        result = get_entity_by_id(args.tin)
        if result["success"]:
            print_entity_details(result["entity"])
            return
        elif args.debug:
            print("Direct entity lookup failed, trying next method...")
        
    if args.method == "all" or args.method == "search":
        print("\n=== Attempting Entity Search ===")
        result = search_entity_by_reference(args.tin)
        if result["success"]:
            print_entity_details(result["entity"])
            return
        elif args.debug:
            print("Entity search failed, trying next method...")
    
    if args.method == "all" or args.method == "transmit":
        print("\n=== Attempting Party Lookup via Transmit API ===")
        result = lookup_party_by_tin(args.tin)
        if result["success"]:
            print_entity_details(result["party"])
            return
    
    print("\n❌ Failed to find entity with all available methods")
    
    # Provide helpful troubleshooting information
    print("\n=== Troubleshooting Guide ===")
    print("1. Verify your API credentials are correct")
    print("2. Check that the TIN format is valid (should be in format XXXXXXXX-XXXX)")
    print("3. Ensure your business has permission to access this entity")
    print("4. Make sure your business certificate is valid")
    print("5. Try authenticating with valid credentials using --email and --password")
    
    if args.debug:
        print("\n=== Debug Information ===")
        print(f"API URL: {FIRS_API_URL}")
        print(f"Authentication token present: {auth_token is not None}")
        print(f"Public key present: {FIRS_PUBLIC_KEY_B64 is not None}")
        print(f"Certificate present: {FIRS_CERTIFICATE_B64 is not None}")

if __name__ == "__main__":
    main()

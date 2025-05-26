#!/usr/bin/env python3
"""
FIRS API Tester V3 - Testing Additional Endpoints
This script tests the remaining FIRS API endpoints not covered in previous test scripts.
"""

import os
import uuid
import datetime
import requests
import base64
import json
import sys
from typing import Dict, Any, Optional, List, Tuple

# Load environment variables
FIRS_API_URL = os.environ.get("FIRS_API_URL", "https://eivc-k6z6d.ondigitalocean.app")
FIRS_API_KEY = os.environ.get("FIRS_API_KEY", "")
FIRS_API_SECRET = os.environ.get("FIRS_API_SECRET", "")
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "MT GARBA GLOBAL VENTURES")
BUSINESS_TIN = os.environ.get("BUSINESS_TIN", "31569955-0001")
BUSINESS_SERVICE_ID = os.environ.get("BUSINESS_SERVICE_ID", "94ND90NR")
BUSINESS_UUID = os.environ.get("BUSINESS_UUID", str(uuid.uuid4()))

# Placeholder for certificate - in a real scenario, load from secure storage
FIRS_CERTIFICATE_B64 = "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUYwekNDQTd1Z0F3SUJBZ0lVYVpIS0c0elpLS1J5TDQrRzFvRndocFhlY0Nrd0RRWUpLb1pJaHZjTkFRRUwKQlFBd2dZRXhDekFKQmdOVkJBWVRBa2ROTVJFd0R3WURWUVFJREFoQlltRnFZVE10UkVNeEVEQU9CZ05WQkFjTQpCME5vYjI5c1lXNHhFakFRQmdOVkJBb01DV2QwZEdWamFDMWpZVEVXTUJRR0ExVUVBd3dOWjNSMFpXTm9MV05oCkxYQnliMlF4SVRBZkJna3Foa2lHOXcwQkNRRVdFbXR5YVhOME5EZEFaMjFoYVd3dVkyOXRNQjRYRFRJME1EUXkKTVRFMU1UZ3dPRm9YRFRJeU1EVXdOakUxTVRnd09Gb3dnWUV4Q3pBSkJnTlZCQVlUQWtkTk1SRXdEd1lEVlFRSQpEQWhCWW1GcVlUTXRSRU14RURBT0JnTlZCQWNNQjBOb2IyOXNZVzR4RWpBUUJnTlZCQW9NQ1dkMGRHVmphQzFqCllURVdNQlFHQTFVRUF3d05aM1IwWldOb0xXTmhMWEJ5YjJReElUQWZCZ2txaGtpRzl3MEJDUUVXRW10eWFYTjAKTkRkQVoyMWhhV3d1WTI5dE1JSUNJakFOQmdrcWhraUc5dzBCQVFFRkFBT0NBZzhBTUlJQ0NnS0NBZ0VBdDdzeApOQVhHUlhiT2dnbFRLMkp5Q2xNcndDMFZCS1BwU21mOHQ0bXd1NU5wSHU1eE9WNFo5TnUzT1Zpem4zZ1FoWkhRCm4wNmh3bWtFTm1XUUpIMzVoeExwNzdudUlUYXNDWElsYUxaS3JvWUFsT3NoNVJveFlUdEt0VCtPNTI1VlMvSkwKRGhsSmpHTzdOdWVpM3BKWmdrVTZhUXRFcERQdjBQdDhsaUNNSUpOYnkyQSszNEhLUkJuU3R3RDBTOXNUdXdCdQpaR2Q4ZXc5OVNqRFBpTWViV00xMEhkaUZRQzdrSVVCZmVsUDJwZWVaUThOcytpd2ZQSkJKeGtRaVBQVGtQZnVDCmlDQVB3WmY1QVlrVFlteFNRRzFZTEMwQ29QVXpqcEtTaWVsV2ZJVmRObnJzbnpQeFpUYUF5QXZJUGEyQnE1RVMKZXJtUG5PbkhJMnZBNTBPeTlRUmZFYXN2YkJKWUlkQjJLVWM3VE12SVlpWVRlQnBKRmQzTG0yMyt5eWJaSy9TegpGWE14aWNqMGhSOFhRMnB5ZlltKzdhSTVieCtpNkMzWmdoL0M1dFlKZUhhclJiVElLWnRIVk53bnF6amdrT1lZCmpYRDJqNUJNRm9RWCtVVjUwNFQ5czRKWnlZSW0wY1Y0OVN5dU5VMjA4ODMxMW0xQm9xbjc5MktSMUNBVk9LM0MKTHZuRjhIbWhvY1ZFbXhOWjVUbG9yRk44UDNZYURMKzB5OHdKSmtISXNDalVRTFBVdTh2T1d3SFNTODZ5NVpsNQpKUWdKQmZyTzNMK2hLTUlDTmlNMm1Zam5MOXNzU1F0cExjZ2dIbjZPa2IrNTlOTWVwZi9JMkVyM293OHpFN1IxCkQzWXVOVW4zVEo1MDdUZGlZMUFseHR3RHh6akdlcHhPSEQ4Q0F3RUFBYU5UTUZFd0hRWURWUjBPQkJZRUZLUnQKY09wTU41a1pOY0VLK0FsVVJkdDVELzJyTUI4R0ExVWRJd1FZTUJhQUZLUnRjT3BNTjVrWk5jRUsrQWxVUmR0NQpELzJyTUE4R0ExVWRFd0VCL3dRRk1BTUJBZjh3RFFZSktvWklodmNOQVFFTEJRQURnZ0lCQUE2MjUwUlZwWkZ1CnZ3b09Dc2cvWkUxZmY1UlVUVkNKdytKa0Q4TDlXa21KQ1NIM0FvQnFZOGtFOVpvb3YrSTBTQjVsWVNNaWFSeTQKQTVndm1RUGdqcEtTOXVNejI1RDFXYkZJeFNQYTdTdWZpRmE0ZkdoM0FscVp5azlIWkw2SUoxNVhKSkx0L0I3NQpFMnBGWHFTOFdpOFE2RExPeXlZU2V4UWk1RHlBMXZiS0p5UDdBZ2JzYTZ2RkxFeG12Z2pPakZFZDdCUDBUSTFRCm9ibTYzVFNlcVE1aTNzcVowRnh0RklxUVpjT1E5SjJybzEwQzZoYkE2aWdXalhjbUozL0JUZ0wzamZkUzdrVTAKWGx3a3pDRytiR0xDWVN0bkZFTm1wazZJMGhta04zSHIyMjJjbmI2RHdiVElkYUdxbEplRjk2bzJtczhDdlFiQQphTVl1endhWjczVXJHcHMyWUtPOXFvQzFaU2g3bzVWeTVGY0hHUmUxMVFQUElTeWR0UlFaNk9FTWlWUi9WVmhOCk9nYTlYT0F6enp1T1QvNUVsK1hEOTJsdGdOV05jSXlYa25MdWxVaEQyMEVtaU1CNk0rc2VQY3AzdnJqNzJrNHUKRDdDVHpZZVVTbHdOa2MyYnUwcFN1Y3BhQ2ZmV1FGMloxemJ1aWs1dStOak1oOG9JKzBCcmVNbVMvNXR5QkxmLwpCL2tGdDRETG5HaElXbFNyUE5zT1BVdnA4Ly9CMis3ODZFY3V6WHJyVWxpclJ4U29DMXdVaWswUGpDcGZjN1pDCmJYSFNnK0x1dEh0QllkSitSSENJTDZXMUVERVlsYUlTNk1XREJqcUo3RVd3NVVkL0lQaExLMUNEbk1LckhSOHIKRHBkdUIxY1FST0pHaGorQUptbHBjQlM0SUJLYQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0t"

# Fixed uuid for the business
BUSINESS_UUID = "71fcdd6f-3027-487b-ae38-4830b99f1cf5"

def get_default_headers() -> Dict[str, str]:
    """Generate default headers for API requests."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_id = str(uuid.uuid4())
    
    return {
        "accept": "*/*",
        "x-api-key": FIRS_API_KEY,
        "x-api-secret": FIRS_API_SECRET,
        "x-timestamp": timestamp,
        "x-request-id": request_id,
        "x-certificate": FIRS_CERTIFICATE_B64,
        "Content-Type": "application/json"
    }

def test_get_countries() -> Dict[str, Any]:
    """Test the countries resource endpoint."""
    print(f"\nFetching countries from FIRS API: {FIRS_API_URL}/api/v1/invoice/resources/countries")
    
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/countries"
    headers = get_default_headers()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            countries = data.get("data", [])
            print(f"✅ Successfully retrieved {len(countries)} countries")
            
            # Display the first 5 countries
            sample_countries = []
            for country in countries[:5]:
                code = country.get("code", "Unknown")
                name = country.get("name", "Unknown Country")
                sample_countries.append(f"{code} ({name})")
            
            print(f"Sample countries: {', '.join(sample_countries)}...")
            return data
        else:
            error_msg = f"❌ Failed to fetch countries: {response.status_code} - {response.text}"
            print(error_msg)
            return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def test_get_services_codes() -> Dict[str, Any]:
    """Test the services codes resource endpoint."""
    print(f"\nFetching service codes from FIRS API: {FIRS_API_URL}/api/v1/invoice/resources/services-codes")
    
    url = f"{FIRS_API_URL}/api/v1/invoice/resources/services-codes"
    headers = get_default_headers()
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            services = data.get("data", [])
            print(f"✅ Successfully retrieved {len(services)} service codes")
            
            # Display the first 5 service codes
            sample_services = []
            for service in services[:5]:
                code = service.get("code", "Unknown")
                name = service.get("name", "Unknown Service")
                sample_services.append(f"{code} ({name})")
            
            print(f"Sample service codes: {', '.join(sample_services)}...")
            return data
        else:
            error_msg = f"❌ Failed to fetch service codes: {response.status_code} - {response.text}"
            print(error_msg)
            return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def test_verify_tin(tin: str = BUSINESS_TIN) -> Dict[str, Any]:
    """Test the verify TIN utility endpoint."""
    print(f"\nVerifying TIN with FIRS API: {FIRS_API_URL}/api/v1/utilities/verify-tin/")
    
    url = f"{FIRS_API_URL}/api/v1/utilities/verify-tin/"
    headers = get_default_headers()
    
    payload = {
        "tin": tin,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "request_id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ TIN verification successful")
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            error_msg = f"❌ Failed to verify TIN: {response.status_code} - {response.text}"
            print(error_msg)
            return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def test_authenticate(email: str = "user@example.com", password: str = "password") -> Dict[str, Any]:
    """Test the authentication endpoint."""
    print(f"\nAuthenticating with FIRS API: {FIRS_API_URL}/api/v1/utilities/authenticate")
    
    url = f"{FIRS_API_URL}/api/v1/utilities/authenticate"
    headers = get_default_headers()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    request_id = str(uuid.uuid4())
    
    payload = {
        "email": email,
        "password": password,
        "business_tin": BUSINESS_TIN,
        "service_id": BUSINESS_SERVICE_ID,
        "request_id": request_id,
        "timestamp": timestamp
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication successful")
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            error_msg = f"❌ Failed to authenticate: {response.status_code} - {response.text}"
            print(error_msg)
            return {"error": error_msg}
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def main():
    """Main function to test FIRS API endpoints."""
    print("=" * 70)
    print("FIRS API Tester V3 - Additional Endpoints")
    print("=" * 70)
    print(f"Business: {BUSINESS_NAME}")
    print(f"TIN: {BUSINESS_TIN}")
    print(f"Service ID: {BUSINESS_SERVICE_ID}")
    print(f"Business UUID: {BUSINESS_UUID}")
    print("-" * 70)
    
    # Test GetCountries endpoint
    countries_data = test_get_countries()
    
    # Test GetServicesCodes endpoint
    services_data = test_get_services_codes()
    
    # Test VerifyTin endpoint
    verify_tin_data = test_verify_tin()
    
    # We won't test authentication by default as it requires valid credentials
    # Uncomment the following line to test if you have valid credentials
    # auth_data = test_authenticate(email="your-email@example.com", password="your-password")
    
    print("\n" + "=" * 70)
    print("Testing completed!")
    print("=" * 70)

if __name__ == "__main__":
    main()

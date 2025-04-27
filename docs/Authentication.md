# Authentication
To securely access the e-invoicing API, all requests must be authenticated using
both an API key and a secret key. This two-layer authentication mechanism
enhances security by verifying the identity of the requesting application.

## API Key and Secret Key Authentication
Each application is assigned an API key and a secret key, which must be included in
the header of every API request.

## Obtaining API Key and Secret Key
- **Register Your Application**: Sign up for an account on the e-Invoicing platform
and register your application.
- **Generate API and Secret Keys**: After registration, navigate to the API section in
your account dashboard to generate both the API key and the secret key.

## Including the Keys in Requests
To authenticate your requests, include both the API key and the secret key in the
headers of each HTTP request. The headers should be structured as follows:
- **Header for API Key**: X-API-KEY
- **Header for Secret Key**: X-SECRET-KEY

## Security Best Practices
To authenticate your requests, include both the API key and the secret key in the
headers of each HTTP request. The headers should be structured as follows:
- **Keep Your Keys Confidential**: Both the API key and the secret key should be kept
secret and not shared publicly.
- **Regenerate Keys if Compromised**: If you suspect that either of your keys has
been compromised, regenerate them immediately via your account dashboard.
- **Use HTTPS**: Always use HTTPS to encrypt the data transmitted, including your
keys.

## Handling Authentication Errors
If the API key or secret key is missing, invalid, or expired, the API will return an
appropriate error message. Make sure your application handles these errors
properly.
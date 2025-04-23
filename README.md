# TaxPoynt eInvoice

A middleware service that facilitates integration between financial software and FIRS (Federal Inland Revenue Service) for electronic invoicing.

## Project Setup

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set up environment variables (create a `.env` file in the backend directory):
```
SECRET_KEY=your_secure_secret_key
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=taxpoynt
```

3. Initialize the database:
```bash
cd backend
python scripts/init_db.py
```

4. Run the development server:
```bash
cd backend
uvicorn app.main:app --reload
```

5. API Documentation:
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

## Features

### POC Phase (Current)

- Basic user registration and login with email/password
- JWT token generation and validation
- Role-based access control (admin, SI user)

## Testing

### Backend Testing

1. Run tests:
```bash
cd backend
pytest
```

2. Test API manually with Postman or curl:
   - Registration: `POST /api/v1/auth/register`
   - Login: `POST /api/v1/auth/login`
   - Get user info: `GET /api/v1/auth/me`

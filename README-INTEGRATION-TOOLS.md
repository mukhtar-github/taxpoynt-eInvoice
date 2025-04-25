# Integration Configuration Tools

This document provides information about the Integration Configuration Tools developed for the TaxPoynt eInvoice system during the POC phase.

## Overview

The Integration Configuration Tools allow system integrators to set up and manage connections between client systems and the TaxPoynt eInvoice platform. These tools are essential for enabling seamless integration with various accounting systems and ERPs.

## Features Implemented

1. **Database Models**
   - Client model for storing client information
   - Integration model for storing integration configurations
   - Integration history model for tracking configuration changes

2. **API Endpoints**
   - CRUD operations for clients and integrations
   - Integration testing endpoint
   - Integration history endpoint

3. **Frontend Components**
   - Integration listing page
   - Integration creation form
   - JSON configuration editor

## Database Schema

The Integration Configuration Tools use the following database tables:

### Clients Table
Stores information about the clients that will be integrated with the system.

### Integrations Table
Stores configuration details for each integration, linked to a specific client.

### Integration History Table
Tracks changes to integration configurations for audit and rollback purposes.

## API Endpoints

### Client Endpoints

- `GET /clients` - List all clients
- `POST /clients` - Create a new client
- `GET /clients/{client_id}` - Get client details
- `PUT /clients/{client_id}` - Update client details
- `DELETE /clients/{client_id}` - Delete a client

### Integration Endpoints

- `GET /integrations` - List all integrations
- `POST /integrations` - Create a new integration
- `GET /integrations/{integration_id}` - Get integration details
- `PUT /integrations/{integration_id}` - Update integration configuration
- `DELETE /integrations/{integration_id}` - Delete an integration
- `POST /integrations/{integration_id}/test` - Test integration connection
- `GET /integrations/{integration_id}/history` - Get integration configuration history

## Frontend Pages

- `/integrations` - Main page for listing and managing integrations
- `/integrations/new` - Page for creating a new integration

## Setup Instructions

### Backend Setup

1. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```

2. Apply database migrations:
   ```
   alembic upgrade head
   ```

3. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```

2. Configure the API URL in `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Start the frontend development server:
   ```
   npm run dev
   ```

## Integration Configuration Format

The integration configuration is stored as a JSON object in the database. The basic structure is:

```json
{
  "api_url": "https://erp.client.com/api",
  "auth_method": "api_key",
  "api_key": "client_api_key_here",
  "schedule": "daily",
  "timezone": "Africa/Lagos"
}
```

Different integration types may have additional configuration options specific to their needs.

## Next Steps

Future improvements planned for the Integration Configuration Tools include:

1. Connection testing with specific error messages and troubleshooting
2. Template-based configuration for common accounting systems
3. Automated discovery of API endpoints
4. Advanced scheduling options
5. Integration cloning and versioning

## Documentation

For more information about the TaxPoynt eInvoice system, refer to the following documentation:

- [API Documentation](docs/api_docs.md)
- [Data Schema Documentation](docs/data_schema.md)
- [Development Guidelines](docs/dev_guidelines.md) 
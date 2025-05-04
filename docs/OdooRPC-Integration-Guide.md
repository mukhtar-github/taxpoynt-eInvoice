# OdooRPC Integration Guide

This guide explains how to use the OdooRPC integration in the TaxPoynt eInvoice system.

## Overview

We've integrated OdooRPC into the TaxPoynt eInvoice system to provide a more robust and maintainable way to connect with Odoo ERP systems. OdooRPC provides a clean, Pythonic interface to interact with Odoo's API.

## Backend Implementation

The integration is primarily implemented in:
- `odoo_service.py` - Core service for Odoo operations
- `integration_service.py` - Service for handling integration configurations and operations

### Key Functions

#### Testing Odoo Connection

```python
def test_odoo_connection(connection_params):
    # Using OdooRPC for connection testing
    odoo = odoorpc.ODOO(host, protocol=protocol, port=port)
    # ...
```

#### Fetching Invoices

```python
def fetch_odoo_invoices(config, from_date=None, limit=100, offset=0):
    # Using OdooRPC for fetching invoices with ORM-like access
    Invoice = odoo.env['account.move']
    invoices = Invoice.browse(invoice_ids)
    # ...
```

## Frontend Implementation

The frontend interacts with the OdooRPC integration through API endpoints. Here's how to use them:

### Testing a Connection

```typescript
import axios, { AxiosError } from 'axios';

// Define interface for the error response
interface ApiErrorResponse {
  detail: string;
  status_code: number;
}

async function testOdooConnection(connectionParams: OdooConnectionParams) {
  try {
    const response = await axios.post('/api/integrations/odoo/test-connection', connectionParams);
    return response.data;
  } catch (error) {
    // Properly type the error to access the response data
    const axiosError = error as AxiosError<ApiErrorResponse>;
    if (axiosError.response?.data) {
      throw new Error(axiosError.response.data.detail || 'Connection failed');
    }
    throw new Error('Failed to test connection');
  }
}
```

### Syncing Invoices

```typescript
import axios, { AxiosError } from 'axios';

// Define interface for the error response
interface ApiErrorResponse {
  detail: string;
  status_code: number;
}

async function syncOdooInvoices(integrationId: string, fromDaysAgo: number = 30, limit: number = 100) {
  try {
    const response = await axios.post(`/api/integrations/${integrationId}/sync-invoices`, {
      from_days_ago: fromDaysAgo,
      limit: limit
    });
    return response.data;
  } catch (error) {
    // Properly type the error to access the response data
    const axiosError = error as AxiosError<ApiErrorResponse>;
    if (axiosError.response?.data) {
      throw new Error(axiosError.response.data.detail || 'Sync failed');
    }
    throw new Error('Failed to sync invoices');
  }
}
```

## Example: Integration Form Component

Here's an example of how to use the OdooRPC integration in a React component:

```tsx
import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';

interface OdooConnectionParams {
  url: string;
  database: string;
  username: string;
  password: string;
  use_api_key: boolean;
}

interface ApiErrorResponse {
  detail: string;
  status_code: number;
}

const OdooIntegrationForm: React.FC = () => {
  const [connectionParams, setConnectionParams] = useState<OdooConnectionParams>({
    url: '',
    database: '',
    username: '',
    password: '',
    use_api_key: false
  });
  const [testResult, setTestResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setConnectionParams({
      ...connectionParams,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const testConnection = async () => {
    setIsLoading(true);
    setError('');
    setTestResult('');
    
    try {
      const response = await axios.post('/api/integrations/odoo/test-connection', connectionParams);
      setTestResult('Connection successful!');
    } catch (error) {
      // Properly type the error to access the response data
      const axiosError = error as AxiosError<ApiErrorResponse>;
      setError(axiosError.response?.data?.detail || 'Connection failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="odoo-integration-form">
      <h2>Odoo Integration</h2>
      
      <div className="form-group">
        <label htmlFor="url">Odoo URL</label>
        <input
          type="text"
          id="url"
          name="url"
          value={connectionParams.url}
          onChange={handleChange}
          placeholder="https://example.odoo.com"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="database">Database</label>
        <input
          type="text"
          id="database"
          name="database"
          value={connectionParams.database}
          onChange={handleChange}
          placeholder="example_db"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="username">Username</label>
        <input
          type="text"
          id="username"
          name="username"
          value={connectionParams.username}
          onChange={handleChange}
          placeholder="admin@example.com"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password/API Key</label>
        <input
          type="password"
          id="password"
          name="password"
          value={connectionParams.password}
          onChange={handleChange}
          placeholder="•••••••••"
        />
      </div>
      
      <div className="form-group checkbox">
        <input
          type="checkbox"
          id="use_api_key"
          name="use_api_key"
          checked={connectionParams.use_api_key}
          onChange={handleChange}
        />
        <label htmlFor="use_api_key">Use API Key</label>
      </div>
      
      <button 
        className="btn btn-primary" 
        onClick={testConnection}
        disabled={isLoading}
      >
        {isLoading ? 'Testing...' : 'Test Connection'}
      </button>
      
      {testResult && <div className="success-message">{testResult}</div>}
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default OdooIntegrationForm;
```

## Tips for Error Handling

When handling API errors in TypeScript, especially with Axios:

1. **Type the error correctly**:
   ```typescript
   try {
     // API call
   } catch (error) {
     const axiosError = error as AxiosError<ApiErrorResponse>;
     // Now you can safely access axiosError.response?.data.detail
   }
   ```

2. **Create specific interfaces for API responses**:
   ```typescript
   interface ApiErrorResponse {
     detail: string;
     status_code: number;
   }
   ```

3. **Use type guards for more complex scenarios**:
   ```typescript
   function isApiErrorResponse(obj: any): obj is ApiErrorResponse {
     return obj && typeof obj.detail === 'string';
   }
   
   try {
     // API call
   } catch (error) {
     const axiosError = error as AxiosError;
     if (axiosError.response && isApiErrorResponse(axiosError.response.data)) {
       console.error(axiosError.response.data.detail);
     }
   }
   ```

## Testing the Integration

You can test the OdooRPC integration using the example script in `examples/odoorpc_demo.py`.

To run:

```bash
cd taxpoynt-eInvoice
source venv/bin/activate
python examples/odoorpc_demo.py
```

Update the configuration in the script with your actual Odoo credentials to test against your own Odoo instance.

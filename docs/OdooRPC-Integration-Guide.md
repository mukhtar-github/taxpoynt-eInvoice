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
    odoo = odoorpc.ODOO(
        connection_params["host"], 
        protocol=connection_params["protocol"], 
        port=connection_params["port"]
    )
    # ...
```

#### Fetching Invoices

```python
def fetch_odoo_invoices(config, from_date=None, limit=100, offset=0):
    # Using OdooRPC for fetching invoices with ORM-like access
    odoo = odoorpc.ODOO(
        config["host"], 
        protocol=config["protocol"], 
        port=config["port"]
    )
    # ...
    Invoice = odoo.env['account.move']
    invoices = Invoice.browse(invoice_ids)
    # ...
```

## Connection Configuration

The OdooRPC integration expects the following configuration structure:

```python
odoo_config = {
    "host": "your-instance.odoo.com",  # Odoo server hostname
    "port": 443,                        # Default HTTPS port
    "protocol": "jsonrpc+ssl",          # Use SSL for security
    "database": "your_database_name",   # Database name
    "username": "your_email@example.com", # Username/email
    "password": "your_password_or_api_key", # Password or API key
    "use_api_key": True                 # True if using API key
}
```

**Important Notes:**
1. Do not include `/odoo` in the host parameter, as this would cause the RPC calls to fail
2. Always use SSL protocols (`jsonrpc+ssl` or `xmlrpc+ssl`) for production environments
3. For enhanced security, use API keys instead of passwords
4. The version of OdooRPC we're using (0.10.1) doesn't support the `base_url` parameter directly in the constructor

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

interface OdooConnectionParams {
  host: string;
  port: number;
  protocol: string;
  database: string;
  username: string;
  password: string;
  use_api_key: boolean;
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
  host: string;
  port: number;
  protocol: string;
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
    host: '',
    port: 443,
    protocol: 'jsonrpc+ssl',
    database: '',
    username: '',
    password: '',
    use_api_key: false
  });
  const [testResult, setTestResult] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    // Handle checkbox vs other input types
    const inputValue = (type === 'checkbox') 
      ? (e.target as HTMLInputElement).checked
      : (name === 'port' ? parseInt(value, 10) : value);
    
    setConnectionParams({
      ...connectionParams,
      [name]: inputValue
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
        <label htmlFor="host">Odoo Host</label>
        <input
          type="text"
          id="host"
          name="host"
          value={connectionParams.host}
          onChange={handleChange}
          placeholder="your-instance.odoo.com"
        />
        <small>Do not include http:// or path components</small>
      </div>
      
      <div className="form-group">
        <label htmlFor="protocol">Protocol</label>
        <select
          id="protocol"
          name="protocol"
          value={connectionParams.protocol}
          onChange={handleChange}
        >
          <option value="jsonrpc+ssl">JSON-RPC (SSL/HTTPS)</option>
          <option value="jsonrpc">JSON-RPC (HTTP)</option>
          <option value="xmlrpc+ssl">XML-RPC (SSL/HTTPS)</option>
          <option value="xmlrpc">XML-RPC (HTTP)</option>
        </select>
      </div>
      
      <div className="form-group">
        <label htmlFor="port">Port</label>
        <input
          type="number"
          id="port"
          name="port"
          value={connectionParams.port}
          onChange={handleChange}
          placeholder="443"
        />
        <small>Usually 443 for HTTPS or 8069 for HTTP</small>
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

# API Client Harmonization

## Overview

This document explains the harmonization of multiple API client implementations in the TaxPoynt eInvoice frontend project to improve maintainability and ensure consistent behavior across the application.

## Background

Previously, the project had two separate API client implementations:

1. `apiClient.ts`: Basic implementation with auth token handling
2. `api.ts`: More advanced implementation with token refresh functionality

Having multiple implementations led to:
- Inconsistent behavior in API requests
- Duplicated code
- Potential maintenance issues
- Different error handling approaches

## Solution

We've created a unified API client with the following characteristics:

1. **Unified Implementation**: Created a new `apiService.ts` that combines the best features of both previous implementations
2. **Backward Compatibility**: Updated existing `api.ts` and `apiClient.ts` to use the new service internally
3. **Enhanced Features**: Included token refresh, comprehensive error handling, and request/response interceptors

## Implementation Details

### 1. New ApiService Class

The new `apiService.ts` implements a class-based approach with:

- Token management (including refresh logic)
- Comprehensive error handling
- Queue management for requests during token refresh
- Consistent redirect on authentication failures
- Typed request/response methods

### 2. Backward Compatibility

The existing files now:
- Import and use the new unified service
- Maintain their original exported interfaces
- Include deprecation notices to encourage migration
- Share the same interceptors for consistent behavior

## Usage Guidelines

### For New Code

```typescript
import apiService from 'utils/apiService';

// Using the service
async function fetchData() {
  try {
    const response = await apiService.get('/api/endpoint');
    return response.data;
  } catch (error) {
    // Error handling
  }
}
```

### For Existing Code

Existing code using `api.ts` or `apiClient.ts` will continue to work without changes, but developers are encouraged to migrate to the new service when convenient.

## Migration Path

1. **Short-term**: Use backward-compatible adapters (`api.ts` and `apiClient.ts`)
2. **Medium-term**: Gradually migrate components to use `apiService.ts` directly
3. **Long-term**: Remove deprecated adapters once all code has migrated

## Benefits

- **Consistency**: All API requests now handle errors, authentication, and token refresh consistently
- **Maintainability**: Single source of truth for API communication logic
- **Type Safety**: Better TypeScript integration with proper types for requests and responses
- **Feature Complete**: Combines all features previously split between implementations

## Compatibility Notes

This change is fully compatible with Next.js v13.0.0 and existing ESLint configuration. No changes to the build process are required.

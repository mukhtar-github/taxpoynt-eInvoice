# Testing Guide for TaxPoynT E-Invoice

This document provides instructions on how to run tests for the TaxPoynT E-Invoice application.

## Backend Tests

### Prerequisites
- Python 3.8+
- PostgreSQL (for integration tests with real database)
- Required packages installed (`pip install -r backend/requirements.txt`)

### Running Backend Tests

#### Unit Tests for Authentication
```bash
cd backend
pytest tests/api/test_auth_endpoints.py -v
```

#### Integration Tests
```bash
cd backend
pytest tests/services/test_auth_integration_service.py -v
```

#### Run All Backend Tests
```bash
cd backend
pytest
```

## Frontend Tests

### Prerequisites
- Node.js 14+
- npm/yarn
- Required packages installed (`cd frontend && npm install`)

### Running Frontend Tests

#### Unit Tests for Authentication
```bash
cd frontend
npm test -- tests/unit/auth
```

#### Run Tests in Watch Mode
```bash
cd frontend
npm run test:watch
```

#### End-to-End Tests with Cypress

1. Start the backend server:
```bash
cd backend
uvicorn app.main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend
npm run dev
```

3. Run Cypress tests in interactive mode:
```bash
cd frontend
npm run cypress:open
```

4. Or run Cypress tests headlessly:
```bash
cd frontend
npm run cypress:run
```

## Continuous Integration

When committing to the repository, ensure all tests pass:

```bash
# Run backend tests
cd backend
pytest

# Run frontend unit tests
cd frontend
npm test

# Run E2E tests
cd frontend
npm run test:e2e
```

## Troubleshooting

### Backend Tests
- Ensure the test database configurations are correct
- Make sure pytest is installed (`pip install pytest`)

### Frontend Tests
- If tests fail to find components, check that data-cy attributes are correctly set
- For Cypress tests, ensure both backend and frontend servers are running
- Clear browser cache if experiencing unexpected behavior

## Additional Resources

- [FastAPI Testing Documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Cypress Documentation](https://docs.cypress.io/guides/overview/why-cypress) 
### Development Guidelines
These guidelines ensure consistency and quality in coding and collaboration, crucial for a small team. They include:
- **Coding Standards**: ESLint for TypeScript and PEP 8 for Python, ensuring readability and maintainability, aligning with best practices for SIs' integration needs.
- **Naming Conventions**: camelCase for TypeScript, snake_case for Python, and PascalCase for classes, ensuring clarity across the codebase.
- **Git Workflow**: Feature branches, descriptive names, and code reviews via pull requests, facilitating collaboration and version control.
- **Testing Practices**: Unit tests with Jest and Pytest, integration tests, E2E tests with Cypress, and 80% coverage, ensuring robustness, especially for security-critical operations like data encryption.
- **Security Rules**: Environment variables for sensitive data, JWT authentication, input validation, and HTTPS, addressing the FIRS emphasis on security features like IRN and CSID.

## General Coding Standards

### TypeScript (Frontend)
- Use TypeScript strict mode
- Follow ESLint configuration with Airbnb preset
- Maintain proper type definitions for all components
- Use functional components with React hooks
- Organize imports alphabetically
- Max line length of 100 characters
- Two space indentation

### Python (Backend)
- Follow PEP 8 style guide
- Use type annotations with mypy
- Follow Black code formatter rules
- Organize imports using isort
- Document functions and classes with docstrings
- Max line length of 88 characters (Black default)
- Four space indentation

## Feature-Specific Development Guidelines

### 1. Authentication and Authorization

#### Best Practices
- Never store plaintext passwords, always use bcrypt for hashing
- Implement password complexity requirements (8+ chars, mixed case, numbers)
- Set appropriate JWT expiration times (access token: 15-60 min, refresh token: 7-30 days)
- Use stateless JWT for API authentication
- Implement rate limiting on auth endpoints (max 10 requests per minute)
- Use RBAC (Role-Based Access Control) for authorization
- Require email verification for new accounts
- Log all authentication events for audit purposes

#### Code Structure
- Separate authentication logic from business logic
- Store authentication middleware in dedicated folder
- Use decorators/middlewares for route protection
- Implement clean error messages that don't expose system details

#### Security Considerations
- Implement CSRF protection for web forms
- Use secure, HTTP-only cookies for refresh tokens
- Set proper CORS policies
- Implement MFA (Multi-Factor Authentication) for sensitive operations
- Sanitize all user inputs to prevent injection attacks

### 2. Integration Configuration

#### Best Practices
- Use JSON Schema validation for configuration data
- Encrypt sensitive configuration values in the database
- Implement configuration versioning
- Create configuration templates for common integration patterns
- Validate configurations before saving
- Use transactions for configuration updates
- Implement connection testing for each configuration

#### Code Structure
- Create abstract integration base classes/interfaces
- Implement provider-specific concrete implementations
- Use factory pattern for integration creation
- Separate configuration validation from business logic

#### Security Considerations
- Mask sensitive data in logs and UI
- Validate all input against allowed schema
- Implement proper access control for configuration data
- Audit all configuration changes

### 3. Invoice Reference Number (IRN) Generation

#### Best Practices
- Use atomic operations for IRN generation to prevent duplicates
- Implement proper error handling for generation failures
- Cache generated IRNs for performance
- Include validation mechanisms for IRN format
- Follow FIRS specifications exactly for IRN format
- Implement IRN status tracking (unused, used, expired)
- Use batch operations for bulk IRN generation

#### Code Structure
- Create dedicated service for IRN generation
- Separate IRN generation logic from API endpoints
- Use repository pattern for IRN storage
- Implement clean interfaces for IRN operations

#### Performance Considerations
- Use database indexing for IRN lookups
- Implement caching mechanisms for frequently accessed IRNs
- Use batch processing for bulk operations
- Optimize database queries for IRN status updates

### 4. Invoice Validation

#### Best Practices
- Implement validation as a pipeline of rules
- Create reusable validation rules
- Use JSON Schema for basic structure validation
- Implement business-logic validation separate from schema validation
- Provide detailed validation error messages
- Group validation errors by field and severity
- Allow for optional warnings vs. required fields

#### Code Structure
- Create rule interfaces/abstract classes
- Implement concrete validation rules
- Use decorator or strategy pattern for validation rules
- Separate validation logic from API endpoints

#### Performance Considerations
- Optimize validation for large invoice batches
- Implement early returns for critical validation failures
- Cache validation results when appropriate
- Use parallel processing for independent validation rules

### 5. Data Encryption

#### Best Practices
- Use industry-standard encryption algorithms (AES-256-GCM)
- Implement proper key management with key rotation
- Never hardcode encryption keys
- Store encryption keys separate from encrypted data
- Use transport layer security (TLS) for all communications
- Implement field-level encryption for sensitive data
- Follow the principle of least privilege for encryption operations

#### Code Structure
- Create encryption service separate from business logic
- Implement interfaces for encryption operations
- Use decorator pattern for automatic encryption/decryption
- Create dedicated utilities for common encryption operations

#### Security Considerations
- Implement secure key storage (HSM if possible)
- Rotate encryption keys periodically
- Audit all encryption/decryption operations
- Test encryption implementation against known vulnerabilities
- Implement key backup and recovery procedures

### 6. Monitoring Dashboard

#### Best Practices
- Use real-time updates for dashboard data (WebSockets)
- Implement efficient data aggregation
- Create reusable dashboard components
- Use appropriate visualizations for different metrics
- Implement proper date/time handling for all metrics
- Allow filtering and custom date ranges
- Optimize for mobile and desktop views

#### Code Structure
- Separate data fetching from presentation
- Create dedicated API endpoints for dashboard data
- Implement caching for dashboard metrics
- Use reactive programming patterns for real-time updates

#### Performance Considerations
- Aggregate data server-side when possible
- Implement pagination for large datasets
- Use appropriate indexing for metrics queries
- Cache dashboard data with appropriate TTL
- Use lazy loading for dashboard components

## Git Workflow

1. **Branching Strategy**:
   - `main`: Production-ready code
   - `develop`: Integration branch for features
   - `feature/[feature-name]`: For new features
   - `bugfix/[bug-description]`: For bug fixes
   - `hotfix/[hotfix-description]`: For urgent production fixes

2. **Commit Messages**:
   - Format: `type(scope): short description`
   - Types: feat, fix, docs, style, refactor, test, chore
   - Example: `feat(auth): implement JWT refresh token`

3. **Pull Request Process**:
   - Create PRs against the `develop` branch
   - Require at least one code review
   - Pass all automated tests
   - Squash commits before merging
   - Delete branch after merging

## Code Review Guidelines

1. **What to Look For**:
   - Correctness: Does the code work as intended?
   - Security: Are there potential vulnerabilities?
   - Performance: Are there inefficient operations?
   - Readability: Is the code clear and maintainable?
   - Test coverage: Are all scenarios tested?

2. **Review Process**:
   - Reviewer should check out branch locally
   - Run tests to verify functionality
   - Provide specific, actionable feedback
   - Approve only when all issues are addressed

## Documentation Requirements

All code should include:

1. **API Endpoints**:
   - Description of purpose
   - Request/response formats
   - Authentication requirements
   - Error responses
   - Usage examples

2. **Functions/Methods**:
   - Purpose description
   - Parameter descriptions
   - Return value description
   - Exception handling
   - Usage examples for complex functions

3. **Components**:
   - Purpose and usage
   - Props/inputs
   - Events/outputs
   - State management
   - Example usage

## Deployment Guidelines

1. **Environment Setup**:
   - Development: Local environment
   - Staging: Mirrors production for testing
   - Production: Live environment

2. **Deployment Process**:
   - Automated CI/CD pipeline using GitHub Actions
   - Run all tests before deployment
   - Use infrastructure as code for environment setup
   - Implement blue-green deployment for zero downtime
   - Monitor application performance after deployment

3. **Rollback Procedure**:
   - Maintain previous version deployment configuration
   - Implement automated rollback for failed deployments
   - Document manual rollback procedures

## Security Standards

1. **Authentication & Authorization**:
   - Secure password handling (bcrypt, Argon2)
   - JWT with appropriate expiration
   - Role-based access control
   - Rate limiting

2. **Data Protection**:
   - Encrypt sensitive data at rest
   - Use HTTPS for all communications
   - Implement proper CORS policies
   - Sanitize all user inputs

3. **API Security**:
   - Input validation on all endpoints
   - Rate limiting and throttling
   - Proper error handling without exposing internals
   - Security headers (Content-Security-Policy, X-XSS-Protection)
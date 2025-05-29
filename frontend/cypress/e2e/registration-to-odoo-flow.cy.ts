/// <reference types="cypress" />
// End-to-end test for the registration to Odoo connection flow
describe('Registration to Odoo Connection Flow', () => {
  const companyName = 'MT Garba Global Ventures';
  const taxId = '12345678';

  beforeEach(() => {
    // Reset and mock API responses as needed
    cy.intercept('POST', '/api/auth/register', {
      statusCode: 201,
      body: {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User'
      }
    }).as('registerUser');

    cy.intercept('POST', '/api/organizations', {
      statusCode: 201,
      body: {
        id: 'org-123',
        name: companyName,
        tax_id: taxId,
        logo_url: null,
        branding_settings: {
          primary_color: '#1a73e8',
          theme: 'light'
        }
      }
    }).as('createOrganization');

    cy.intercept('POST', '/api/organizations/*/integrations', {
      statusCode: 201,
      body: {
        id: 'integration-123',
        name: 'Odoo Integration',
        type: 'odoo',
        status: 'configured'
      }
    }).as('createIntegration');

    cy.intercept('POST', '/api/organizations/*/integrations/*/test', {
      statusCode: 200,
      body: {
        status: 'success',
        message: 'Connection successful'
      }
    }).as('testIntegration');

    // Clean up cookies and local storage before tests
    cy.clearCookies();
    cy.clearLocalStorage();
  });

  it('should allow user to register, set up company and connect to Odoo', () => {
    // Step 1: Visit the registration page
    cy.visit('/register');
    cy.get('[data-cy=register-form]').should('be.visible');

    // Step 2: Fill out registration form
    cy.get('[data-cy=input-name]').type('Test User');
    cy.get('[data-cy=input-email]').type('test@example.com');
    cy.get('[data-cy=input-password]').type('Password123!');
    cy.get('[data-cy=input-confirm-password]').type('Password123!');
    cy.get('[data-cy=submit-button]').click();

    // Wait for registration API call to complete
    cy.wait('@registerUser');

    // Step 3: Should redirect to company registration
    cy.url().should('include', '/register/company');
    cy.get('[data-cy=company-registration-form]').should('be.visible');

    // Step 4: Fill out company registration form
    cy.get('[data-cy=input-company-name]').type(companyName);
    cy.get('[data-cy=input-tax-id]').type(taxId);
    cy.get('[data-cy=submit-button]').click();

    // Wait for organization creation API call to complete
    cy.wait('@createOrganization');

    // Step 5: Should redirect to dashboard with option to set up integrations
    cy.url().should('include', '/dashboard');
    cy.get('[data-cy=setup-integration-button]').should('be.visible').click();

    // Step 6: Should show integration options
    cy.get('[data-cy=integration-options]').should('be.visible');
    cy.get('[data-cy=odoo-integration-option]').should('be.visible').click();

    // Step 7: Should show the Odoo integration setup wizard
    cy.get('[data-cy=integration-setup-wizard]').should('be.visible');
    cy.get('[data-cy=step-connection-details]').should('be.visible');

    // Step 8: Fill out Odoo connection details
    cy.get('[data-cy=input-odoo-url]').type('https://example.odoo.com');
    cy.get('[data-cy=input-database]').type('test_db');
    cy.get('[data-cy=select-auth-method]').select('password');
    cy.get('[data-cy=input-username]').type('admin');
    cy.get('[data-cy=input-password]').type('admin');
    cy.get('[data-cy=next-button]').click();

    // Step 9: Test the connection
    cy.get('[data-cy=step-test-connection]').should('be.visible');
    cy.get('[data-cy=test-connection-button]').click();

    // Wait for test integration API call to complete
    cy.wait('@testIntegration');

    // Step 10: Should show success message and allow to proceed
    cy.get('[data-cy=connection-success-message]').should('be.visible');
    cy.get('[data-cy=next-button]').click();

    // Step 11: Complete the setup
    cy.get('[data-cy=step-configuration-summary]').should('be.visible');
    cy.get('[data-cy=finish-button]').click();

    // Step 12: Should redirect to dashboard with integration status
    cy.url().should('include', '/dashboard');
    cy.get('[data-cy=integration-status-panel]').should('be.visible');
    cy.get('[data-cy=integration-status]').should('contain', 'Connected');

    // Step 13: Should show Odoo data sections
    cy.get('[data-cy=odoo-invoices-section]').should('be.visible');
    cy.get('[data-cy=odoo-customers-section]').should('be.visible');
    cy.get('[data-cy=odoo-products-section]').should('be.visible');
  });

  it('should handle failed Odoo connection gracefully', () => {
    // Override the successful test connection with a failure
    cy.intercept('POST', '/api/organizations/*/integrations/*/test', {
      statusCode: 200,
      body: {
        status: 'error',
        message: 'Connection failed: Invalid credentials'
      }
    }).as('testIntegrationFailure');

    // Follow same steps as successful flow up to connection test
    cy.visit('/register');
    cy.get('[data-cy=register-form]').should('be.visible');
    cy.get('[data-cy=input-name]').type('Test User');
    cy.get('[data-cy=input-email]').type('test@example.com');
    cy.get('[data-cy=input-password]').type('Password123!');
    cy.get('[data-cy=input-confirm-password]').type('Password123!');
    cy.get('[data-cy=submit-button]').click();
    cy.wait('@registerUser');

    cy.url().should('include', '/register/company');
    cy.get('[data-cy=company-registration-form]').should('be.visible');
    cy.get('[data-cy=input-company-name]').type(companyName);
    cy.get('[data-cy=input-tax-id]').type(taxId);
    cy.get('[data-cy=submit-button]').click();
    cy.wait('@createOrganization');

    cy.url().should('include', '/dashboard');
    cy.get('[data-cy=setup-integration-button]').should('be.visible').click();
    cy.get('[data-cy=integration-options]').should('be.visible');
    cy.get('[data-cy=odoo-integration-option]').should('be.visible').click();

    cy.get('[data-cy=integration-setup-wizard]').should('be.visible');
    cy.get('[data-cy=input-odoo-url]').type('https://example.odoo.com');
    cy.get('[data-cy=input-database]').type('test_db');
    cy.get('[data-cy=select-auth-method]').select('password');
    cy.get('[data-cy=input-username]').type('admin');
    cy.get('[data-cy=input-password]').type('wrong_password');
    cy.get('[data-cy=next-button]').click();

    // Test the connection (this will fail)
    cy.get('[data-cy=step-test-connection]').should('be.visible');
    cy.get('[data-cy=test-connection-button]').click();
    cy.wait('@testIntegrationFailure');

    // Should show error message and allow to retry
    cy.get('[data-cy=connection-error-message]').should('be.visible');
    cy.get('[data-cy=connection-error-message]').should('contain', 'Invalid credentials');
    cy.get('[data-cy=retry-button]').should('be.visible');

    // Should allow to go back and edit connection details
    cy.get('[data-cy=back-button]').click();
    cy.get('[data-cy=step-connection-details]').should('be.visible');
    cy.get('[data-cy=input-password]').clear().type('admin');
    cy.get('[data-cy=next-button]').click();

    // Override with successful response for the retry
    cy.intercept('POST', '/api/organizations/*/integrations/*/test', {
      statusCode: 200,
      body: {
        status: 'success',
        message: 'Connection successful'
      }
    }).as('testIntegrationSuccess');

    // Test the connection again (this will succeed)
    cy.get('[data-cy=test-connection-button]').click();
    cy.wait('@testIntegrationSuccess');
    cy.get('[data-cy=connection-success-message]').should('be.visible');
  });
});

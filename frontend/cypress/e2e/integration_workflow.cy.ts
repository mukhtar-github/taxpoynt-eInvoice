/// <reference types="cypress" />

describe('ERP Integration Flow', () => {
  beforeEach(() => {
    // Mock auth
    cy.intercept('GET', '/api/v1/auth/user', {
      statusCode: 200,
      body: {
        id: 'user-123',
        name: 'Test User',
        email: 'test@example.com',
        organization: {
          id: 'org-123',
          name: 'Test Organization'
        }
      }
    }).as('getUser');
    
    // Mock integrations list
    cy.intercept('GET', '/api/v1/organizations/*/integrations', {
      statusCode: 200,
      body: {
        success: true,
        integrations: [
          {
            id: 'int-1',
            name: 'Test Odoo Integration',
            description: 'Integration with Odoo ERP',
            integration_type: 'odoo',
            status: 'configured',
            created_at: '2025-05-01T10:00:00Z',
            last_sync: '2025-05-27T15:30:00Z'
          }
        ]
      }
    }).as('getIntegrations');
  });
  
  it('should display the integrations list', () => {
    cy.visit('/dashboard/integrations');
    cy.wait('@getUser');
    cy.wait('@getIntegrations');
    
    cy.contains('ERP Integrations').should('be.visible');
    cy.contains('Test Odoo Integration').should('be.visible');
    cy.contains('Configured').should('be.visible');
  });
  
  it('should navigate to integration details', () => {
    // Mock integration detail
    cy.intercept('GET', '/api/v1/organizations/*/integrations/int-1', {
      statusCode: 200,
      body: {
        success: true,
        integration: {
          id: 'int-1',
          name: 'Test Odoo Integration',
          description: 'Integration with Odoo ERP',
          integration_type: 'odoo',
          status: 'configured',
          created_at: '2025-05-01T10:00:00Z',
          last_sync: '2025-05-27T15:30:00Z',
          config: {
            url: 'https://demo.odoo.com',
            database: 'demo_db'
          }
        }
      }
    }).as('getIntegration');
    
    // Mock company info
    cy.intercept('GET', '/api/v1/organizations/*/integrations/*/company', {
      statusCode: 200,
      body: {
        success: true,
        company: {
          id: 1,
          name: 'Test Company',
          vat: '123456789',
          email: 'company@example.com',
          phone: '+1234567890'
        }
      }
    }).as('getCompanyInfo');
    
    // Mock invoices
    cy.intercept('GET', '/api/v1/organizations/*/integrations/*/odoo/invoices*', {
      statusCode: 200,
      body: {
        success: true,
        invoices: [
          {
            id: 1,
            name: 'INV/2025/0001',
            partner_id: { id: 1, name: 'Customer 1' },
            date: '2025-05-20',
            amount_total: 1000,
            state: 'posted',
            currency: 'NGN'
          }
        ],
        total: 1
      }
    }).as('getInvoices');
    
    cy.visit('/dashboard/integrations');
    cy.wait('@getIntegrations');
    
    cy.contains('Test Odoo Integration').click();
    cy.wait('@getIntegration');
    cy.wait('@getCompanyInfo');
    cy.wait('@getInvoices');
    
    // Check details page
    cy.contains('Test Odoo Integration').should('be.visible');
    cy.contains('Invoices').should('be.visible');
    cy.contains('Customers').should('be.visible');
    cy.contains('Products').should('be.visible');
    
    // Check invoice tab
    cy.contains('INV/2025/0001').should('be.visible');
    cy.contains('Customer 1').should('be.visible');
  });
  
  it('should sync an integration', () => {
    // Mock sync endpoint
    cy.intercept('POST', '/api/v1/organizations/*/integrations/*/sync', {
      statusCode: 200,
      body: {
        success: true,
        message: 'Sync initiated successfully',
        integration: {
          id: 'int-1',
          status: 'syncing'
        }
      }
    }).as('syncIntegration');
    
    // Mock integration detail with status changes
    let syncCount = 0;
    cy.intercept('GET', '/api/v1/organizations/*/integrations/int-1', (req) => {
      // First response: syncing status
      if (syncCount === 0) {
        req.reply({
          statusCode: 200,
          body: {
            success: true,
            integration: {
              id: 'int-1',
              name: 'Test Odoo Integration',
              integration_type: 'odoo',
              status: 'syncing',
              created_at: '2025-05-01T10:00:00Z'
            }
          }
        });
        syncCount++;
      } else {
        // Second response: configured status with updated last_sync
        req.reply({
          statusCode: 200,
          body: {
            success: true,
            integration: {
              id: 'int-1',
              name: 'Test Odoo Integration',
              integration_type: 'odoo',
              status: 'configured',
              created_at: '2025-05-01T10:00:00Z',
              last_sync: new Date().toISOString()
            }
          }
        });
      }
    }).as('getIntegrationStatus');
    
    cy.visit('/dashboard/integrations/int-1');
    cy.wait('@getIntegration');
    
    // Click the sync button
    cy.contains('Sync').click();
    cy.wait('@syncIntegration');
    
    // Status should change to syncing
    cy.contains('Syncing').should('be.visible');
    
    // Simulate polling by forcing another request
    cy.wait(5000); // Wait for polling
    cy.wait('@getIntegrationStatus');
    
    // Status should change back to configured
    cy.contains('Configured').should('be.visible');
  });
  
  it('should handle API errors gracefully', () => {
    // Mock integration list with error
    cy.intercept('GET', '/api/v1/organizations/*/integrations', {
      statusCode: 500,
      body: {
        success: false,
        error: 'Server error occurred'
      }
    }).as('getIntegrationsError');
    
    cy.visit('/dashboard/integrations');
    cy.wait('@getUser');
    cy.wait('@getIntegrationsError');
    
    // Should show error message
    cy.contains('Failed to fetch integrations').should('be.visible');
  });
  
  it('should add a new integration', () => {
    // Mock test connection endpoint
    cy.intercept('POST', '/api/v1/organizations/*/integrations/test-connection', {
      statusCode: 200,
      body: {
        success: true,
        message: 'Connection successful'
      }
    }).as('testConnection');
    
    // Mock create integration endpoint
    cy.intercept('POST', '/api/v1/organizations/*/integrations', {
      statusCode: 201,
      body: {
        success: true,
        integration: {
          id: 'int-2',
          name: 'New Test Integration',
          integration_type: 'odoo',
          status: 'configured'
        }
      }
    }).as('createIntegration');
    
    cy.visit('/dashboard/integrations/add');
    cy.wait('@getUser');
    
    // Step 1: Select integration type
    cy.contains('Odoo').click();
    cy.contains('Next').click();
    
    // Step 2: Fill connection form
    cy.get('input[name="url"]').type('https://test.odoo.com');
    cy.get('input[name="database"]').type('test_db');
    cy.get('select[name="auth_method"]').select('password');
    cy.get('input[name="username"]').type('admin');
    cy.get('input[name="password"]').type('password123');
    
    // Test connection
    cy.contains('Test Connection').click();
    cy.wait('@testConnection');
    cy.contains('Connection successful').should('be.visible');
    
    cy.contains('Next').click();
    
    // Step 3: Finalize
    cy.get('input[name="name"]').type('New Test Integration');
    cy.get('textarea[name="description"]').type('Integration for testing');
    
    cy.contains('Create Integration').click();
    cy.wait('@createIntegration');
    
    // Should redirect to integrations list
    cy.url().should('include', '/dashboard/integrations');
  });
});

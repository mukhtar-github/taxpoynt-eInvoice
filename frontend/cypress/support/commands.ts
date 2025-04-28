// ***********************************************
// This example commands.ts shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

// Add TypeScript types
declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Custom command to login a user via UI
       * @example cy.login('test@example.com', 'password123')
       */
      login(email: string, password: string): Chainable<Element>;
      
      /**
       * Custom command to register a new user via UI
       * @example cy.register('test@example.com', 'password123', 'Test User')
       */
      register(email: string, password: string, fullName: string): Chainable<Element>;
      
      /**
       * Custom command to login via API (faster than UI)
       * @example cy.loginByApi('test@example.com', 'password123')
       */
      loginByApi(email: string, password: string): Chainable<Element>;
      
      /**
       * Custom command to logout
       * @example cy.logout()
       */
      logout(): Chainable<Element>;
    }
  }
}

// Login through the UI form
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/login');
  cy.get('[data-cy=input-email]').type(email);
  cy.get('[data-cy=input-password]').type(password);
  cy.get('[data-cy=btn-login]').click();
  
  // Wait for redirect to dashboard or success indication
  cy.url().should('include', '/dashboard');
});

// Register through the UI form
Cypress.Commands.add('register', (email: string, password: string, fullName: string) => {
  cy.visit('/register');
  cy.get('[data-cy=input-email]').type(email);
  cy.get('[data-cy=input-password]').type(password);
  cy.get('[data-cy=input-fullname]').type(fullName);
  cy.get('[data-cy=btn-register]').click();
  
  // Wait for redirect or success message
  cy.url().should('include', '/login');
});

// Login directly via API to save time in tests that just need an authenticated user
Cypress.Commands.add('loginByApi', (email: string, password: string) => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl') || 'http://localhost:8000'}/api/v1/auth/login`,
    body: {
      username: email,
      password: password,
    },
    form: true, // Send as form data for FastAPI
  }).then((response) => {
    // Store token in localStorage
    window.localStorage.setItem('token', response.body.access_token);
    
    // Visit dashboard to apply the token
    cy.visit('/dashboard');
  });
});

// Logout functionality
Cypress.Commands.add('logout', () => {
  // If there's a logout button/link
  cy.get('[data-cy=btn-logout]').click();
  
  // Alternative: just clear localStorage
  // cy.clearLocalStorage('token');
  
  // Verify logged out state
  cy.url().should('eq', Cypress.config().baseUrl + '/');
});

export {}; 
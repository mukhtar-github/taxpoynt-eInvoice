describe('Authentication Flow', () => {
  const testEmail = `test${Math.floor(Math.random() * 10000)}@example.com`;
  const testPassword = 'Password123!';
  const testFullName = 'Test User';

  beforeEach(() => {
    // Visit the homepage
    cy.visit('/');
  });

  it('should register a new user successfully', () => {
    // Navigate to register page
    cy.get('[data-cy=nav-register]').click();
    cy.url().should('include', '/register');

    // Fill in the form
    cy.get('[data-cy=input-email]').type(testEmail);
    cy.get('[data-cy=input-password]').type(testPassword);
    cy.get('[data-cy=input-fullname]').type(testFullName);
    
    // Submit form
    cy.get('[data-cy=btn-register]').click();
    
    // Verify successful registration (could redirect to login or dashboard)
    cy.url().should('include', '/login');
    cy.get('[data-cy=register-success]').should('be.visible');
  });

  it('should log in successfully and access protected content', () => {
    // Navigate to login page
    cy.get('[data-cy=nav-login]').click();
    cy.url().should('include', '/login');
    
    // Fill in the form
    cy.get('[data-cy=input-email]').type(testEmail);
    cy.get('[data-cy=input-password]').type(testPassword);
    
    // Submit form
    cy.get('[data-cy=btn-login]').click();
    
    // Verify successful login (redirected to dashboard)
    cy.url().should('include', '/dashboard');
    
    // Verify auth state by checking protected content
    cy.get('[data-cy=user-greeting]').should('contain', testFullName);
  });

  it('should handle invalid login attempts', () => {
    // Navigate to login page
    cy.get('[data-cy=nav-login]').click();
    
    // Try invalid email
    cy.get('[data-cy=input-email]').type('invalid@example.com');
    cy.get('[data-cy=input-password]').type('wrongpassword');
    cy.get('[data-cy=btn-login]').click();
    
    // Verify error message
    cy.get('[data-cy=login-error]').should('be.visible');
    cy.url().should('include', '/login'); // Still on login page
  });

  it('should log out correctly', () => {
    // Log in first
    cy.get('[data-cy=nav-login]').click();
    cy.get('[data-cy=input-email]').type(testEmail);
    cy.get('[data-cy=input-password]').type(testPassword);
    cy.get('[data-cy=btn-login]').click();
    
    // Verify login
    cy.url().should('include', '/dashboard');
    
    // Log out
    cy.get('[data-cy=btn-logout]').click();
    
    // Verify logout (back to homepage or login)
    cy.url().should('eq', Cypress.config().baseUrl + '/');
    
    // Try to access protected route
    cy.visit('/dashboard');
    
    // Should be redirected to login
    cy.url().should('include', '/login');
  });

  it('should maintain authenticated state across page navigation', () => {
    // Log in
    cy.get('[data-cy=nav-login]').click();
    cy.get('[data-cy=input-email]').type(testEmail);
    cy.get('[data-cy=input-password]').type(testPassword);
    cy.get('[data-cy=btn-login]').click();
    
    // Navigate to different pages
    cy.get('[data-cy=nav-profile]').click();
    cy.url().should('include', '/profile');
    cy.get('[data-cy=user-email]').should('contain', testEmail);
    
    cy.get('[data-cy=nav-settings]').click();
    cy.url().should('include', '/settings');
    
    cy.get('[data-cy=nav-dashboard]').click();
    cy.url().should('include', '/dashboard');
    
    // Still authenticated after navigation
    cy.get('[data-cy=user-greeting]').should('be.visible');
  });
}); 
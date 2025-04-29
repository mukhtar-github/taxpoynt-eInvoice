// ***********************************************************
// This file is processed and loaded automatically before your test files.
//
// This is a great place to put global configuration and behavior that modifies Cypress.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Prevent TypeScript errors when Cypress adds custom commands
declare global {
  namespace Cypress {
    interface Window {
      localStorage: Storage;
    }
  }
}

// Preserve localStorage between tests to maintain auth state
// Note: In newer Cypress versions, we don't need preserveOnce as cookies are preserved by default
// with the right configuration in cypress.config.ts
beforeEach(() => {
  // We can use sessionStorage or localStorage to maintain state
  // The token is typically stored in localStorage
});

// Error handling
Cypress.on('uncaught:exception', (err) => {
  // Returning false here prevents Cypress from failing the test
  // Useful for third-party library errors that don't affect test
  // You might want to adjust this based on your needs
  console.error('Uncaught exception:', err);
  return false;
}); 
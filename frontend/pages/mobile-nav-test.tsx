import React from 'react';
import { MobileNav } from '../components/ui/MobileNav';
import { Container } from '../components/ui/Container';

const MobileNavTestPage: React.FC = () => {
  const mockUserInfo = {
    name: 'John Doe',
    email: 'john.doe@example.com'
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Navigation */}
      <MobileNav 
        userInfo={mockUserInfo}
        onLogout={() => alert('Logged out')}
      />

      {/* Main Content */}
      <Container maxWidth="lg" padding="medium" className="pt-8 md:pt-12">
        <h1 className="text-3xl font-heading font-semibold mb-6">Mobile Navigation Test</h1>
        
        <div className="space-y-6">
          <p className="text-lg">
            This page demonstrates the MobileNav component. Resize your browser to mobile width 
            to see the mobile navigation bar with hamburger menu.
          </p>
          
          <h2 className="text-2xl font-heading font-semibold mt-8 mb-4">Features Implemented:</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>Responsive mobile-only navigation bar</li>
            <li>Hamburger menu toggle</li>
            <li>Animated slide-in drawer</li>
            <li>User profile section</li>
            <li>Navigation links with active state</li>
            <li>Logout functionality</li>
            <li>Accessibility features (aria-labels, proper focus handling)</li>
          </ul>
          
          <h2 className="text-2xl font-heading font-semibold mt-8 mb-4">Testing Instructions:</h2>
          <ol className="list-decimal pl-6 space-y-2">
            <li>Resize browser to mobile width (&lt;768px)</li>
            <li>Click hamburger icon to open drawer</li>
            <li>Verify profile info display</li>
            <li>Check that navigation links highlight correctly</li>
            <li>Test backdrop click to close</li>
            <li>Test X button to close</li>
            <li>Test logout functionality</li>
          </ol>
        </div>
      </Container>
    </div>
  );
};

export default MobileNavTestPage; 
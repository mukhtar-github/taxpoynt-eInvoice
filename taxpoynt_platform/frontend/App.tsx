/**
 * TaxPoynt Platform - Main Application
 * ====================================
 * 
 * Root application component with providers and routing.
 * Supports Business Interface, System Integrator Interface, and APP Interface.
 */
import React from 'react';
import AppRouter from './shared_components/AppRouter';
import { CombinedProvider } from './role_management/combined_provider';
import { FeatureFlagProvider } from './role_management/feature_flag_provider';

const App: React.FC = () => {
  return (
    <div className="App">
      <FeatureFlagProvider>
        <CombinedProvider>
          <AppRouter />
        </CombinedProvider>
      </FeatureFlagProvider>
    </div>
  );
};

export default App;
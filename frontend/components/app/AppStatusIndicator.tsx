import React from 'react';
import { isFeatureEnabled } from '../../config/featureFlags';

/**
 * AppStatusIndicator component
 * 
 * Displays the current status of APP functionality
 * Used as a placeholder during the SI-focused MVP phase
 * Will be expanded with real functionality when APP features are implemented
 */
interface AppStatusIndicatorProps {
  variant?: 'default' | 'compact' | 'detailed';
  className?: string;
}

const AppStatusIndicator: React.FC<AppStatusIndicatorProps> = ({ 
  variant = 'default',
  className = ''
}) => {
  // Only render if APP UI elements are enabled
  if (!isFeatureEnabled('APP_UI_ELEMENTS')) {
    return null;
  }
  
  // Different variants for different contexts
  if (variant === 'compact') {
    return (
      <div className={`app-status-indicator-compact ${className}`}>
        <span className="badge badge-info">APP: Coming Soon</span>
      </div>
    );
  }
  
  if (variant === 'detailed') {
    return (
      <div className={`app-status-indicator-detailed ${className}`}>
        <h4>APP Functionality Status</h4>
        <div className="status-grid">
          <div className="status-item">
            <span className="status-label">Certificate Management</span>
            <span className="status-badge coming-soon">Coming Soon</span>
          </div>
          <div className="status-item">
            <span className="status-label">Cryptographic Stamping</span>
            <span className="status-badge coming-soon">Coming Soon</span>
          </div>
          <div className="status-item">
            <span className="status-label">Secure Transmission</span>
            <span className="status-badge coming-soon">Coming Soon</span>
          </div>
        </div>
        <p className="status-note">
          These APP features will be available in the next phase of development.
          Contact support for more information about our APP certification timeline.
        </p>
      </div>
    );
  }
  
  // Default variant
  return (
    <div className={`app-status-indicator ${className}`}>
      <div className="status-content">
        <span className="status-icon">🔒</span>
        <span className="status-text">APP Features: Coming Soon</span>
        <span className="status-info-icon" title="Access Point Provider functionality will be available in the next development phase">ⓘ</span>
      </div>
    </div>
  );
};

export default AppStatusIndicator;

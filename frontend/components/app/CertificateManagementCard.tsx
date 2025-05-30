import React from 'react';
import { isFeatureEnabled } from '../../config/featureFlags';

/**
 * CertificateManagementCard component
 * 
 * Placeholder dashboard card for certificate management functionality
 * Will be expanded with actual certificate management in the APP phase
 */
interface CertificateManagementCardProps {
  className?: string;
}

const CertificateManagementCard: React.FC<CertificateManagementCardProps> = ({ 
  className = '' 
}) => {
  // Only render if APP UI elements are enabled
  if (!isFeatureEnabled('APP_UI_ELEMENTS')) {
    return null;
  }
  
  return (
    <div className={`card certificate-management-card ${className}`}>
      <div className="card-header">
        <h3 className="card-title">
          <span className="card-icon">🔐</span>
          Certificate Management
        </h3>
        <span className="badge badge-info">Coming Soon</span>
      </div>
      
      <div className="card-body">
        <div className="placeholder-content">
          <p>
            As an Access Point Provider (APP), TaxPoynt will soon offer complete
            certificate management for secure e-invoice transmission:
          </p>
          
          <ul className="feature-list">
            <li>Digital certificate issuance and renewal</li>
            <li>Certificate status monitoring</li>
            <li>Secure key storage and management</li>
            <li>Cryptographic invoice stamping</li>
          </ul>
          
          <div className="placeholder-cta">
            <button className="btn btn-outline-primary" disabled>
              Request Certificate (Coming Soon)
            </button>
          </div>
        </div>
      </div>
      
      <div className="card-footer">
        <small className="text-muted">
          APP functionality will be available in the next development phase.
        </small>
      </div>
    </div>
  );
};

export default CertificateManagementCard;

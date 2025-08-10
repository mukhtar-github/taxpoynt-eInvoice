/**
 * FormSection Component
 * ====================
 * 
 * Organized form section with title, description, and grouped form fields.
 * Provides consistent spacing and visual hierarchy for complex forms.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React from 'react';
import { colors, typography, spacing, borders } from '../../design_system/tokens';

export interface FormSectionProps {
  title?: string;
  description?: string;
  required?: boolean;
  children: React.ReactNode;
  role?: 'si' | 'app' | 'hybrid' | 'admin';
  variant?: 'default' | 'bordered' | 'card';
  collapsible?: boolean;
  defaultCollapsed?: boolean;
  className?: string;
  'data-testid'?: string;
}

export const FormSection: React.FC<FormSectionProps> = ({
  title,
  description,
  required = false,
  children,
  role,
  variant = 'default',
  collapsible = false,
  defaultCollapsed = false,
  className = '',
  'data-testid': testId,
}) => {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed);
  const roleColor = role ? colors.roles[role] : colors.brand.primary;

  const getVariantStyles = () => {
    switch (variant) {
      case 'bordered':
        return {
          border: `${borders.width[1]} solid ${colors.neutral[200]}`,
          borderRadius: borders.radius.lg,
          padding: spacing[6],
        };
      
      case 'card':
        return {
          backgroundColor: '#FFFFFF',
          border: `${borders.width[1]} solid ${colors.neutral[200]}`,
          borderRadius: borders.radius.lg,
          padding: spacing[6],
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
        };
      
      default:
        return {
          padding: 0,
        };
    }
  };

  const sectionStyles = {
    marginBottom: spacing[8],
    ...getVariantStyles(),
  };

  const headerStyles = {
    marginBottom: title || description ? spacing[6] : 0,
  };

  const titleStyles = {
    fontSize: typography.sizes.lg,
    fontWeight: typography.weights.semibold,
    color: colors.neutral[900],
    margin: 0,
    marginBottom: description ? spacing[2] : 0,
    display: 'flex',
    alignItems: 'center',
    gap: spacing[2],
  };

  const descriptionStyles = {
    fontSize: typography.sizes.sm,
    color: colors.neutral[600],
    lineHeight: typography.lineHeights.relaxed,
    margin: 0,
  };

  const requiredIndicatorStyles = {
    color: colors.semantic.error,
    fontSize: typography.sizes.base,
    fontWeight: typography.weights.medium,
  };

  const collapseButtonStyles = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '24px',
    height: '24px',
    border: `${borders.width[1]} solid ${colors.neutral[300]}`,
    borderRadius: borders.radius.md,
    backgroundColor: '#FFFFFF',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    color: colors.neutral[600],
    fontSize: '12px',
    padding: 0,
  };

  const contentStyles = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: spacing[4],
  };

  const roleAccentStyles = role && variant !== 'default' ? {
    borderTop: `3px solid ${roleColor}`,
    borderTopLeftRadius: borders.radius.lg,
    borderTopRightRadius: borders.radius.lg,
  } : {};

  const handleToggleCollapse = () => {
    if (collapsible) {
      setIsCollapsed(!isCollapsed);
    }
  };

  return (
    <section 
      style={{ ...sectionStyles, ...roleAccentStyles }}
      className={className}
      data-testid={testId}
    >
      {(title || description || collapsible) && (
        <div style={headerStyles}>
          {title && (
            <h3 style={titleStyles}>
              {title}
              {required && <span style={requiredIndicatorStyles}>*</span>}
              {collapsible && (
                <button
                  type="button"
                  onClick={handleToggleCollapse}
                  style={collapseButtonStyles}
                  aria-label={isCollapsed ? 'Expand section' : 'Collapse section'}
                  aria-expanded={!isCollapsed}
                >
                  {isCollapsed ? '+' : '−'}
                </button>
              )}
            </h3>
          )}
          {description && !isCollapsed && (
            <p style={descriptionStyles}>
              {description}
            </p>
          )}
        </div>
      )}
      
      {!isCollapsed && (
        <div style={contentStyles}>
          {children}
        </div>
      )}

      {/* Hover effects for interactive sections */}
      {collapsible && (
        <style jsx>{`
          button:hover {
            border-color: ${roleColor};
            background-color: ${roleColor}10;
            color: ${roleColor};
          }
        `}</style>
      )}
    </section>
  );
};

export default FormSection;
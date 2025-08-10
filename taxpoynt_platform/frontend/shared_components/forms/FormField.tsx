/**
 * FormField Component
 * ==================
 * 
 * Complete form field component with label, input, validation, and helper text.
 * Integrates with TaxPoynt design system and supports various input types.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { forwardRef } from 'react';
import { Input, InputProps } from '../../design_system/components/Input';
import { colors, typography, spacing } from '../../design_system/tokens';

export interface FormFieldProps extends Omit<InputProps, 'label' | 'error' | 'helper'> {
  label: string;
  name: string;
  error?: string | string[];
  helper?: string;
  required?: boolean;
  optional?: boolean;
  tooltip?: string;
  'data-testid'?: string;
}

export const FormField = forwardRef<HTMLInputElement, FormFieldProps>(({
  label,
  name,
  error,
  helper,
  required = false,
  optional = false,
  tooltip,
  'data-testid': testId,
  ...inputProps
}, ref) => {
  const errorMessage = Array.isArray(error) ? error[0] : error;
  const hasError = Boolean(errorMessage);

  const fieldSetStyles = {
    width: inputProps.fullWidth ? '100%' : 'auto',
    marginBottom: spacing[4],
  };

  const labelContainerStyles = {
    display: 'flex',
    alignItems: 'center',
    marginBottom: spacing[2],
    gap: spacing[2],
  };

  const labelStyles = {
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.medium,
    color: hasError ? colors.semantic.error : colors.neutral[700],
    margin: 0,
  };

  const requiredIndicatorStyles = {
    color: colors.semantic.error,
    fontSize: typography.sizes.sm,
    fontWeight: typography.weights.medium,
  };

  const optionalIndicatorStyles = {
    color: colors.neutral[500],
    fontSize: typography.sizes.xs,
    fontWeight: typography.weights.normal,
    fontStyle: 'italic' as const,
  };

  const tooltipStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '16px',
    height: '16px',
    borderRadius: '50%',
    backgroundColor: colors.neutral[400],
    color: '#FFFFFF',
    fontSize: '10px',
    fontWeight: typography.weights.bold,
    cursor: 'help',
    userSelect: 'none' as const,
  };

  const helperTextStyles = {
    fontSize: typography.sizes.sm,
    color: colors.neutral[600],
    marginTop: spacing[1],
    lineHeight: typography.lineHeights.normal,
  };

  const errorTextStyles = {
    fontSize: typography.sizes.sm,
    color: colors.semantic.error,
    marginTop: spacing[1],
    lineHeight: typography.lineHeights.normal,
    display: 'flex',
    alignItems: 'flex-start',
    gap: spacing[1],
  };

  const errorIconStyles = {
    fontSize: '14px',
    marginTop: '1px',
    flexShrink: 0,
  };

  return (
    <fieldset style={fieldSetStyles} data-testid={testId}>
      <div style={labelContainerStyles}>
        <label htmlFor={name} style={labelStyles}>
          {label}
        </label>
        
        {required && <span style={requiredIndicatorStyles}>*</span>}
        {optional && !required && <span style={optionalIndicatorStyles}>(optional)</span>}
        
        {tooltip && (
          <span 
            style={tooltipStyles}
            title={tooltip}
            aria-label={tooltip}
          >
            ?
          </span>
        )}
      </div>

      <Input
        ref={ref}
        id={name}
        name={name}
        error={errorMessage}
        required={required}
        aria-invalid={hasError}
        aria-describedby={
          hasError ? `${name}-error` : helper ? `${name}-helper` : undefined
        }
        {...inputProps}
      />

      {hasError && (
        <div 
          id={`${name}-error`}
          role="alert"
          style={errorTextStyles}
          aria-live="polite"
        >
          <span style={errorIconStyles}>⚠</span>
          <span>{errorMessage}</span>
        </div>
      )}

      {!hasError && helper && (
        <div 
          id={`${name}-helper`}
          style={helperTextStyles}
        >
          {helper}
        </div>
      )}
    </fieldset>
  );
});

FormField.displayName = 'FormField';

export default FormField;
/**
 * Enhanced Form Field Component
 * 
 * Week 3 Implementation: Advanced form validation with:
 * - Real-time validation with debouncing
 * - Multiple validation states (success, warning, error)
 * - Enhanced accessibility features
 * - Loading states and micro-animations
 * - Touch-friendly mobile design
 */

import React, { useState, useEffect, ReactNode } from 'react';
import { 
  AlertCircle, 
  CheckCircle, 
  AlertTriangle, 
  Info, 
  Eye, 
  EyeOff,
  Loader2 
} from 'lucide-react';
import { cn } from '@/utils/cn';

export interface ValidationResult {
  isValid: boolean;
  message?: string;
  type?: 'error' | 'warning' | 'success' | 'info';
}

export interface EnhancedFormFieldProps {
  children: ReactNode;
  label?: string;
  htmlFor?: string;
  helpText?: string;
  error?: boolean;
  errorMessage?: string;
  warning?: boolean;
  warningMessage?: string;
  success?: boolean;
  successMessage?: string;
  required?: boolean;
  optional?: boolean;
  className?: string;
  
  // Enhanced validation features
  validation?: ValidationResult;
  isValidating?: boolean;
  showValidationIcon?: boolean;
  
  // Enhanced UX features
  showCharacterCount?: boolean;
  maxLength?: number;
  
  // Accessibility
  describedBy?: string;
  'aria-label'?: string;
}

/**
 * Enhanced FormField component with advanced validation states and UX improvements
 */
export const EnhancedFormField: React.FC<EnhancedFormFieldProps> = ({
  children,
  label,
  htmlFor,
  helpText,
  error = false,
  errorMessage,
  warning = false,
  warningMessage,
  success = false,
  successMessage,
  required = false,
  optional = false,
  className,
  validation,
  isValidating = false,
  showValidationIcon = true,
  showCharacterCount = false,
  maxLength,
  describedBy,
  'aria-label': ariaLabel,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [characterCount, setCharacterCount] = useState(0);

  // Determine validation state
  const getValidationState = () => {
    if (validation) return validation;
    if (error) return { isValid: false, message: errorMessage, type: 'error' as const };
    if (warning) return { isValid: true, message: warningMessage, type: 'warning' as const };
    if (success) return { isValid: true, message: successMessage, type: 'success' as const };
    return null;
  };

  const validationState = getValidationState();

  // Get validation icon
  const getValidationIcon = () => {
    if (isValidating) return <Loader2 className="w-4 h-4 animate-spin text-primary" />;
    if (!validationState || !showValidationIcon) return null;

    switch (validationState.type) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-error" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-warning" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-success" />;
      case 'info':
        return <Info className="w-4 h-4 text-primary" />;
      default:
        return null;
    }
  };

  // Get border color based on validation state
  const getBorderColor = () => {
    if (isFocused) return 'ring-2 ring-primary ring-offset-2';
    if (!validationState) return 'border-gray-300';

    switch (validationState.type) {
      case 'error':
        return 'border-error shadow-sm shadow-error/20';
      case 'warning':
        return 'border-warning shadow-sm shadow-warning/20';
      case 'success':
        return 'border-success shadow-sm shadow-success/20';
      default:
        return 'border-gray-300';
    }
  };

  // Enhanced children with validation props
  const enhancedChildren = React.cloneElement(children as React.ReactElement, {
    onFocus: (e: React.FocusEvent) => {
      setIsFocused(true);
      (children as React.ReactElement).props.onFocus?.(e);
    },
    onBlur: (e: React.FocusEvent) => {
      setIsFocused(false);
      (children as React.ReactElement).props.onBlur?.(e);
    },
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      if (showCharacterCount) {
        setCharacterCount(e.target.value.length);
      }
      (children as React.ReactElement).props.onChange?.(e);
    },
    className: cn(
      'transition-all duration-200',
      getBorderColor(),
      (children as React.ReactElement).props.className
    ),
    'aria-describedby': describedBy || `${htmlFor}-help`,
    'aria-label': ariaLabel,
    'aria-invalid': validationState?.type === 'error',
  });

  return (
    <div className={cn('space-y-2', className)}>
      {/* Label */}
      {label && (
        <div className="flex items-center justify-between">
          <label 
            htmlFor={htmlFor}
            className={cn(
              'block text-sm font-medium transition-colors duration-200',
              validationState?.type === 'error' ? 'text-error' : 'text-text-primary',
              isFocused && 'text-primary'
            )}
          >
            {label}
            {required && (
              <span className="text-error ml-1" aria-label="required">*</span>
            )}
            {optional && (
              <span className="text-text-secondary ml-1 font-normal">(optional)</span>
            )}
          </label>

          {/* Character count */}
          {showCharacterCount && maxLength && (
            <span className={cn(
              'text-xs transition-colors duration-200',
              characterCount > maxLength * 0.9 ? 'text-warning' : 'text-text-secondary',
              characterCount >= maxLength && 'text-error'
            )}>
              {characterCount}/{maxLength}
            </span>
          )}
        </div>
      )}
      
      {/* Input with validation icon */}
      <div className="relative">
        {enhancedChildren}
        
        {/* Validation icon */}
        {(showValidationIcon && (validationState || isValidating)) && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {getValidationIcon()}
          </div>
        )}
      </div>
      
      {/* Help text, validation messages */}
      <div className="space-y-1">
        {/* Help text (when no validation message) */}
        {helpText && !validationState?.message && (
          <p 
            id={`${htmlFor}-help`}
            className="text-xs text-text-secondary"
          >
            {helpText}
          </p>
        )}
        
        {/* Validation message */}
        {validationState?.message && (
          <p 
            id={`${htmlFor}-validation`}
            className={cn(
              'text-xs flex items-center gap-1 animate-fade-in',
              {
                'text-error': validationState.type === 'error',
                'text-warning': validationState.type === 'warning',
                'text-success': validationState.type === 'success',
                'text-primary': validationState.type === 'info',
              }
            )}
            role={validationState.type === 'error' ? 'alert' : 'status'}
          >
            {getValidationIcon()}
            {validationState.message}
          </p>
        )}
      </div>
    </div>
  );
};

/**
 * Enhanced Input Component with built-in validation
 */
export interface EnhancedInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helpText?: string;
  error?: boolean;
  errorMessage?: string;
  warning?: boolean;
  warningMessage?: string;
  success?: boolean;
  successMessage?: string;
  validation?: ValidationResult;
  isValidating?: boolean;
  showValidationIcon?: boolean;
  showCharacterCount?: boolean;
  containerClassName?: string;
  
  // Password toggle
  showPasswordToggle?: boolean;
}

export const EnhancedInput: React.FC<EnhancedInputProps> = ({
  label,
  helpText,
  error,
  errorMessage,
  warning,
  warningMessage,
  success,
  successMessage,
  validation,
  isValidating,
  showValidationIcon = true,
  showCharacterCount,
  containerClassName,
  showPasswordToggle = false,
  type,
  className,
  ...inputProps
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const inputType = showPasswordToggle ? (showPassword ? 'text' : 'password') : type;

  return (
    <EnhancedFormField
      label={label}
      htmlFor={inputProps.id}
      helpText={helpText}
      error={error}
      errorMessage={errorMessage}
      warning={warning}
      warningMessage={warningMessage}
      success={success}
      successMessage={successMessage}
      validation={validation}
      isValidating={isValidating}
      showValidationIcon={showValidationIcon && !showPasswordToggle}
      showCharacterCount={showCharacterCount}
      maxLength={inputProps.maxLength}
      className={containerClassName}
    >
      <div className="relative">
        <input
          {...inputProps}
          type={inputType}
          className={cn(
            'w-full px-4 py-3 border rounded-lg transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:border-transparent',
            'placeholder:text-gray-400',
            showPasswordToggle && 'pr-12',
            showValidationIcon && !showPasswordToggle && 'pr-10',
            className
          )}
        />
        
        {/* Password toggle button */}
        {showPasswordToggle && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600 transition-colors"
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </button>
        )}

        {/* Validation icon for password fields */}
        {showPasswordToggle && showValidationIcon && (validation || isValidating) && (
          <div className="absolute inset-y-0 right-10 flex items-center pr-1">
            {isValidating ? (
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
            ) : validation?.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-error" />
            ) : validation?.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-success" />
            ) : null}
          </div>
        )}
      </div>
    </EnhancedFormField>
  );
};

/**
 * Enhanced Textarea Component
 */
export interface EnhancedTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helpText?: string;
  error?: boolean;
  errorMessage?: string;
  warning?: boolean;
  warningMessage?: string;
  success?: boolean;
  successMessage?: string;
  validation?: ValidationResult;
  isValidating?: boolean;
  showValidationIcon?: boolean;
  showCharacterCount?: boolean;
  containerClassName?: string;
  
  // Auto-resize
  autoResize?: boolean;
}

export const EnhancedTextarea: React.FC<EnhancedTextareaProps> = ({
  label,
  helpText,
  error,
  errorMessage,
  warning,
  warningMessage,
  success,
  successMessage,
  validation,
  isValidating,
  showValidationIcon = true,
  showCharacterCount,
  containerClassName,
  autoResize = false,
  className,
  onChange,
  ...textareaProps
}) => {
  const [textareaRef, setTextareaRef] = useState<HTMLTextAreaElement | null>(null);

  // Auto-resize functionality
  useEffect(() => {
    if (autoResize && textareaRef) {
      const adjustHeight = () => {
        textareaRef.style.height = 'auto';
        textareaRef.style.height = `${textareaRef.scrollHeight}px`;
      };
      adjustHeight();
    }
  }, [autoResize, textareaRef, textareaProps.value]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (autoResize) {
      e.target.style.height = 'auto';
      e.target.style.height = `${e.target.scrollHeight}px`;
    }
    onChange?.(e);
  };

  return (
    <EnhancedFormField
      label={label}
      htmlFor={textareaProps.id}
      helpText={helpText}
      error={error}
      errorMessage={errorMessage}
      warning={warning}
      warningMessage={warningMessage}
      success={success}
      successMessage={successMessage}
      validation={validation}
      isValidating={isValidating}
      showValidationIcon={showValidationIcon}
      showCharacterCount={showCharacterCount}
      maxLength={textareaProps.maxLength}
      className={containerClassName}
    >
      <textarea
        {...textareaProps}
        ref={setTextareaRef}
        onChange={handleChange}
        className={cn(
          'w-full px-4 py-3 border rounded-lg transition-all duration-200 resize-none',
          'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:border-transparent',
          'placeholder:text-gray-400',
          showValidationIcon && 'pr-10',
          autoResize && 'overflow-hidden',
          className
        )}
      />
    </EnhancedFormField>
  );
};

export default EnhancedFormField;
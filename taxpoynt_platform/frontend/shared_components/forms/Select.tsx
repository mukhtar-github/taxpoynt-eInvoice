/**
 * Select Component
 * ===============
 * 
 * Dropdown select component with TaxPoynt design system integration.
 * Supports single and multi-select, search, and custom rendering.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

import React, { useState, useRef, useEffect, forwardRef } from 'react';
import { colors, typography, spacing, borders, shadows, animations } from '../../design_system/tokens';

export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  icon?: React.ReactNode;
  description?: string;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string | number | (string | number)[];
  defaultValue?: string | number | (string | number)[];
  placeholder?: string;
  multiple?: boolean;
  searchable?: boolean;
  clearable?: boolean;
  disabled?: boolean;
  loading?: boolean;
  error?: string;
  size?: 'sm' | 'md' | 'lg';
  role?: 'si' | 'app' | 'hybrid' | 'admin';
  fullWidth?: boolean;
  maxHeight?: number;
  onChange?: (value: string | number | (string | number)[] | null) => void;
  onSearch?: (searchTerm: string) => void;
  renderOption?: (option: SelectOption) => React.ReactNode;
  className?: string;
  'data-testid'?: string;
}

export const Select = forwardRef<HTMLDivElement, SelectProps>(({
  options,
  value,
  defaultValue,
  placeholder = 'Select an option...',
  multiple = false,
  searchable = false,
  clearable = false,
  disabled = false,
  loading = false,
  error,
  size = 'md',
  role,
  fullWidth = false,
  maxHeight = 200,
  onChange,
  onSearch,
  renderOption,
  className = '',
  'data-testid': testId,
  ...props
}, ref) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [internalValue, setInternalValue] = useState(
    value !== undefined ? value : defaultValue || (multiple ? [] : null)
  );
  
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  
  const roleColor = role ? colors.roles[role] : colors.brand.primary;

  // Update internal value when prop changes
  useEffect(() => {
    if (value !== undefined) {
      setInternalValue(value);
    }
  }, [value]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter options based on search term
  const filteredOptions = searchable && searchTerm
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return {
          padding: `${spacing[2]} ${spacing[3]}`,
          fontSize: typography.sizes.sm,
          minHeight: '32px',
        };
      case 'lg':
        return {
          padding: `${spacing[4]} ${spacing[4]}`,
          fontSize: typography.sizes.lg,
          minHeight: '48px',
        };
      default:
        return {
          padding: `${spacing[3]} ${spacing[4]}`,
          fontSize: typography.sizes.base,
          minHeight: '40px',
        };
    }
  };

  const containerStyles = {
    position: 'relative' as const,
    width: fullWidth ? '100%' : 'auto',
    fontFamily: typography.fonts.sans.join(', '),
  };

  const triggerStyles = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    backgroundColor: disabled ? colors.neutral[100] : '#FFFFFF',
    border: `${borders.width[1]} solid ${
      error 
        ? colors.semantic.error 
        : isOpen 
          ? roleColor 
          : colors.neutral[300]
    }`,
    borderRadius: borders.radius.md,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: animations.transition.base,
    ...getSizeStyles(),
  };

  const placeholderStyles = {
    color: colors.neutral[400],
    flex: 1,
    textAlign: 'left' as const,
  };

  const valueStyles = {
    color: colors.neutral[900],
    flex: 1,
    textAlign: 'left' as const,
    display: 'flex',
    alignItems: 'center',
    gap: spacing[1],
  };

  const dropdownStyles = {
    position: 'absolute' as const,
    top: '100%',
    left: 0,
    right: 0,
    zIndex: 1000,
    backgroundColor: '#FFFFFF',
    border: `${borders.width[1]} solid ${colors.neutral[200]}`,
    borderTop: 'none',
    borderRadius: `0 0 ${borders.radius.md} ${borders.radius.md}`,
    boxShadow: shadows.lg,
    maxHeight: `${maxHeight}px`,
    overflowY: 'auto' as const,
  };

  const optionStyles = (option: SelectOption, isSelected: boolean, isHighlighted: boolean) => ({
    display: 'flex',
    alignItems: 'center',
    padding: `${spacing[3]} ${spacing[4]}`,
    cursor: option.disabled ? 'not-allowed' : 'pointer',
    backgroundColor: 
      option.disabled 
        ? 'transparent'
        : isSelected 
          ? roleColor + '20'
          : isHighlighted 
            ? colors.neutral[100] 
            : 'transparent',
    color: option.disabled ? colors.neutral[400] : colors.neutral[900],
    borderBottom: `${borders.width[1]} solid ${colors.neutral[100]}`,
    transition: animations.transition.fast,
  });

  const searchInputStyles = {
    width: '100%',
    padding: `${spacing[2]} ${spacing[3]}`,
    border: `${borders.width[1]} solid ${colors.neutral[200]}`,
    borderRadius: 0,
    outline: 'none',
    fontSize: typography.sizes.sm,
    backgroundColor: colors.neutral[50],
  };

  const handleOptionClick = (option: SelectOption) => {
    if (option.disabled || disabled) return;

    let newValue;
    
    if (multiple) {
      const currentArray = Array.isArray(internalValue) ? internalValue : [];
      const isSelected = currentArray.includes(option.value);
      
      if (isSelected) {
        newValue = currentArray.filter(v => v !== option.value);
      } else {
        newValue = [...currentArray, option.value];
      }
    } else {
      newValue = option.value;
      setIsOpen(false);
    }

    setInternalValue(newValue);
    onChange?.(newValue);
    setSearchTerm('');
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    const newValue = multiple ? [] : null;
    setInternalValue(newValue);
    onChange?.(newValue);
  };

  const getSelectedOption = (val: string | number) => 
    options.find(option => option.value === val);

  const getDisplayValue = () => {
    if (multiple && Array.isArray(internalValue)) {
      if (internalValue.length === 0) return null;
      if (internalValue.length === 1) {
        return getSelectedOption(internalValue[0])?.label;
      }
      return `${internalValue.length} selected`;
    }
    
    if (internalValue !== null && internalValue !== undefined) {
      return getSelectedOption(internalValue)?.label;
    }
    
    return null;
  };

  const isOptionSelected = (option: SelectOption) => {
    if (multiple && Array.isArray(internalValue)) {
      return internalValue.includes(option.value);
    }
    return internalValue === option.value;
  };

  const displayValue = getDisplayValue();
  const showClear = clearable && displayValue && !disabled;

  return (
    <div 
      ref={containerRef}
      style={containerStyles}
      className={className}
      data-testid={testId}
      {...props}
    >
      <div
        ref={ref}
        style={triggerStyles}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        tabIndex={disabled ? -1 : 0}
      >
        <div style={displayValue ? valueStyles : placeholderStyles}>
          {displayValue || placeholder}
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing[1] }}>
          {loading && (
            <div
              style={{
                width: '16px',
                height: '16px',
                border: `2px solid ${colors.neutral[200]}`,
                borderTop: `2px solid ${roleColor}`,
                borderRadius: borders.radius.full,
                animation: 'spin 1s linear infinite',
              }}
            />
          )}
          
          {showClear && (
            <button
              type="button"
              onClick={handleClear}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '16px',
                height: '16px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                color: colors.neutral[500],
                fontSize: '12px',
              }}
              aria-label="Clear selection"
            >
              ×
            </button>
          )}
          
          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              color: colors.neutral[500],
              fontSize: '12px',
              transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: animations.transition.fast,
            }}
          >
            ▼
          </span>
        </div>
      </div>

      {isOpen && (
        <div style={dropdownStyles} role="listbox">
          {searchable && (
            <div style={{ borderBottom: `${borders.width[1]} solid ${colors.neutral[200]}` }}>
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search options..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  onSearch?.(e.target.value);
                }}
                style={searchInputStyles}
                autoFocus
              />
            </div>
          )}
          
          {filteredOptions.length === 0 ? (
            <div style={{ padding: `${spacing[4]} ${spacing[4]}`, textAlign: 'center', color: colors.neutral[500] }}>
              No options found
            </div>
          ) : (
            filteredOptions.map((option) => (
              <div
                key={String(option.value)}
                style={optionStyles(option, isOptionSelected(option), false)}
                onClick={() => handleOptionClick(option)}
                role="option"
                aria-selected={isOptionSelected(option)}
              >
                {renderOption ? renderOption(option) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: spacing[2] }}>
                    {option.icon && <span>{option.icon}</span>}
                    <div>
                      <div>{option.label}</div>
                      {option.description && (
                        <div style={{ fontSize: typography.sizes.sm, color: colors.neutral[500] }}>
                          {option.description}
                        </div>
                      )}
                    </div>
                    {isOptionSelected(option) && (
                      <span style={{ marginLeft: 'auto', color: roleColor }}>✓</span>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
});

Select.displayName = 'Select';

export default Select;
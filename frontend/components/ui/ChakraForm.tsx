import React from 'react';

interface FormControlProps {
  children: React.ReactNode;
  isInvalid?: boolean;
  isRequired?: boolean;
}

export const FormControl: React.FC<FormControlProps> = ({ 
  children, 
  isInvalid, 
  isRequired 
}) => {
  return (
    <div style={{ 
      marginBottom: '16px', 
      position: 'relative' 
    }}>
      {children}
      {isRequired && (
        <span 
          style={{ 
            color: '#E53E3E', 
            position: 'absolute', 
            top: '0', 
            right: '-12px' 
          }}
        >
          *
        </span>
      )}
    </div>
  );
};

interface FormLabelProps {
  children: React.ReactNode;
  htmlFor?: string;
}

export const FormLabel: React.FC<FormLabelProps> = ({ 
  children, 
  htmlFor 
}) => {
  return (
    <label
      htmlFor={htmlFor}
      style={{
        fontWeight: 500,
        marginBottom: '8px',
        display: 'block'
      }}
    >
      {children}
    </label>
  );
};

interface FormErrorMessageProps {
  children: React.ReactNode;
}

export const FormErrorMessage: React.FC<FormErrorMessageProps> = ({ 
  children 
}) => {
  if (!children) return null;
  
  return (
    <div 
      style={{ 
        color: '#E53E3E', 
        fontSize: '14px', 
        marginTop: '4px' 
      }}
    >
      {children}
    </div>
  );
};

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  id?: string;
  placeholder?: string;
}

export const Input: React.FC<InputProps> = (props) => {
  return (
    <input
      style={{
        width: '100%',
        padding: '8px',
        borderWidth: '1px',
        borderColor: '#E2E8F0',
        borderRadius: '4px',
        outline: 'none'
      }}
      {...props}
      onFocus={(e) => {
        e.target.style.borderColor = '#63B3ED';
        e.target.style.boxShadow = '0 0 0 1px #63B3ED';
        if (props.onFocus) props.onFocus(e);
      }}
      onBlur={(e) => {
        e.target.style.borderColor = '#E2E8F0';
        e.target.style.boxShadow = 'none';
        if (props.onBlur) props.onBlur(e);
      }}
    />
  );
};

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  id?: string;
  placeholder?: string;
  children: React.ReactNode;
}

export const Select: React.FC<SelectProps> = ({ 
  children, 
  placeholder, 
  ...props 
}) => {
  return (
    <select
      style={{
        width: '100%',
        padding: '8px',
        borderWidth: '1px',
        borderColor: '#E2E8F0',
        borderRadius: '4px',
        outline: 'none'
      }}
      {...props}
      onFocus={(e) => {
        e.target.style.borderColor = '#63B3ED';
        e.target.style.boxShadow = '0 0 0 1px #63B3ED';
        if (props.onFocus) props.onFocus(e);
      }}
      onBlur={(e) => {
        e.target.style.borderColor = '#E2E8F0';
        e.target.style.boxShadow = 'none';
        if (props.onBlur) props.onBlur(e);
      }}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {children}
    </select>
  );
};

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  id?: string;
  placeholder?: string;
}

export const Textarea: React.FC<TextareaProps> = (props) => {
  return (
    <textarea
      rows={4}
      style={{
        width: '100%',
        padding: '8px',
        borderWidth: '1px',
        borderColor: '#E2E8F0',
        borderRadius: '4px',
        outline: 'none'
      }}
      {...props}
      onFocus={(e) => {
        e.target.style.borderColor = '#63B3ED';
        e.target.style.boxShadow = '0 0 0 1px #63B3ED';
        if (props.onFocus) props.onFocus(e);
      }}
      onBlur={(e) => {
        e.target.style.borderColor = '#E2E8F0';
        e.target.style.boxShadow = 'none';
        if (props.onBlur) props.onBlur(e);
      }}
    />
  );
};

interface VStackProps {
  children: React.ReactNode;
  spacing: number;
  align?: string;
}

export const VStack: React.FC<VStackProps> = ({ 
  children, 
  spacing, 
  align 
}) => {
  return (
    <div 
      style={{ 
        display: 'flex',
        flexDirection: 'column',
        gap: `${spacing * 4}px`,
        alignItems: align === 'flex-start' ? 'flex-start' : 'stretch',
        width: '100%'
      }}
    >
      {children}
    </div>
  );
}; 
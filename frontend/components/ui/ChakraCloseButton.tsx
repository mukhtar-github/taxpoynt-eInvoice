import React from 'react';

interface CloseButtonProps {
  onClick: () => void;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  display?: any;
}

export const CloseButton: React.FC<CloseButtonProps> = ({ 
  onClick, 
  size = 'md',
  color = 'currentColor',
  display
}) => {
  // Size mapping
  const sizeMap = {
    sm: { size: '24px', fontSize: '16px' },
    md: { size: '32px', fontSize: '20px' },
    lg: { size: '40px', fontSize: '24px' }
  };
  
  const { size: buttonSize, fontSize } = sizeMap[size];
  
  return (
    <button
      aria-label="Close"
      style={{
        display: display || 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: buttonSize,
        height: buttonSize,
        borderRadius: '50%',
        color,
        background: 'transparent',
        border: 'none',
        padding: 0,
        cursor: 'pointer'
      }}
      onClick={onClick}
    >
      <svg
        width={fontSize}
        height={fontSize}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <line x1="18" y1="6" x2="6" y2="18" />
        <line x1="6" y1="6" x2="18" y2="18" />
      </svg>
    </button>
  );
}; 
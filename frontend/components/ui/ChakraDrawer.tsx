import React from 'react';

interface DrawerProps {
  isOpen: boolean;
  placement?: 'left' | 'right' | 'top' | 'bottom';
  onClose: () => void;
  children: React.ReactNode;
  autoFocus?: boolean;
  returnFocusOnClose?: boolean;
  onOverlayClick?: () => void;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  placement = 'right',
  onClose,
  children,
  size = 'md'
}) => {
  if (!isOpen) return null;
  
  // Determine drawer width based on size
  const getWidth = () => {
    switch (size) {
      case 'xs': return '15rem';
      case 'sm': return '20rem';
      case 'md': return '25rem';
      case 'lg': return '30rem';
      case 'xl': return '35rem';
      case 'full': return '100%';
      default: return '25rem';
    }
  };

  // Position the drawer based on placement
  const getPosition = () => {
    switch (placement) {
      case 'left': return { left: 0, top: 0, bottom: 0 };
      case 'right': return { right: 0, top: 0, bottom: 0 };
      case 'top': return { top: 0, left: 0, right: 0 };
      case 'bottom': return { bottom: 0, left: 0, right: 0 };
      default: return { left: 0, top: 0, bottom: 0 };
    }
  };

  // Determine if width or height should be applied
  const isVertical = placement === 'left' || placement === 'right';
  const dimension = isVertical 
    ? { width: getWidth() } 
    : { height: getWidth() };

  return (
    <>
      {/* Overlay */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.4)',
          zIndex: 999
        }}
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div
        style={{
          position: 'fixed',
          ...getPosition(),
          ...dimension,
          backgroundColor: 'white',
          boxShadow: '0 0 10px rgba(0,0,0,0.2)',
          zIndex: 1000,
          overflowY: 'auto'
        }}
      >
        {children}
      </div>
    </>
  );
};

interface DrawerContentProps {
  children: React.ReactNode;
}

export const DrawerContent: React.FC<DrawerContentProps> = ({ children }) => {
  return (
    <div>
      {children}
    </div>
  );
}; 
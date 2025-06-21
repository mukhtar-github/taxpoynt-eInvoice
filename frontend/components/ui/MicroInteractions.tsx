/**
 * Micro-Interactions and Hover States
 * 
 * Features:
 * - Animated counters and progress indicators
 * - Smooth transitions and state changes
 * - Interactive feedback components
 * - Loading states with sophisticated animations
 * - Hover effects and focus states
 * - Touch feedback for mobile
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { cn } from '../../utils/cn';
import { Check, X, AlertCircle, Info, ChevronDown, Plus, Minus } from 'lucide-react';

// Enhanced button with micro-interactions
interface InteractiveButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
  className?: string;
  ripple?: boolean;
}

export const InteractiveButton: React.FC<InteractiveButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  className = '',
  ripple = true
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const [ripples, setRipples] = useState<Array<{ id: number; x: number; y: number }>>([]);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const variantClasses = {
    primary: 'bg-primary text-white hover:bg-primary-dark focus:ring-primary/20',
    secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200 focus:ring-gray-500/20',
    success: 'bg-success text-white hover:bg-success-dark focus:ring-success/20',
    warning: 'bg-warning text-white hover:bg-warning-dark focus:ring-warning/20',
    error: 'bg-error text-white hover:bg-error-dark focus:ring-error/20',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500/20'
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  const handleClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled || loading) return;

    if (ripple && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const newRipple = { id: Date.now(), x, y };
      setRipples(prev => [...prev, newRipple]);
      
      setTimeout(() => {
        setRipples(prev => prev.filter(r => r.id !== newRipple.id));
      }, 600);
    }

    onClick?.();
  }, [disabled, loading, onClick, ripple]);

  return (
    <button
      ref={buttonRef}
      className={cn(
        'relative overflow-hidden font-medium rounded-lg transition-all duration-200',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'transform hover:scale-105 active:scale-95',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
        variantClasses[variant],
        sizeClasses[size],
        isPressed && 'scale-95',
        className
      )}
      onClick={handleClick}
      disabled={disabled || loading}
      onMouseDown={() => setIsPressed(true)}
      onMouseUp={() => setIsPressed(false)}
      onMouseLeave={() => setIsPressed(false)}
    >
      {/* Ripple effects */}
      {ripples.map(ripple => (
        <span
          key={ripple.id}
          className="absolute rounded-full bg-white/30 animate-ping pointer-events-none"
          style={{
            left: ripple.x - 10,
            top: ripple.y - 10,
            width: 20,
            height: 20,
          }}
        />
      ))}

      {/* Loading spinner */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        </div>
      )}

      {/* Button content */}
      <span className={cn('flex items-center justify-center', loading && 'opacity-0')}>
        {children}
      </span>
    </button>
  );
};

// Animated counter component
interface AnimatedCounterProps {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  precision?: number;
  formatValue?: (value: number) => string;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  duration = 2000,
  prefix = '',
  suffix = '',
  className = '',
  precision = 0,
  formatValue
}) => {
  const [displayValue, setDisplayValue] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const counterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );

    if (counterRef.current) {
      observer.observe(counterRef.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isVisible) return;

    let startTime: number;
    let animationFrame: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const currentValue = easeOutQuart * value;
      
      setDisplayValue(currentValue);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [value, duration, isVisible]);

  const formattedValue = formatValue 
    ? formatValue(displayValue)
    : precision > 0 
      ? displayValue.toFixed(precision) 
      : Math.round(displayValue).toLocaleString();

  return (
    <div ref={counterRef} className={cn('font-bold tabular-nums', className)}>
      {prefix}{formattedValue}{suffix}
    </div>
  );
};

// Progress bar with smooth animations
interface AnimatedProgressProps {
  value: number; // 0-100
  max?: number;
  height?: string;
  color?: string;
  backgroundColor?: string;
  showLabel?: boolean;
  animated?: boolean;
  className?: string;
}

export const AnimatedProgress: React.FC<AnimatedProgressProps> = ({
  value,
  max = 100,
  height = '8px',
  color = 'bg-primary',
  backgroundColor = 'bg-gray-200',
  showLabel = false,
  animated = true,
  className = ''
}) => {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    if (!animated) {
      setAnimatedValue(value);
      return;
    }

    const timer = setTimeout(() => {
      setAnimatedValue(value);
    }, 100);

    return () => clearTimeout(timer);
  }, [value, animated]);

  const percentage = Math.min((animatedValue / max) * 100, 100);

  return (
    <div className={cn('relative', className)}>
      <div
        className={cn('w-full rounded-full overflow-hidden', backgroundColor)}
        style={{ height }}
      >
        <div
          className={cn(
            'h-full rounded-full transition-all duration-1000 ease-out',
            color,
            animated && 'animate-pulse'
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="absolute inset-0 flex items-center justify-center text-xs font-medium">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
};

// Notification toast with animations
interface NotificationToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  visible: boolean;
  onClose: () => void;
  autoClose?: number; // milliseconds
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export const NotificationToast: React.FC<NotificationToastProps> = ({
  type,
  title,
  message,
  visible,
  onClose,
  autoClose = 5000,
  position = 'top-right'
}) => {
  const [isAnimating, setIsAnimating] = useState(false);

  const icons = {
    success: <Check className="w-5 h-5" />,
    error: <X className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />
  };

  const colors = {
    success: 'bg-success text-white',
    error: 'bg-error text-white',
    warning: 'bg-warning text-white',
    info: 'bg-info text-white'
  };

  const positions = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4'
  };

  useEffect(() => {
    if (visible) {
      setIsAnimating(true);
      if (autoClose > 0) {
        const timer = setTimeout(() => {
          onClose();
        }, autoClose);
        return () => clearTimeout(timer);
      }
    } else {
      setIsAnimating(false);
    }
  }, [visible, autoClose, onClose]);

  if (!visible && !isAnimating) return null;

  return (
    <div
      className={cn(
        'fixed z-50 max-w-sm w-full shadow-lg rounded-lg overflow-hidden transition-all duration-300 transform',
        positions[position],
        colors[type],
        visible ? 'translate-x-0 opacity-100 scale-100' : 'translate-x-full opacity-0 scale-95'
      )}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {icons[type]}
          </div>
          <div className="ml-3 flex-1">
            <h3 className="text-sm font-medium">{title}</h3>
            {message && (
              <p className="mt-1 text-sm opacity-90">{message}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="ml-4 flex-shrink-0 rounded-md inline-flex text-white hover:opacity-75 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Progress bar for auto-close */}
      {autoClose > 0 && visible && (
        <div className="h-1 bg-white/20">
          <div
            className="h-full bg-white transition-all ease-linear"
            style={{
              width: '100%',
              animationDuration: `${autoClose}ms`,
              animation: 'shrink 1 linear forwards'
            }}
          />
        </div>
      )}
    </div>
  );
};

// Expandable/collapsible section with smooth animations
interface ExpandableProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  className?: string;
  headerClassName?: string;
  contentClassName?: string;
}

export const Expandable: React.FC<ExpandableProps> = ({
  title,
  children,
  defaultExpanded = false,
  className = '',
  headerClassName = '',
  contentClassName = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [height, setHeight] = useState<string | number>(defaultExpanded ? 'auto' : 0);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (contentRef.current) {
      const contentHeight = contentRef.current.scrollHeight;
      setHeight(isExpanded ? contentHeight : 0);
    }
  }, [isExpanded]);

  return (
    <div className={cn('border border-gray-200 rounded-lg overflow-hidden', className)}>
      <button
        className={cn(
          'w-full px-4 py-3 text-left bg-gray-50 hover:bg-gray-100 focus:bg-gray-100 transition-colors',
          'flex items-center justify-between focus:outline-none',
          headerClassName
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className="font-medium">{title}</span>
        <ChevronDown
          className={cn(
            'w-4 h-4 transition-transform duration-200',
            isExpanded && 'rotate-180'
          )}
        />
      </button>
      
      <div
        className="transition-all duration-300 ease-in-out overflow-hidden"
        style={{ height }}
      >
        <div ref={contentRef} className={cn('p-4', contentClassName)}>
          {children}
        </div>
      </div>
    </div>
  );
};

// Floating label input with smooth animations
interface FloatingLabelInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  required?: boolean;
  error?: string;
  className?: string;
}

export const FloatingLabelInput: React.FC<FloatingLabelInputProps> = ({
  label,
  value,
  onChange,
  type = 'text',
  required = false,
  error,
  className = ''
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const hasValue = value.length > 0;
  const isFloating = isFocused || hasValue;

  return (
    <div className={cn('relative', className)}>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        className={cn(
          'w-full px-3 pt-6 pb-2 border rounded-lg transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary',
          error ? 'border-error' : 'border-gray-300'
        )}
        required={required}
      />
      
      <label
        className={cn(
          'absolute left-3 transition-all duration-200 pointer-events-none',
          'text-gray-500',
          isFloating
            ? 'top-2 text-xs text-primary'
            : 'top-1/2 transform -translate-y-1/2 text-base'
        )}
      >
        {label}
        {required && <span className="text-error ml-1">*</span>}
      </label>
      
      {error && (
        <p className="mt-1 text-sm text-error">{error}</p>
      )}
    </div>
  );
};

// Quantity selector with smooth animations
interface QuantitySelectorProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  className?: string;
}

export const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  value,
  onChange,
  min = 0,
  max = Infinity,
  step = 1,
  className = ''
}) => {
  const [isAnimating, setIsAnimating] = useState<'up' | 'down' | null>(null);

  const handleIncrement = () => {
    if (value < max) {
      setIsAnimating('up');
      onChange(value + step);
      setTimeout(() => setIsAnimating(null), 150);
    }
  };

  const handleDecrement = () => {
    if (value > min) {
      setIsAnimating('down');
      onChange(value - step);
      setTimeout(() => setIsAnimating(null), 150);
    }
  };

  return (
    <div className={cn('flex items-center space-x-3', className)}>
      <button
        onClick={handleDecrement}
        disabled={value <= min}
        className={cn(
          'w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center',
          'hover:border-primary hover:text-primary transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-gray-300 disabled:hover:text-gray-400',
          'active:scale-90 transition-transform'
        )}
      >
        <Minus className="w-4 h-4" />
      </button>
      
      <div className="flex items-center justify-center min-w-[3rem]">
        <span
          className={cn(
            'text-lg font-semibold transition-all duration-150',
            isAnimating === 'up' && 'transform scale-110 text-primary',
            isAnimating === 'down' && 'transform scale-110 text-primary'
          )}
        >
          {value}
        </span>
      </div>
      
      <button
        onClick={handleIncrement}
        disabled={value >= max}
        className={cn(
          'w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center',
          'hover:border-primary hover:text-primary transition-colors',
          'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-gray-300 disabled:hover:text-gray-400',
          'active:scale-90 transition-transform'
        )}
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  );
};

// Add shrink animation to styles
const styles = `
@keyframes shrink {
  from { width: 100%; }
  to { width: 0%; }
}
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = styles;
  document.head.appendChild(styleElement);
}

const MicroInteractionsExports = {
  InteractiveButton,
  AnimatedCounter,
  AnimatedProgress,
  NotificationToast,
  Expandable,
  FloatingLabelInput,
  QuantitySelector
};

export default MicroInteractionsExports;
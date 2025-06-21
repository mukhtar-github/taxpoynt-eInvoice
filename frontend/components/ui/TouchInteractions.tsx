/**
 * Touch-First Interaction Components
 * 
 * Features:
 * - Swipe gestures for mobile navigation
 * - Touch-friendly action buttons
 * - Drag and drop support
 * - Pull-to-refresh functionality
 * - Long press interactions
 * - Touch feedback animations
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronLeft, ChevronRight, RotateCcw, Trash2, Archive, Check } from 'lucide-react';
import { cn } from '../../utils/cn';

// Types for touch interactions
interface TouchPoint {
  x: number;
  y: number;
  timestamp: number;
}

interface SwipeGestureProps {
  children: React.ReactNode;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
  className?: string;
}

// Custom hook for swipe gestures
const useSwipeGesture = (
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void,
  onSwipeUp?: () => void,
  onSwipeDown?: () => void,
  threshold = 50
) => {
  const [touchStart, setTouchStart] = useState<TouchPoint | null>(null);
  const [touchEnd, setTouchEnd] = useState<TouchPoint | null>(null);

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.targetTouches[0];
    setTouchStart({
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now()
    });
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const touch = e.targetTouches[0];
    setTouchEnd({
      x: touch.clientX,
      y: touch.clientY,
      timestamp: Date.now()
    });
  }, []);

  const handleTouchEnd = useCallback(() => {
    if (!touchStart || !touchEnd) return;

    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = touchStart.y - touchEnd.y;
    const isLeftSwipe = distanceX > threshold;
    const isRightSwipe = distanceX < -threshold;
    const isUpSwipe = distanceY > threshold;
    const isDownSwipe = distanceY < -threshold;

    // Determine primary direction
    if (Math.abs(distanceX) > Math.abs(distanceY)) {
      if (isLeftSwipe && onSwipeLeft) onSwipeLeft();
      if (isRightSwipe && onSwipeRight) onSwipeRight();
    } else {
      if (isUpSwipe && onSwipeUp) onSwipeUp();
      if (isDownSwipe && onSwipeDown) onSwipeDown();
    }

    setTouchStart(null);
    setTouchEnd(null);
  }, [touchStart, touchEnd, threshold, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);

  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd
  };
};

// Swipe gesture wrapper component
export const SwipeGesture: React.FC<SwipeGestureProps> = ({
  children,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  threshold = 50,
  className = ''
}) => {
  const swipeHandlers = useSwipeGesture(
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    threshold
  );

  return (
    <div className={cn('touch-pan-y', className)} {...swipeHandlers}>
      {children}
    </div>
  );
};

// Swipeable card component
interface SwipeableCardProps {
  children: React.ReactNode;
  leftAction?: {
    icon: React.ReactNode;
    label: string;
    color: string;
    action: () => void;
  };
  rightAction?: {
    icon: React.ReactNode;
    label: string;
    color: string;
    action: () => void;
  };
  className?: string;
}

export const SwipeableCard: React.FC<SwipeableCardProps> = ({
  children,
  leftAction,
  rightAction,
  className = ''
}) => {
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [isSwipeActive, setIsSwipeActive] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    setTouchStart(e.targetTouches[0].clientX);
    setIsSwipeActive(true);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchStart) return;
    
    const currentX = e.targetTouches[0].clientX;
    const diff = currentX - touchStart;
    const maxOffset = 100;
    
    // Constrain swipe offset
    const constrainedOffset = Math.max(-maxOffset, Math.min(maxOffset, diff));
    setSwipeOffset(constrainedOffset);
  };

  const handleTouchEnd = () => {
    const threshold = 50;
    
    if (Math.abs(swipeOffset) > threshold) {
      if (swipeOffset > 0 && rightAction) {
        rightAction.action();
      } else if (swipeOffset < 0 && leftAction) {
        leftAction.action();
      }
    }
    
    setSwipeOffset(0);
    setIsSwipeActive(false);
    setTouchStart(null);
  };

  return (
    <div className={cn('relative overflow-hidden', className)}>
      {/* Left action background */}
      {leftAction && (
        <div className={cn(
          'absolute left-0 top-0 bottom-0 flex items-center justify-start pl-4 w-full transition-opacity duration-200',
          leftAction.color,
          Math.abs(swipeOffset) > 20 && swipeOffset < 0 ? 'opacity-100' : 'opacity-0'
        )}>
          <div className="flex items-center text-white">
            {leftAction.icon}
            <span className="ml-2 font-medium">{leftAction.label}</span>
          </div>
        </div>
      )}
      
      {/* Right action background */}
      {rightAction && (
        <div className={cn(
          'absolute right-0 top-0 bottom-0 flex items-center justify-end pr-4 w-full transition-opacity duration-200',
          rightAction.color,
          Math.abs(swipeOffset) > 20 && swipeOffset > 0 ? 'opacity-100' : 'opacity-0'
        )}>
          <div className="flex items-center text-white">
            <span className="mr-2 font-medium">{rightAction.label}</span>
            {rightAction.icon}
          </div>
        </div>
      )}
      
      {/* Card content */}
      <div
        ref={cardRef}
        className={cn(
          'relative bg-white transition-transform duration-200 ease-out',
          isSwipeActive ? 'duration-0' : 'duration-200'
        )}
        style={{
          transform: `translateX(${swipeOffset}px)`
        }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {children}
      </div>
    </div>
  );
};

// Pull to refresh component
interface PullToRefreshProps {
  children: React.ReactNode;
  onRefresh: () => Promise<void>;
  threshold?: number;
  className?: string;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  children,
  onRefresh,
  threshold = 80,
  className = ''
}) => {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleTouchStart = (e: React.TouchEvent) => {
    const scrollTop = containerRef.current?.scrollTop || 0;
    if (scrollTop === 0) {
      setTouchStart(e.targetTouches[0].clientY);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchStart || isRefreshing) return;
    
    const scrollTop = containerRef.current?.scrollTop || 0;
    if (scrollTop > 0) return;
    
    const currentY = e.targetTouches[0].clientY;
    const diff = currentY - touchStart;
    
    if (diff > 0) {
      e.preventDefault();
      setPullDistance(Math.min(diff * 0.5, threshold * 1.5));
    }
  };

  const handleTouchEnd = async () => {
    if (pullDistance >= threshold && !isRefreshing) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
      }
    }
    
    setPullDistance(0);
    setTouchStart(null);
  };

  const refreshProgress = Math.min(pullDistance / threshold, 1);

  return (
    <div
      ref={containerRef}
      className={cn('relative overflow-auto', className)}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull to refresh indicator */}
      <div
        className="absolute top-0 left-0 right-0 flex items-center justify-center transition-all duration-300 ease-out z-10"
        style={{
          height: `${pullDistance}px`,
          opacity: refreshProgress
        }}
      >
        <div className={cn(
          'flex items-center space-x-2 text-primary',
          isRefreshing && 'animate-pulse'
        )}>
          <RotateCcw 
            className={cn(
              'w-5 h-5 transition-transform duration-300',
              isRefreshing ? 'animate-spin' : '',
              refreshProgress >= 1 ? 'rotate-180' : ''
            )}
            style={{
              transform: `rotate(${refreshProgress * 180}deg)`
            }}
          />
          <span className="text-sm font-medium">
            {isRefreshing ? 'Refreshing...' : pullDistance >= threshold ? 'Release to refresh' : 'Pull to refresh'}
          </span>
        </div>
      </div>
      
      {/* Content */}
      <div
        className="transition-transform duration-300 ease-out"
        style={{
          transform: `translateY(${pullDistance}px)`
        }}
      >
        {children}
      </div>
    </div>
  );
};

// Long press component
interface LongPressProps {
  children: React.ReactNode;
  onLongPress: () => void;
  delay?: number;
  className?: string;
}

export const LongPress: React.FC<LongPressProps> = ({
  children,
  onLongPress,
  delay = 500,
  className = ''
}) => {
  const [isPressed, setIsPressed] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const handleStart = () => {
    setIsPressed(true);
    timeoutRef.current = setTimeout(() => {
      onLongPress();
      setIsPressed(false);
    }, delay);
  };

  const handleEnd = () => {
    setIsPressed(false);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  };

  return (
    <div
      className={cn(
        'select-none transition-all duration-200',
        isPressed && 'scale-95 opacity-70',
        className
      )}
      onTouchStart={handleStart}
      onTouchEnd={handleEnd}
      onTouchCancel={handleEnd}
      onMouseDown={handleStart}
      onMouseUp={handleEnd}
      onMouseLeave={handleEnd}
    >
      {children}
    </div>
  );
};

// Touch-friendly action buttons
interface TouchActionButtonProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const TouchActionButton: React.FC<TouchActionButtonProps> = ({
  icon,
  label,
  onClick,
  variant = 'primary',
  size = 'md',
  className = ''
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const variantClasses = {
    primary: 'bg-primary text-white active:bg-primary-dark',
    secondary: 'bg-gray-100 text-gray-800 active:bg-gray-200',
    success: 'bg-success text-white active:bg-success-dark',
    warning: 'bg-warning text-white active:bg-warning-dark',
    error: 'bg-error text-white active:bg-error-dark'
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-6 py-4 text-lg'
  };

  return (
    <button
      className={cn(
        'flex items-center space-x-2 rounded-lg font-medium transition-all duration-200',
        'min-h-touch min-w-touch touch-manipulation select-none',
        'active:scale-95 active:shadow-sm',
        variantClasses[variant],
        sizeClasses[size],
        isPressed && 'scale-95 shadow-sm',
        className
      )}
      onClick={onClick}
      onTouchStart={() => setIsPressed(true)}
      onTouchEnd={() => setIsPressed(false)}
      onTouchCancel={() => setIsPressed(false)}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
};

// Floating Action Button with touch-friendly gestures
interface FloatingActionButtonProps {
  icon: React.ReactNode;
  onClick: () => void;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  icon,
  onClick,
  position = 'bottom-right',
  size = 'md',
  className = ''
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const positionClasses = {
    'bottom-right': 'fixed bottom-6 right-6',
    'bottom-left': 'fixed bottom-6 left-6',
    'top-right': 'fixed top-6 right-6',
    'top-left': 'fixed top-6 left-6'
  };

  const sizeClasses = {
    sm: 'w-12 h-12',
    md: 'w-14 h-14',
    lg: 'w-16 h-16'
  };

  return (
    <button
      className={cn(
        'flex items-center justify-center rounded-full shadow-lg',
        'bg-primary text-white hover:bg-primary-dark',
        'transition-all duration-300 z-50 touch-manipulation',
        'active:scale-90 active:shadow-xl',
        positionClasses[position],
        sizeClasses[size],
        isPressed && 'scale-90 shadow-xl',
        className
      )}
      onClick={onClick}
      onTouchStart={() => setIsPressed(true)}
      onTouchEnd={() => setIsPressed(false)}
      onTouchCancel={() => setIsPressed(false)}
    >
      {icon}
    </button>
  );
};

const TouchInteractionsExports = {
  SwipeGesture,
  SwipeableCard,
  PullToRefresh,
  LongPress,
  TouchActionButton,
  FloatingActionButton,
  useSwipeGesture
};

export default TouchInteractionsExports;
/**
 * Quick Actions Floating Button Component
 * 
 * Features:
 * - Floating Action Button (FAB) with expandable menu
 * - Mobile-first touch-friendly design
 * - Smooth animations and micro-interactions
 * - Contextual actions based on current page
 * - Keyboard navigation support
 * - Auto-hide on scroll down, show on scroll up
 * - Pulse animation for important actions
 */

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import {
  Plus,
  FileText,
  Download,
  Upload,
  Link as LinkIcon,
  Users,
  Settings,
  Zap,
  X,
  ChevronUp,
  Sync
} from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export interface QuickAction {
  id: string;
  label: string;
  icon: React.ElementType;
  onClick: () => void;
  color?: 'primary' | 'success' | 'warning' | 'error';
  pulse?: boolean; // Add pulse animation for important actions
  badge?: string | number; // Show badge with count/text
}

interface QuickActionsProps {
  actions?: QuickAction[];
  className?: string;
  position?: 'bottom-right' | 'bottom-left' | 'bottom-center';
  autoHide?: boolean; // Auto-hide on scroll
  alwaysShow?: boolean; // Never hide, even when scrolling
}

// Default actions based on current page context
const getDefaultActionsForPage = (pathname: string): QuickAction[] => {
  const baseActions: QuickAction[] = [];

  // Dashboard page actions
  if (pathname === '/dashboard') {
    baseActions.push(
      {
        id: 'generate-irn',
        label: 'Generate IRN',
        icon: FileText,
        onClick: () => window.location.href = '/dashboard/irn/generate',
        color: 'primary',
        pulse: true
      },
      {
        id: 'sync-integrations',
        label: 'Sync All',
        icon: Sync,
        onClick: () => console.log('Sync all integrations'),
        color: 'success'
      }
    );
  }

  // Integration pages
  if (pathname.includes('/integrations')) {
    baseActions.push(
      {
        id: 'add-integration',
        label: 'Add Integration',
        icon: LinkIcon,
        onClick: () => window.location.href = '/dashboard/integrations/add',
        color: 'primary'
      }
    );
  }

  // CRM pages
  if (pathname.includes('/crm')) {
    baseActions.push(
      {
        id: 'add-crm',
        label: 'Connect CRM',
        icon: Users,
        onClick: () => window.location.href = '/dashboard/crm/add',
        color: 'primary'
      }
    );
  }

  // Submission pages
  if (pathname.includes('/submission')) {
    baseActions.push(
      {
        id: 'submit-batch',
        label: 'Submit Batch',
        icon: Upload,
        onClick: () => console.log('Submit batch'),
        color: 'warning'
      },
      {
        id: 'download-report',
        label: 'Download Report',
        icon: Download,
        onClick: () => console.log('Download report'),
        color: 'success'
      }
    );
  }

  // Common actions for all pages
  baseActions.push(
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      onClick: () => window.location.href = '/dashboard/organization',
      color: 'primary'
    }
  );

  return baseActions;
};

// Hook for auto-hide behavior on scroll
const useAutoHide = (enabled: boolean) => {
  const [isVisible, setIsVisible] = useState(true);
  const lastScrollY = useRef(0);

  useEffect(() => {
    if (!enabled) return;

    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY.current && currentScrollY > 100) {
        // Scrolling down and past threshold - hide
        setIsVisible(false);
      } else if (currentScrollY < lastScrollY.current) {
        // Scrolling up - show
        setIsVisible(true);
      }
      
      lastScrollY.current = currentScrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [enabled]);

  return isVisible;
};

// Individual action button component
const ActionButton: React.FC<{
  action: QuickAction;
  isExpanded: boolean;
  index: number;
  onClose: () => void;
}> = ({ action, isExpanded, index, onClose }) => {
  const IconComponent = action.icon;
  
  const colorClasses = {
    primary: 'bg-primary hover:bg-primary-dark text-white',
    success: 'bg-success hover:bg-success/90 text-white',
    warning: 'bg-warning hover:bg-warning/90 text-white',
    error: 'bg-error hover:bg-error/90 text-white'
  };

  const handleClick = () => {
    action.onClick();
    onClose();
  };

  return (
    <div
      className={cn(
        "flex items-center gap-3 transition-all duration-300 ease-out",
        isExpanded 
          ? "opacity-100 translate-y-0" 
          : "opacity-0 translate-y-4 pointer-events-none"
      )}
      style={{ 
        transitionDelay: isExpanded ? `${index * 50}ms` : '0ms'
      }}
    >
      {/* Label */}
      <span className="bg-gray-900 text-white px-3 py-2 rounded-lg text-sm font-medium shadow-lg whitespace-nowrap">
        {action.label}
      </span>
      
      {/* Button */}
      <button
        onClick={handleClick}
        className={cn(
          "relative w-12 h-12 rounded-full shadow-lg transition-all duration-200 hover:scale-110 active:scale-95 flex items-center justify-center",
          colorClasses[action.color || 'primary'],
          action.pulse && "animate-pulse-subtle"
        )}
        aria-label={action.label}
      >
        <IconComponent className="w-5 h-5" />
        
        {/* Badge */}
        {action.badge && (
          <div className="absolute -top-1 -right-1 bg-error text-white text-xs rounded-full min-w-5 h-5 flex items-center justify-center px-1">
            {action.badge}
          </div>
        )}
      </button>
    </div>
  );
};

export const QuickActions: React.FC<QuickActionsProps> = ({
  actions,
  className = '',
  position = 'bottom-right',
  autoHide = true,
  alwaysShow = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const router = useRouter();
  const isVisible = useAutoHide(autoHide && !alwaysShow);
  
  // Use provided actions or get default ones based on current page
  const quickActions = actions || getDefaultActionsForPage(router.pathname);
  
  // Position classes
  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-6',
    'bottom-center': 'bottom-6 left-1/2 transform -translate-x-1/2'
  };

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isExpanded && !(event.target as Element).closest('.quick-actions')) {
        setIsExpanded(false);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [isExpanded]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isExpanded) {
        setIsExpanded(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isExpanded]);

  if (quickActions.length === 0) return null;

  return (
    <div
      className={cn(
        "quick-actions fixed z-50 transition-all duration-300",
        positionClasses[position],
        isVisible ? "translate-y-0 opacity-100" : "translate-y-16 opacity-0",
        // Add bottom padding on mobile to account for bottom navigation
        "mb-16 md:mb-0",
        className
      )}
    >
      {/* Action buttons - appear above main button */}
      <div className="flex flex-col-reverse items-end gap-3 mb-3">
        {quickActions.map((action, index) => (
          <ActionButton
            key={action.id}
            action={action}
            isExpanded={isExpanded}
            index={index}
            onClose={() => setIsExpanded(false)}
          />
        ))}
      </div>
      
      {/* Main FAB */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          "w-14 h-14 bg-primary hover:bg-primary-dark text-white rounded-full shadow-lg transition-all duration-300 hover:scale-110 active:scale-95 flex items-center justify-center",
          isExpanded && "rotate-45"
        )}
        aria-label={isExpanded ? "Close quick actions" : "Open quick actions"}
        aria-expanded={isExpanded}
      >
        {isExpanded ? (
          <X className="w-6 h-6" />
        ) : (
          <Plus className="w-6 h-6" />
        )}
      </button>
      
      {/* Backdrop for mobile */}
      {isExpanded && (
        <div 
          className="fixed inset-0 bg-black/20 -z-10 md:hidden"
          onClick={() => setIsExpanded(false)}
        />
      )}
    </div>
  );
};

// Hook for custom quick actions
export const useQuickActions = (actions: QuickAction[]) => {
  return { actions };
};

export default QuickActions;
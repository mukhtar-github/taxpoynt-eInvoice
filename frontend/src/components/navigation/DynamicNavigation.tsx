import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { cn } from '../../utils/cn';
import { useServiceAccess } from '../../contexts/ServiceAccessContext';
import { useServicePermissions } from '../../hooks/useServicePermissions';
import { 
  navigationItems, 
  navigationCategories, 
  getNavigationByCategory, 
  getCategoryConfig,
  type NavItem 
} from '../../config/navigationConfig';
import { Badge } from '../ui/Badge';

interface DynamicNavigationProps {
  variant?: 'sidebar' | 'horizontal' | 'dropdown';
  showCategories?: boolean;
  showDescriptions?: boolean;
  showBadges?: boolean;
  className?: string;
  itemClassName?: string;
  categoryClassName?: string;
  onItemClick?: (item: NavItem) => void;
}

interface NavigationItemProps {
  item: NavItem;
  isActive: boolean;
  showDescription?: boolean;
  showBadge?: boolean;
  className?: string;
  onClick?: (item: NavItem) => void;
}

interface CategorySectionProps {
  categoryId: string;
  items: NavItem[];
  showDescriptions?: boolean;
  showBadges?: boolean;
  itemClassName?: string;
  categoryClassName?: string;
  onItemClick?: (item: NavItem) => void;
}

// Single navigation item component
const NavigationItem: React.FC<NavigationItemProps> = ({
  item,
  isActive,
  showDescription = false,
  showBadge = false,
  className,
  onClick
}) => {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={() => onClick?.(item)}
      className={cn(
        "flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group",
        isActive 
          ? "bg-primary-100 text-primary-800 shadow-sm" 
          : "text-gray-700 hover:bg-gray-50 hover:text-gray-900",
        className
      )}
    >
      <Icon className={cn(
        "h-5 w-5 flex-shrink-0 transition-colors",
        isActive ? "text-primary-600" : "text-gray-500 group-hover:text-gray-700"
      )} />
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className={cn(
            "font-medium truncate",
            isActive ? "text-primary-900" : "text-gray-900"
          )}>
            {item.label}
          </span>
          
          {showBadge && (item.badge || item.isNew || item.isBeta) && (
            <div className="flex space-x-1">
              {item.badge && (
                <Badge variant="secondary" className="text-xs">
                  {item.badge}
                </Badge>
              )}
              {item.isNew && (
                <Badge variant="success" className="text-xs">
                  New
                </Badge>
              )}
              {item.isBeta && (
                <Badge variant="warning" className="text-xs">
                  Beta
                </Badge>
              )}
            </div>
          )}
        </div>
        
        {showDescription && item.description && (
          <p className={cn(
            "text-sm mt-1 truncate",
            isActive ? "text-primary-700" : "text-gray-500"
          )}>
            {item.description}
          </p>
        )}
      </div>
    </Link>
  );
};

// Category section component
const CategorySection: React.FC<CategorySectionProps> = ({
  categoryId,
  items,
  showDescriptions,
  showBadges,
  itemClassName,
  categoryClassName,
  onItemClick
}) => {
  const router = useRouter();
  const categoryConfig = getCategoryConfig(categoryId);

  if (!categoryConfig || items.length === 0) {
    return null;
  }

  const isActive = (href: string) => {
    return router.pathname === href || router.pathname.startsWith(`${href}/`);
  };

  const getCategoryColorClasses = (color: string) => {
    const colorMap = {
      yellow: 'text-yellow-600 bg-yellow-100 border-yellow-200',
      blue: 'text-blue-600 bg-blue-100 border-blue-200',
      cyan: 'text-cyan-600 bg-cyan-100 border-cyan-200',
      purple: 'text-purple-600 bg-purple-100 border-purple-200',
      green: 'text-green-600 bg-green-100 border-green-200',
      gray: 'text-gray-600 bg-gray-100 border-gray-200'
    };
    return colorMap[color as keyof typeof colorMap] || 'text-gray-600 bg-gray-100 border-gray-200';
  };

  const CategoryIcon = categoryConfig.icon;

  return (
    <div className="space-y-2">
      {/* Category Header */}
      <div className={cn(
        "flex items-center space-x-2 px-3 py-2 text-xs font-semibold uppercase tracking-wider rounded-md border",
        getCategoryColorClasses(categoryConfig.color),
        categoryClassName
      )}>
        <CategoryIcon className="h-4 w-4" />
        <span>{categoryConfig.label}</span>
      </div>

      {/* Category Items */}
      <div className="space-y-1">
        {items.map((item) => (
          <NavigationItem
            key={item.id}
            item={item}
            isActive={isActive(item.href)}
            showDescription={showDescriptions}
            showBadge={showBadges}
            className={itemClassName}
            onClick={onItemClick}
          />
        ))}
      </div>
    </div>
  );
};

/**
 * DynamicNavigation Component
 * 
 * Service-aware navigation that filters items based on user permissions
 */
export const DynamicNavigation: React.FC<DynamicNavigationProps> = ({
  variant = 'sidebar',
  showCategories = true,
  showDescriptions = false,
  showBadges = true,
  className,
  itemClassName,
  categoryClassName,
  onItemClick
}) => {
  const { hasAccess, isLoading } = useServiceAccess();
  const permissions = useServicePermissions();

  // Filter navigation items based on user permissions
  const getVisibleItems = (): NavItem[] => {
    return navigationItems.filter(item => {
      // Always show items with 'any' service
      if (item.service === 'any') return true;
      
      // Check service access
      return hasAccess(item.service, item.level || 'read');
    });
  };

  // Group visible items by category
  const getItemsByCategory = () => {
    const visibleItems = getVisibleItems();
    const categorized: Record<string, NavItem[]> = {};

    navigationCategories.forEach(category => {
      const categoryItems = visibleItems.filter(item => item.category === category.id);
      if (categoryItems.length > 0) {
        categorized[category.id] = categoryItems;
      }
    });

    return categorized;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const itemsByCategory = getItemsByCategory();
  const visibleItems = getVisibleItems();

  // Render based on variant
  if (variant === 'horizontal') {
    return (
      <nav className={cn("flex items-center space-x-6", className)}>
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const router = useRouter();
          const isActive = router.pathname === item.href || router.pathname.startsWith(`${item.href}/`);
          
          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={() => onItemClick?.(item)}
              className={cn(
                "flex items-center space-x-2 px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive 
                  ? "text-primary-600 bg-primary-50" 
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-50",
                itemClassName
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
              {showBadges && (item.badge || item.isNew || item.isBeta) && (
                <div className="flex space-x-1">
                  {item.badge && <Badge variant="secondary" className="text-xs">{item.badge}</Badge>}
                  {item.isNew && <Badge variant="success" className="text-xs">New</Badge>}
                  {item.isBeta && <Badge variant="warning" className="text-xs">Beta</Badge>}
                </div>
              )}
            </Link>
          );
        })}
      </nav>
    );
  }

  if (variant === 'dropdown') {
    return (
      <div className={cn("py-2", className)}>
        {visibleItems.map((item) => {
          const Icon = item.icon;
          
          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={() => onItemClick?.(item)}
              className={cn(
                "flex items-center space-x-3 px-4 py-2 text-sm hover:bg-gray-50 transition-colors",
                itemClassName
              )}
            >
              <Icon className="h-4 w-4 text-gray-500" />
              <div className="flex-1">
                <div className="font-medium text-gray-900">{item.label}</div>
                {showDescriptions && item.description && (
                  <div className="text-sm text-gray-500">{item.description}</div>
                )}
              </div>
              {showBadges && (item.badge || item.isNew || item.isBeta) && (
                <div className="flex space-x-1">
                  {item.badge && <Badge variant="secondary" className="text-xs">{item.badge}</Badge>}
                  {item.isNew && <Badge variant="success" className="text-xs">New</Badge>}
                  {item.isBeta && <Badge variant="warning" className="text-xs">Beta</Badge>}
                </div>
              )}
            </Link>
          );
        })}
      </div>
    );
  }

  // Default sidebar variant
  return (
    <nav className={cn("space-y-6", className)}>
      {showCategories ? (
        // Categorized navigation
        navigationCategories.map(category => {
          const categoryItems = itemsByCategory[category.id];
          if (!categoryItems) return null;

          return (
            <CategorySection
              key={category.id}
              categoryId={category.id}
              items={categoryItems}
              showDescriptions={showDescriptions}
              showBadges={showBadges}
              itemClassName={itemClassName}
              categoryClassName={categoryClassName}
              onItemClick={onItemClick}
            />
          );
        })
      ) : (
        // Flat navigation
        <div className="space-y-2">
          {visibleItems.map((item) => {
            const router = useRouter();
            const isActive = router.pathname === item.href || router.pathname.startsWith(`${item.href}/`);
            
            return (
              <NavigationItem
                key={item.id}
                item={item}
                isActive={isActive}
                showDescription={showDescriptions}
                showBadge={showBadges}
                className={itemClassName}
                onClick={onItemClick}
              />
            );
          })}
        </div>
      )}

      {/* Empty state */}
      {visibleItems.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500 text-sm">
            No navigation items available
          </div>
          <div className="text-gray-400 text-xs mt-1">
            Contact your administrator for access
          </div>
        </div>
      )}
    </nav>
  );
};

export default DynamicNavigation;
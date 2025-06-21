/**
 * Activity Feed Component
 * 
 * Features:
 * - Real-time activity timeline
 * - Mobile-first responsive design  
 * - Smooth animations and micro-interactions
 * - Pull-to-refresh support
 * - Infinite scrolling capability
 * - Activity type icons and color coding
 * - Relative time formatting
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  FileText, 
  Users, 
  Link as LinkIcon,
  Zap,
  Shield,
  ChevronDown,
  RefreshCw,
  Filter
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';

// Activity types and their configurations
export interface ActivityItem {
  id: string;
  type: 'invoice_generated' | 'integration_sync' | 'user_action' | 'system_event' | 'error' | 'submission';
  title: string;
  description?: string;
  timestamp: Date;
  metadata?: {
    user?: string;
    integration?: string;
    count?: number;
    status?: 'success' | 'error' | 'warning' | 'info';
    [key: string]: any;
  };
}

interface ActivityFeedProps {
  activities: ActivityItem[];
  loading?: boolean;
  onRefresh?: () => Promise<void>;
  onLoadMore?: () => Promise<void>;
  hasMore?: boolean;
  className?: string;
  maxHeight?: string;
  showFilter?: boolean;
}

// Activity type configurations
const ACTIVITY_CONFIG = {
  invoice_generated: {
    icon: FileText,
    color: 'text-primary',
    bgColor: 'bg-primary/10',
    label: 'Invoice'
  },
  integration_sync: {
    icon: LinkIcon,
    color: 'text-info',
    bgColor: 'bg-info/10',
    label: 'Integration'
  },
  user_action: {
    icon: Users,
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    label: 'User'
  },
  system_event: {
    icon: Zap,
    color: 'text-success',
    bgColor: 'bg-success/10',
    label: 'System'
  },
  error: {
    icon: AlertCircle,
    color: 'text-error',
    bgColor: 'bg-error/10',
    label: 'Error'
  },
  submission: {
    icon: Shield,
    color: 'text-primary',
    bgColor: 'bg-primary/10',
    label: 'Submission'
  }
};

// Format relative time
const formatRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
};

// Individual activity item component
const ActivityItem: React.FC<{ 
  activity: ActivityItem; 
  isLast: boolean;
}> = ({ activity, isLast }) => {
  const config = ACTIVITY_CONFIG[activity.type];
  const IconComponent = config.icon;

  return (
    <div className="relative flex gap-3 group">
      {/* Timeline line */}
      {!isLast && (
        <div className="absolute left-5 top-10 w-0.5 h-full bg-gray-200 group-hover:bg-gray-300 transition-colors" />
      )}
      
      {/* Icon container */}
      <div className={cn(
        "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 group-hover:scale-110",
        config.bgColor
      )}>
        <IconComponent className={cn("w-5 h-5", config.color)} />
      </div>
      
      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-text-primary text-sm xs:text-base truncate group-hover:text-primary transition-colors">
              {activity.title}
            </h4>
            
            {activity.description && (
              <p className="text-text-secondary text-xs xs:text-sm mt-1 line-clamp-2">
                {activity.description}
              </p>
            )}
            
            {/* Metadata */}
            {activity.metadata && (
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {activity.metadata.user && (
                  <Badge variant="secondary" className="text-xs">
                    {activity.metadata.user}
                  </Badge>
                )}
                
                {activity.metadata.integration && (
                  <Badge variant="outline" className="text-xs">
                    {activity.metadata.integration}
                  </Badge>
                )}
                
                {activity.metadata.count && (
                  <Badge variant="primary" className="text-xs">
                    {activity.metadata.count} items
                  </Badge>
                )}
                
                {activity.metadata.status && (
                  <Badge 
                    variant={activity.metadata.status === 'success' ? 'success' : 
                            activity.metadata.status === 'error' ? 'error' : 'warning'} 
                    className="text-xs"
                  >
                    {activity.metadata.status}
                  </Badge>
                )}
              </div>
            )}
          </div>
          
          <div className="flex-shrink-0 text-xs text-text-secondary">
            {formatRelativeTime(activity.timestamp)}
          </div>
        </div>
      </div>
    </div>
  );
};

// Loading skeleton for activity items
const ActivitySkeleton: React.FC = () => (
  <div className="relative flex gap-3">
    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 animate-pulse" />
    <div className="flex-1 space-y-2">
      <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4" />
      <div className="h-3 bg-gray-200 rounded animate-pulse w-1/2" />
      <div className="flex gap-2">
        <div className="h-5 bg-gray-200 rounded animate-pulse w-16" />
        <div className="h-5 bg-gray-200 rounded animate-pulse w-20" />
      </div>
    </div>
  </div>
);

export const ActivityFeed: React.FC<ActivityFeedProps> = ({
  activities,
  loading = false,
  onRefresh,
  onLoadMore,
  hasMore = false,
  className = '',
  maxHeight = '400px',
  showFilter = false
}) => {
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [filterType, setFilterType] = useState<string>('all');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Filter activities
  const filteredActivities = filterType === 'all' 
    ? activities 
    : activities.filter(activity => activity.type === filterType);

  // Handle refresh
  const handleRefresh = async () => {
    if (!onRefresh || refreshing) return;
    
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };

  // Handle load more
  const handleLoadMore = async () => {
    if (!onLoadMore || loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    try {
      await onLoadMore();
    } finally {
      setLoadingMore(false);
    }
  };

  // Intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMore && !loadingMore) {
          handleLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    const loadMoreTrigger = document.getElementById('load-more-trigger');
    if (loadMoreTrigger) {
      observer.observe(loadMoreTrigger);
    }

    return () => observer.disconnect();
  }, [hasMore, loadingMore]);

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader 
        title="Recent Activity" 
        subtitle="Latest system events and user actions"
        action={
          <div className="flex items-center gap-2">
            {showFilter && (
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary/20"
              >
                <option value="all">All</option>
                {Object.entries(ACTIVITY_CONFIG).map(([type, config]) => (
                  <option key={type} value={type}>
                    {config.label}
                  </option>
                ))}
              </select>
            )}
            
            {onRefresh && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
                className="min-w-0"
              >
                <RefreshCw className={cn(
                  "w-4 h-4",
                  refreshing ? "animate-spin" : ""
                )} />
                <span className="hidden xs:inline ml-2">Refresh</span>
              </Button>
            )}
          </div>
        }
      />
      
      <CardContent className="p-0">
        <div 
          ref={scrollRef}
          className="max-h-96 overflow-y-auto"
          style={{ maxHeight }}
        >
          {loading && activities.length === 0 ? (
            <div className="p-6 space-y-4">
              {[...Array(3)].map((_, index) => (
                <ActivitySkeleton key={index} />
              ))}
            </div>
          ) : filteredActivities.length > 0 ? (
            <div className="p-6">
              {filteredActivities.map((activity, index) => (
                <ActivityItem
                  key={activity.id}
                  activity={activity}
                  isLast={index === filteredActivities.length - 1}
                />
              ))}
              
              {/* Load more trigger */}
              {hasMore && (
                <div id="load-more-trigger" className="flex justify-center pt-4">
                  {loadingMore ? (
                    <div className="flex items-center gap-2 text-text-secondary">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Loading more...</span>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleLoadMore}
                      className="text-sm"
                    >
                      <ChevronDown className="w-4 h-4 mr-2" />
                      Load More
                    </Button>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 text-center text-text-secondary">
              <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No recent activity</p>
              {filterType !== 'all' && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFilterType('all')}
                  className="mt-2 text-xs"
                >
                  Clear filter
                </Button>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ActivityFeed;
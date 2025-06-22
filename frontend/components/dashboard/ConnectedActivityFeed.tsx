/**
 * Connected Activity Feed Component
 * 
 * A wrapper around the ActivityFeed component that handles:
 * - Data fetching from the backend API
 * - Real-time updates with polling
 * - Pagination and infinite scroll
 * - Error handling and retry logic
 * - Integration with authentication context
 */

import React, { useState, useEffect, useCallback } from 'react';
import { ActivityFeed, ActivityItem } from './ActivityFeed';
import { fetchActivities, ActivitiesResponse } from '@/services/dashboardService';
import { useAuth } from '@/hooks/useAuth';
import { useApiPolling } from '@/hooks/useApiPolling';

interface ConnectedActivityFeedProps {
  className?: string;
  maxHeight?: string;
  showFilter?: boolean;
  pollInterval?: number; // Polling interval in milliseconds
  pageSize?: number; // Number of activities per page
  activityType?: string; // Filter by activity type
}

export const ConnectedActivityFeed: React.FC<ConnectedActivityFeedProps> = ({
  className = '',
  maxHeight = '400px',
  showFilter = true,
  pollInterval = 30000, // 30 seconds default
  pageSize = 20,
  activityType
}) => {
  const { organization } = useAuth();
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);

  // Fetch activities function
  const fetchActivityData = useCallback(async (reset: boolean = false) => {
    try {
      const currentOffset = reset ? 0 : offset;
      
      const response: ActivitiesResponse = await fetchActivities(
        pageSize,
        currentOffset,
        activityType,
        organization?.id
      );

      if (reset) {
        setActivities(response.activities);
        setOffset(pageSize);
      } else {
        setActivities(prev => [...prev, ...response.activities]);
        setOffset(prev => prev + pageSize);
      }

      setHasMore(response.activities.length === pageSize);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch activities:', err);
      setError(err.message || 'Failed to load activities');
    } finally {
      setLoading(false);
    }
  }, [pageSize, offset, activityType, organization?.id]);

  // Initial load
  useEffect(() => {
    setLoading(true);
    setOffset(0);
    fetchActivityData(true);
  }, [organization?.id, activityType]);

  // Set up polling for real-time updates
  const { 
    startPolling, 
    stopPolling, 
    isPolling, 
    refresh: manualRefresh 
  } = useApiPolling(
    () => fetchActivityData(true),
    pollInterval,
    !!organization?.id // Only poll if we have an organization
  );

  // Start polling when component mounts
  useEffect(() => {
    if (organization?.id) {
      startPolling();
    }
    
    return () => {
      stopPolling();
    };
  }, [organization?.id, startPolling, stopPolling]);

  // Handle refresh
  const handleRefresh = useCallback(async () => {
    setOffset(0);
    await fetchActivityData(true);
  }, [fetchActivityData]);

  // Handle load more
  const handleLoadMore = useCallback(async () => {
    if (!hasMore || loading) return;
    await fetchActivityData(false);
  }, [fetchActivityData, hasMore, loading]);

  // Handle retry on error
  const handleRetry = useCallback(() => {
    setError(null);
    setLoading(true);
    setOffset(0);
    fetchActivityData(true);
  }, [fetchActivityData]);

  // Show error state
  if (error && activities.length === 0) {
    return (
      <div className={`border rounded-lg p-6 text-center ${className}`}>
        <div className="text-red-500 mb-2">Failed to load activities</div>
        <div className="text-sm text-gray-600 mb-4">{error}</div>
        <button
          onClick={handleRetry}
          className="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className={className}>
      {/* Polling indicator */}
      {isPolling && (
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Live updates enabled
        </div>
      )}

      {/* Error banner for partial failures */}
      {error && activities.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
          <div className="text-sm text-yellow-800">
            Failed to load latest activities: {error}
          </div>
          <button
            onClick={handleRetry}
            className="text-xs text-yellow-600 hover:text-yellow-800 underline mt-1"
          >
            Try again
          </button>
        </div>
      )}

      {/* Activity Feed Component */}
      <ActivityFeed
        activities={activities}
        loading={loading}
        onRefresh={handleRefresh}
        onLoadMore={handleLoadMore}
        hasMore={hasMore}
        maxHeight={maxHeight}
        showFilter={showFilter}
      />

      {/* Loading more indicator */}
      {!loading && hasMore && (
        <div className="text-center py-4">
          <button
            onClick={handleLoadMore}
            className="text-sm text-primary hover:text-primary/80 underline"
          >
            Load more activities
          </button>
        </div>
      )}
    </div>
  );
};

export default ConnectedActivityFeed;
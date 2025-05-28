import { useState, useEffect, useRef, useCallback } from 'react';

interface PollingOptions<T> {
  // The function that fetches data from the API
  fetchFunction: () => Promise<T>;
  // Polling interval in milliseconds (defaults to 30 seconds)
  interval?: number;
  // Should polling start immediately? (defaults to true)
  startImmediately?: boolean;
  // Should the hook refetch when component mounts? (defaults to true)
  fetchOnMount?: boolean;
  // Optional predicate to determine if polling should stop
  stopPollingWhen?: (data: T) => boolean;
  // Error handling function
  onError?: (error: any) => void;
}

/**
 * Custom hook for polling an API endpoint at regular intervals
 * Useful for monitoring integration status or sync operations
 */
export function useApiPolling<T>({
  fetchFunction,
  interval = 30000,
  startImmediately = true,
  fetchOnMount = true,
  stopPollingWhen,
  onError
}: PollingOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [isPolling, setIsPolling] = useState<boolean>(startImmediately);
  
  // Use refs to avoid dependency issues with the interval
  const pollingRef = useRef<boolean>(startImmediately);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Function to fetch data
  const fetchData = useCallback(async () => {
    if (!pollingRef.current) return;
    
    setLoading(true);
    try {
      const result = await fetchFunction();
      setData(result);
      setError(null);
      
      // Check if we should stop polling based on the data
      if (stopPollingWhen && stopPollingWhen(result)) {
        setIsPolling(false);
        pollingRef.current = false;
      }
    } catch (err: any) {
      setError(err);
      if (onError) onError(err);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, stopPollingWhen, onError]);
  
  // Function to start polling
  const startPolling = useCallback(() => {
    setIsPolling(true);
    pollingRef.current = true;
    // Fetch immediately when starting
    fetchData();
  }, [fetchData]);
  
  // Function to stop polling
  const stopPolling = useCallback(() => {
    setIsPolling(false);
    pollingRef.current = false;
    // Clear any pending timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);
  
  // Manual trigger for fetching data (useful for refresh buttons)
  const refetch = useCallback(() => {
    return fetchData();
  }, [fetchData]);
  
  // Set up the polling interval
  useEffect(() => {
    // Fetch on mount if enabled
    if (fetchOnMount) {
      fetchData();
    }
    
    // Function that schedules the next poll
    const poll = async () => {
      if (!pollingRef.current) return;
      
      await fetchData();
      
      // Schedule the next poll if still polling
      if (pollingRef.current) {
        timeoutRef.current = setTimeout(poll, interval);
      }
    };
    
    // Start polling if enabled
    if (startImmediately) {
      timeoutRef.current = setTimeout(poll, interval);
    }
    
    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [fetchData, interval, startImmediately, fetchOnMount]);
  
  return {
    data,
    loading,
    error,
    isPolling,
    startPolling,
    stopPolling,
    refetch
  };
}

import { renderHook, act, waitFor } from '@testing-library/react';
import { useApiPolling } from '../useApiPolling';

// Define interfaces for our test data
interface TestData {
  data?: string;
  status?: string;
}

// Mock timers for testing polling
jest.useFakeTimers();

describe('useApiPolling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  afterEach(() => {
    jest.clearAllTimers();
  });
  
  test('should fetch data on mount when fetchOnMount is true', async () => {
    const mockFetchFunction = jest.fn().mockResolvedValue({ data: 'test data' } as TestData);
    
    renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      fetchOnMount: true
    }));
    
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
  });
  
  test('should not fetch data on mount when fetchOnMount is false', () => {
    const mockFetchFunction = jest.fn().mockResolvedValue({ data: 'test data' } as TestData);
    
    renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      fetchOnMount: false
    }));
    
    expect(mockFetchFunction).not.toHaveBeenCalled();
  });
  
  test('should start polling when startImmediately is true', () => {
    const mockFetchFunction = jest.fn().mockResolvedValue({ data: 'test data' } as TestData);
    
    renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      startImmediately: true
    }));
    
    // Initial fetch
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
    
    // Fast-forward time by interval
    jest.advanceTimersByTime(5000);
    
    // Should fetch again after interval
    expect(mockFetchFunction).toHaveBeenCalledTimes(2);
  });
  
  test('should not start polling when startImmediately is false', () => {
    const mockFetchFunction = jest.fn().mockResolvedValue({ data: 'test data' } as TestData);
    
    renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      startImmediately: false,
      fetchOnMount: true // Still fetch on mount
    }));
    
    // Initial fetch on mount
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
    
    // Fast-forward time by interval
    jest.advanceTimersByTime(5000);
    
    // Should not fetch again as polling is not started
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
  });
  
  test('should stop polling when condition is met', async () => {
    // Mock fetch function that will satisfy the condition on second call
    const mockFetchFunction = jest.fn()
      .mockResolvedValueOnce({ status: 'syncing' } as TestData)
      .mockResolvedValueOnce({ status: 'configured' } as TestData);
    
    const { result } = renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      stopPollingWhen: (data) => data?.status === 'configured'
    }));
    
    // Initial fetch
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
    
    // Fast-forward time by interval
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    // Should fetch again after interval
    expect(mockFetchFunction).toHaveBeenCalledTimes(2);
    
    // Polling should have stopped due to condition
    await waitFor(() => {
      expect(result.current.isPolling).toBe(false);
    });
    
    // Fast-forward time by another interval
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    // Should not fetch again as polling is stopped
    expect(mockFetchFunction).toHaveBeenCalledTimes(2);
  });
  
  test('should call onError when fetch fails', async () => {
    const mockError = new Error('Test error');
    const mockFetchFunction = jest.fn().mockRejectedValue(mockError);
    const mockOnError = jest.fn();
    
    renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      onError: mockOnError
    }));
    
    // Wait for error handling
    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(mockError);
    });
  });
  
  test('startPolling and stopPolling functions work correctly', () => {
    const mockFetchFunction = jest.fn().mockResolvedValue({ data: 'test data' } as TestData);
    
    const { result } = renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      startImmediately: false,
      fetchOnMount: false
    }));
    
    // Initially, no fetch should happen
    expect(mockFetchFunction).not.toHaveBeenCalled();
    
    // Start polling manually
    act(() => {
      result.current.startPolling();
    });
    
    // Should fetch immediately when starting
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
    
    // Fast-forward time by interval
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    // Should fetch again after interval
    expect(mockFetchFunction).toHaveBeenCalledTimes(2);
    
    // Stop polling manually
    act(() => {
      result.current.stopPolling();
    });
    
    // Fast-forward time by another interval
    act(() => {
      jest.advanceTimersByTime(5000);
    });
    
    // Should not fetch again as polling is stopped
    expect(mockFetchFunction).toHaveBeenCalledTimes(2);
  });
  
  test('refetch function works correctly', async () => {
    const mockFetchFunction = jest.fn().mockResolvedValue({ data: 'test data' } as TestData);
    
    const { result } = renderHook(() => useApiPolling<TestData>({
      fetchFunction: mockFetchFunction,
      interval: 5000,
      startImmediately: false,
      fetchOnMount: false
    }));
    
    // Initially, no fetch should happen
    expect(mockFetchFunction).not.toHaveBeenCalled();
    
    // Call refetch manually
    act(() => {
      result.current.refetch();
    });
    
    // Should fetch immediately
    expect(mockFetchFunction).toHaveBeenCalledTimes(1);
  });
});

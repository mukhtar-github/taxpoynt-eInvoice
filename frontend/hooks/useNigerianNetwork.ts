/**
 * Nigerian Network Adaptation Hook
 * Detects and adapts to Nigerian mobile network conditions
 */

import { useState, useEffect, useCallback } from 'react';
import { NetworkDetection } from '../config/nigerian-pwa.config';

interface NetworkState {
  effectiveType: string;
  downlink: number;
  rtt: number;
  saveData: boolean;
  isSlowConnection: boolean;
  isOffline: boolean;
  carrier: string | null;
}

interface NetworkAdaptation {
  shouldReduceImages: boolean;
  shouldPrefetch: boolean;
  shouldShowDataSaverNotice: boolean;
  recommendedImageQuality: 'low' | 'medium' | 'high';
  maxConcurrentRequests: number;
}

export const useNigerianNetwork = () => {
  const [networkState, setNetworkState] = useState<NetworkState>({
    effectiveType: 'unknown',
    downlink: 0,
    rtt: 0,
    saveData: false,
    isSlowConnection: false,
    isOffline: false,
    carrier: null
  });

  const [adaptation, setAdaptation] = useState<NetworkAdaptation>({
    shouldReduceImages: false,
    shouldPrefetch: true,
    shouldShowDataSaverNotice: false,
    recommendedImageQuality: 'high',
    maxConcurrentRequests: 6
  });

  // Detect Nigerian mobile carriers based on connection patterns
  const detectCarrier = useCallback((): string | null => {
    // This is a simplified carrier detection
    // In production, you might use more sophisticated methods
    const userAgent = navigator.userAgent.toLowerCase();
    const connection = NetworkDetection.getConnectionInfo();
    
    // MTN typically has specific RTT patterns
    if (connection.rtt > 100 && connection.rtt < 300) {
      return 'MTN';
    }
    // Airtel often has different downlink characteristics
    else if (connection.downlink > 0.5 && connection.downlink < 2) {
      return 'Airtel';
    }
    // Glo has specific network signatures
    else if (connection.rtt > 200) {
      return 'Glo';  
    }
    // 9mobile (Etisalat) patterns
    else if (connection.downlink < 1 && connection.rtt > 150) {
      return '9mobile';
    }
    
    return null;
  }, []);

  // Calculate network adaptations based on current conditions
  const calculateAdaptations = useCallback((network: NetworkState): NetworkAdaptation => {
    const isSlowOrSaveData = network.isSlowConnection || network.saveData;
    
    return {
      shouldReduceImages: isSlowOrSaveData,
      shouldPrefetch: !isSlowOrSaveData && !network.isOffline,
      shouldShowDataSaverNotice: network.saveData,
      recommendedImageQuality: isSlowOrSaveData ? 'low' : 
                              network.effectiveType === '3g' ? 'medium' : 'high',
      maxConcurrentRequests: isSlowOrSaveData ? 2 : 
                            network.effectiveType === '3g' ? 4 : 6
    };
  }, []);

  // Update network state
  const updateNetworkState = useCallback(() => {
    const connectionInfo = NetworkDetection.getConnectionInfo();
    const isSlowConnection = NetworkDetection.isSlowConnection();
    const isOffline = !navigator.onLine;
    const carrier = detectCarrier();

    const newState: NetworkState = {
      ...connectionInfo,
      isSlowConnection,
      isOffline,
      carrier
    };

    setNetworkState(newState);
    setAdaptation(calculateAdaptations(newState));
  }, [detectCarrier, calculateAdaptations]);

  // Initialize and set up listeners
  useEffect(() => {
    updateNetworkState();

    // Listen for connection changes
    const handleOnline = () => updateNetworkState();
    const handleOffline = () => updateNetworkState();
    const handleConnectionChange = () => updateNetworkState();

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    // Listen for connection API changes
    if ('connection' in navigator) {
      (navigator as any).connection.addEventListener('change', handleConnectionChange);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if ('connection' in navigator) {
        (navigator as any).connection.removeEventListener('change', handleConnectionChange);
      }
    };
  }, [updateNetworkState]);

  // Utility functions for Nigerian-specific optimizations
  const nigerianOptimizations = {
    /**
     * Get optimized image URL based on current network
     */
    getOptimizedImageUrl: (baseUrl: string): string => {
      const quality = adaptation.recommendedImageQuality;
      const qualityParam = quality === 'low' ? 'q_30' : 
                          quality === 'medium' ? 'q_60' : 'q_80';
      
      // If using a CDN like Cloudinary, append quality parameters
      if (baseUrl.includes('cloudinary.com')) {
        return baseUrl.replace('/upload/', `/upload/${qualityParam}/`);
      }
      
      return baseUrl;
    },

    /**
     * Check if we should load heavy components
     */
    shouldLoadHeavyComponents: (): boolean => {
      return !adaptation.shouldReduceImages && !networkState.isSlowConnection;
    },

    /**
     * Get recommended timeout for API calls
     */
    getRecommendedTimeout: (): number => {
      if (networkState.isSlowConnection) return 30000; // 30 seconds
      if (networkState.effectiveType === '3g') return 15000; // 15 seconds
      return 10000; // 10 seconds for 4G+
    },

    /**
     * Check if carrier-specific optimizations should be applied
     */
    shouldApplyCarrierOptimizations: (carrier: string): boolean => {
      return networkState.carrier === carrier;
    }
  };

  return {
    networkState,
    adaptation,
    nigerianOptimizations,
    refreshNetworkState: updateNetworkState
  };
};

export default useNigerianNetwork;
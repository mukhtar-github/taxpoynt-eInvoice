/**
 * Nigerian PWA Configuration
 * Optimized for Nigerian mobile infrastructure and network conditions
 */

export interface NigerianNetworkConfig {
  bandwidth_detection: boolean;
  connection_aware_loading: boolean;
  fallback_2g_mode: boolean;
  data_saver_mode: boolean;
}

export interface NigerianCarrierOptimization {
  mtn_optimization: boolean;
  airtel_optimization: boolean;
  glo_optimization: boolean;
  etisalat_optimization: boolean;
}

export interface OfflineCapabilities {
  cache_strategy: 'cache_first' | 'network_first' | 'stale_while_revalidate';
  offline_pages: string[];
  data_sync_on_reconnect: boolean;
}

export interface PerformanceOptimization {
  image_compression: 'aggressive' | 'moderate' | 'conservative';
  bundle_splitting: 'route_based' | 'component_based' | 'custom';
  lazy_loading: 'viewport_based' | 'intersection_based' | 'manual';
  prefetch_critical_resources: boolean;
}

export const NigerianPWAConfig = {
  offline_capabilities: {
    cache_strategy: 'cache_first' as const,
    offline_pages: ['/dashboard', '/invoices', '/compliance', '/integrations'],
    data_sync_on_reconnect: true
  } as OfflineCapabilities,
  
  performance_optimization: {
    image_compression: 'aggressive' as const,
    bundle_splitting: 'route_based' as const,
    lazy_loading: 'viewport_based' as const,
    prefetch_critical_resources: true
  } as PerformanceOptimization,
  
  network_adaptation: {
    bandwidth_detection: true,
    connection_aware_loading: true,
    fallback_2g_mode: true,
    data_saver_mode: true
  } as NigerianNetworkConfig,
  
  nigerian_specific: {
    mtn_optimization: true,
    airtel_optimization: true,
    glo_optimization: true,
    etisalat_optimization: true
  } as NigerianCarrierOptimization
};

// Mobile-first responsive design optimized for Nigerian usage patterns
export const NigerianMobileTheme = {
  breakpoints: {
    mobile: '320px',    // Basic smartphones (most common in Nigeria)
    tablet: '768px',    // Tablets and larger phones
    desktop: '1024px'   // Desktop/laptop
  },
  
  touch_targets: {
    minimum_size: '44px',  // Nigerian finger-friendly touch targets
    spacing: '8px',        // Adequate spacing for accurate taps
    hover_area: '48px'     // Extended hover area for better UX
  },
  
  typography: {
    scale_factor: 1.2,     // Larger text for better readability on mobile
    line_height: 1.6,      // Improved readability
    base_font_size: '16px' // Prevent zoom on iOS
  },
  
  colors: {
    // High contrast for outdoor visibility (common in Nigeria)
    primary: '#16a34a',    // Nigerian green
    secondary: '#dc2626',  // Alert red
    background: '#ffffff', // High contrast white
    text: '#1f2937'       // Dark gray for readability
  }
};

// Network detection utilities
export const NetworkDetection = {
  /**
   * Detect current network conditions
   */
  getConnectionInfo(): {
    effectiveType: string;
    downlink: number;
    rtt: number;
    saveData: boolean;
  } {
    if ('connection' in navigator) {
      const connection = (navigator as any).connection;
      return {
        effectiveType: connection.effectiveType || 'unknown',
        downlink: connection.downlink || 0,
        rtt: connection.rtt || 0,
        saveData: connection.saveData || false
      };
    }
    
    // Fallback for browsers without connection API
    return {
      effectiveType: 'unknown',
      downlink: 0,
      rtt: 0,
      saveData: false
    };
  },
  
  /**
   * Check if connection is slow (2G/slow 3G)
   */
  isSlowConnection(): boolean {
    const connection = this.getConnectionInfo();
    return connection.effectiveType === '2g' || 
           connection.effectiveType === 'slow-2g' ||
           (connection.downlink > 0 && connection.downlink < 0.5);
  },
  
  /**
   * Check if user has data saver enabled
   */
  isDataSaverEnabled(): boolean {
    return this.getConnectionInfo().saveData;
  }
};

// PWA manifest configuration for Nigerian context
export const NigerianPWAManifest = {
  name: "TaxPoynt E-Invoice Platform",
  short_name: "TaxPoynt",
  description: "Nigerian FIRS-compliant e-invoicing platform",
  start_url: "/dashboard",
  display: "standalone",
  background_color: "#ffffff",
  theme_color: "#16a34a",
  orientation: "portrait-primary",
  scope: "/",
  icons: [
    {
      src: "/icons/icon-192x192.png",
      sizes: "192x192",
      type: "image/png",
      purpose: "maskable"
    },
    {
      src: "/icons/icon-512x512.png", 
      sizes: "512x512",
      type: "image/png",
      purpose: "any"
    }
  ],
  categories: ["business", "finance", "productivity"],
  lang: "en-NG",
  dir: "ltr",
  shortcuts: [
    {
      name: "Create Invoice",
      short_name: "Invoice",
      description: "Create new FIRS-compliant invoice",
      url: "/invoices/new",
      icons: [{ src: "/icons/invoice-icon.png", sizes: "96x96" }]
    },
    {
      name: "Dashboard",
      short_name: "Dashboard", 
      description: "View business metrics",
      url: "/dashboard",
      icons: [{ src: "/icons/dashboard-icon.png", sizes: "96x96" }]
    }
  ]
};

export default NigerianPWAConfig;
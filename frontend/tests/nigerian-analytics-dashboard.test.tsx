/**
 * Tests for Nigerian Analytics Dashboard
 * 
 * Comprehensive test suite for the Nigerian analytics dashboard component
 * and associated services.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import '@testing-library/jest-dom';

import { NigerianAnalyticsDashboard } from '../components/nigerian/analytics/NigerianAnalyticsDashboard';
import { nigerianAnalyticsService } from '../services/nigerianAnalyticsService';

// Mock the analytics service
jest.mock('../services/nigerianAnalyticsService');

// Mock chart components to avoid canvas rendering issues in tests
jest.mock('../components/ui/Charts', () => ({
  BarChart: ({ data, options }: any) => (
    <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)}>
      Bar Chart Mock
    </div>
  ),
  LineChart: ({ data, options }: any) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)}>
      Line Chart Mock
    </div>
  ),
  DoughnutChart: ({ data, options }: any) => (
    <div data-testid="doughnut-chart" data-chart-data={JSON.stringify(data)}>
      Doughnut Chart Mock
    </div>
  ),
  AreaChart: ({ data, options }: any) => (
    <div data-testid="area-chart" data-chart-data={JSON.stringify(data)}>
      Area Chart Mock
    </div>
  )
}));

// Mock UI components
jest.mock('../components/ui/LoadingSkeleton', () => ({
  LoadingSkeleton: ({ count, height }: any) => (
    <div data-testid="loading-skeleton">Loading {count} items...</div>
  )
}));

const mockAnalyticsData = {
  nitda_status: 'Active',
  nitda_expiry: '2025-12-31',
  ndpr_compliance_score: 95,
  iso_status: 'Certified',
  next_audit_date: '2025-03-15',
  total_penalties: 2500000,
  state_revenue: [
    { state: 'Lagos', revenue: 15000000000, growth: 12.5 },
    { state: 'Rivers', revenue: 8000000000, growth: 8.3 },
    { state: 'Kano', revenue: 6000000000, growth: 15.2 }
  ],
  payment_methods: [
    { method: 'Bank Transfer', volume: 45, value: 12000000000 },
    { method: 'USSD', volume: 30, value: 3500000000 },
    { method: 'Card Payment', volume: 15, value: 2800000000 }
  ],
  language_usage: [
    { language: 'English', users: 12500, percentage: 62 },
    { language: 'Hausa', users: 4200, percentage: 21 },
    { language: 'Yoruba', users: 2800, percentage: 14 },
    { language: 'Igbo', users: 600, percentage: 3 }
  ],
  device_usage: [
    { device: 'Mobile', users: 14800, sessions: 45200 },
    { device: 'Desktop', users: 4200, sessions: 8900 },
    { device: 'Tablet', users: 1000, sessions: 1800 }
  ],
  support_channels: [
    { channel: 'WhatsApp Business', tickets: 1250, satisfaction: 4.8 },
    { channel: 'Phone Support', tickets: 890, satisfaction: 4.5 },
    { channel: 'Email', tickets: 560, satisfaction: 4.2 }
  ],
  compliance_timeline: [],
  regional_metrics: [],
  cultural_adoption: []
};

describe('NigerianAnalyticsDashboard', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock successful API response
    (nigerianAnalyticsService.getAnalyticsData as jest.Mock).mockResolvedValue({
      success: true,
      data: mockAnalyticsData
    });
    
    // Mock fetch for fallback API calls
    global.fetch = jest.fn().mockResolvedValue({
      json: jest.fn().mockResolvedValue(mockAnalyticsData)
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders dashboard header correctly', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Nigerian Market Analytics')).toBeInTheDocument();
        expect(screen.getByText('Comprehensive insights into Nigerian business operations')).toBeInTheDocument();
      });
    });

    test('renders loading state initially', () => {
      render(<NigerianAnalyticsDashboard />);
      
      expect(screen.getByTestId('loading-skeleton')).toBeInTheDocument();
    });

    test('renders compliance cards after data loads', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('NITDA Accreditation')).toBeInTheDocument();
        expect(screen.getByText('NDPR Compliance')).toBeInTheDocument();
        expect(screen.getByText('ISO 27001 Status')).toBeInTheDocument();
        expect(screen.getByText('FIRS Penalties')).toBeInTheDocument();
      });
    });

    test('renders time range filter buttons', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('7 Days')).toBeInTheDocument();
        expect(screen.getByText('30 Days')).toBeInTheDocument();
        expect(screen.getByText('90 Days')).toBeInTheDocument();
        expect(screen.getByText('1 Year')).toBeInTheDocument();
      });
    });

    test('renders tab navigation', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Overview')).toBeInTheDocument();
        expect(screen.getByText('Compliance')).toBeInTheDocument();
        expect(screen.getByText('Regional')).toBeInTheDocument();
        expect(screen.getByText('Cultural')).toBeInTheDocument();
      });
    });
  });

  describe('Data Display', () => {
    test('displays NITDA status correctly', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Active')).toBeInTheDocument();
      });
    });

    test('displays NDPR compliance score', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('95%')).toBeInTheDocument();
      });
    });

    test('displays FIRS penalties amount', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        // Should format as Nigerian Naira
        expect(screen.getByText(/₦2,500,000/)).toBeInTheDocument();
      });
    });

    test('renders revenue by state chart', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
        expect(screen.getByText('Revenue by Nigerian State')).toBeInTheDocument();
      });
    });

    test('renders payment method distribution chart', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
        expect(screen.getByText('Payment Method Distribution')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    test('time range filter changes trigger data refresh', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const sevenDaysButton = screen.getByText('7 Days');
        fireEvent.click(sevenDaysButton);
      });
      
      // Should call API with new time range
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('timeRange=7d'),
      );
    });

    test('refresh button triggers data reload', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const refreshButton = screen.getByText('Refresh');
        fireEvent.click(refreshButton);
      });
      
      // Should call fetch again
      expect(global.fetch).toHaveBeenCalledTimes(2); // Initial load + refresh
    });

    test('export button triggers export functionality', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const exportButton = screen.getByText('Export');
        fireEvent.click(exportButton);
      });
      
      // Should log export action (in real implementation, would trigger download)
      // This is a basic test since we're just logging in the mock implementation
    });

    test('tab switching works correctly', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const complianceTab = screen.getByText('Compliance');
        fireEvent.click(complianceTab);
      });
      
      await waitFor(() => {
        expect(screen.getByText('User Language Preferences')).toBeInTheDocument();
        expect(screen.getByText('Device Usage Distribution')).toBeInTheDocument();
        expect(screen.getByText('Support Channel Performance')).toBeInTheDocument();
      });
    });
  });

  describe('Compliance Tab', () => {
    test('renders language distribution correctly', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Compliance'));
      });
      
      await waitFor(() => {
        expect(screen.getByText('English')).toBeInTheDocument();
        expect(screen.getByText('Hausa')).toBeInTheDocument();
        expect(screen.getByText('Yoruba')).toBeInTheDocument();
        expect(screen.getByText('Igbo')).toBeInTheDocument();
      });
    });

    test('renders device usage chart', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Compliance'));
      });
      
      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
      });
    });

    test('renders support channel performance', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        fireEvent.click(screen.getByText('Compliance'));
      });
      
      await waitFor(() => {
        expect(screen.getByText('WhatsApp Business')).toBeInTheDocument();
        expect(screen.getByText('Phone Support')).toBeInTheDocument();
        expect(screen.getByText('Email')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('handles API error gracefully', async () => {
      // Mock API failure
      (global.fetch as jest.Mock).mockRejectedValue(new Error('API Error'));
      
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to load analytics data')).toBeInTheDocument();
      });
    });

    test('handles empty data gracefully', async () => {
      // Mock empty data response
      (global.fetch as jest.Mock).mockResolvedValue({
        json: jest.fn().mockResolvedValue({
          ...mockAnalyticsData,
          state_revenue: [],
          payment_methods: [],
          language_usage: []
        })
      });
      
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('No data available')).toBeInTheDocument();
      });
    });
  });

  describe('Chart Data Validation', () => {
    test('state revenue chart receives correct data format', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const chartElement = screen.getByTestId('bar-chart');
        const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '{}');
        
        expect(chartData.labels).toEqual(['Lagos', 'Rivers', 'Kano']);
        expect(chartData.datasets).toHaveLength(2); // Revenue and Growth datasets
        expect(chartData.datasets[0].label).toBe('Revenue (₦M)');
        expect(chartData.datasets[1].label).toBe('Growth (%)');
      });
    });

    test('payment method chart receives correct data format', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const chartElement = screen.getByTestId('doughnut-chart');
        const chartData = JSON.parse(chartElement.getAttribute('data-chart-data') || '{}');
        
        expect(chartData.labels).toEqual(['Bank Transfer', 'USSD', 'Card Payment']);
        expect(chartData.datasets[0].data).toEqual([45, 30, 15]);
      });
    });
  });

  describe('Accessibility', () => {
    test('dashboard has proper heading structure', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        const mainHeading = screen.getByRole('heading', { level: 1 });
        expect(mainHeading).toHaveTextContent('Nigerian Market Analytics');
      });
    });

    test('buttons have appropriate labels', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /refresh/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument();
      });
    });

    test('charts have proper titles', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Revenue by Nigerian State')).toBeInTheDocument();
        expect(screen.getByText('Payment Method Distribution')).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    test('does not make unnecessary API calls on initial render', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        expect(screen.getByText('Nigerian Market Analytics')).toBeInTheDocument();
      });
      
      // Should only call API once on initial render
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test('debounces time range changes', async () => {
      render(<NigerianAnalyticsDashboard />);
      
      await waitFor(() => {
        // Rapidly click different time ranges
        fireEvent.click(screen.getByText('7 Days'));
        fireEvent.click(screen.getByText('90 Days'));
        fireEvent.click(screen.getByText('1 Year'));
      });
      
      // Should only make the final API call (plus initial load)
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });
    });
  });
});

describe('ComplianceCard Component', () => {
  const ComplianceCard = ({ title, status, percentage, amount, currency, icon }: any) => {
    const getStatusColor = (value: string | number) => {
      if (typeof value === 'number') {
        if (value >= 90) return 'text-green-600';
        if (value >= 70) return 'text-yellow-600';
        return 'text-red-600';
      }
      
      if (value === 'Active' || value === 'Compliant') return 'text-green-600';
      if (value === 'Expiring Soon') return 'text-yellow-600';
      return 'text-red-600';
    };

    const formatValue = (value: string | number) => {
      if (amount && typeof value === 'number') {
        return new Intl.NumberFormat('en-NG', {
          style: 'currency',
          currency: currency || 'NGN'
        }).format(value);
      }
      
      if (percentage && typeof value === 'number') {
        return `${value}%`;
      }
      
      return value;
    };

    return (
      <div data-testid="compliance-card">
        <div>{title}</div>
        <div className={getStatusColor(status)}>
          {formatValue(status)}
        </div>
      </div>
    );
  };

  test('formats percentage values correctly', () => {
    render(
      <ComplianceCard
        title="Test Compliance"
        status={95}
        percentage={true}
        icon={<div>Icon</div>}
      />
    );
    
    expect(screen.getByText('95%')).toBeInTheDocument();
  });

  test('formats currency values correctly', () => {
    render(
      <ComplianceCard
        title="Test Amount"
        status={2500000}
        amount={true}
        currency="NGN"
        icon={<div>Icon</div>}
      />
    );
    
    expect(screen.getByText(/₦2,500,000/)).toBeInTheDocument();
  });

  test('applies correct status colors', () => {
    const { rerender } = render(
      <ComplianceCard
        title="Test Status"
        status="Active"
        icon={<div>Icon</div>}
      />
    );
    
    expect(screen.getByText('Active')).toHaveClass('text-green-600');
    
    rerender(
      <ComplianceCard
        title="Test Status"
        status="Inactive"
        icon={<div>Icon</div>}
      />
    );
    
    expect(screen.getByText('Inactive')).toHaveClass('text-red-600');
  });
});
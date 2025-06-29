/**
 * Nigerian Analytics Service
 * 
 * Service for fetching and managing Nigerian market analytics data
 */

import { ApiResponse, apiClient } from './apiClient';

export interface NigerianAnalyticsData {
  nitda_status: string;
  nitda_expiry: string;
  ndpr_compliance_score: number;
  iso_status: string;
  next_audit_date: string;
  total_penalties: number;
  state_revenue: Array<{
    state: string;
    revenue: number;
    growth: number;
    region: string;
    compliance_rate: number;
  }>;
  payment_methods: Array<{
    method: string;
    volume: number;
    value: number;
    growth_rate: number;
  }>;
  language_usage: Array<{
    language: string;
    users: number;
    percentage: number;
    engagement_rate: number;
  }>;
  device_usage: Array<{
    device: string;
    users: number;
    sessions: number;
    bounce_rate: number;
  }>;
  support_channels: Array<{
    channel: string;
    tickets: number;
    satisfaction: number;
    response_time: number;
  }>;
  compliance_timeline: Array<{
    month: string;
    nitda: number;
    ndpr: number;
    iso: number;
    firs_penalties: number;
  }>;
  regional_metrics: Array<{
    region: string;
    businesses: number;
    transactions: number;
    compliance_rate: number;
    revenue: number;
  }>;
  cultural_adoption: Array<{
    feature: string;
    adoption_rate: number;
    satisfaction: number;
    usage_frequency: string;
  }>;
  penalty_trends: Array<{
    month: string;
    total_penalties: number;
    resolved_penalties: number;
    active_penalties: number;
  }>;
  business_metrics: {
    total_businesses: number;
    active_businesses: number;
    compliance_rate: number;
    average_transaction_value: number;
    monthly_growth_rate: number;
  };
}

export interface TimeRangeOptions {
  range: '7d' | '30d' | '90d' | '1y';
  start_date?: string;
  end_date?: string;
}

export interface AnalyticsFilters {
  state_codes?: string[];
  business_sectors?: string[];
  compliance_status?: string[];
  language_preference?: string;
}

class NigerianAnalyticsService {
  private baseUrl = '/api/dashboard/nigerian-analytics';

  /**
   * Fetch comprehensive Nigerian analytics data
   */
  async getAnalyticsData(
    timeRange: TimeRangeOptions = { range: '30d' },
    filters?: AnalyticsFilters
  ): Promise<ApiResponse<NigerianAnalyticsData>> {
    try {
      const params = new URLSearchParams({
        range: timeRange.range,
        ...(timeRange.start_date && { start_date: timeRange.start_date }),
        ...(timeRange.end_date && { end_date: timeRange.end_date }),
        ...(filters?.state_codes && { state_codes: filters.state_codes.join(',') }),
        ...(filters?.business_sectors && { business_sectors: filters.business_sectors.join(',') }),
        ...(filters?.compliance_status && { compliance_status: filters.compliance_status.join(',') }),
        ...(filters?.language_preference && { language_preference: filters.language_preference })
      });

      const response = await apiClient.get(`${this.baseUrl}?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch Nigerian analytics data:', error);
      throw error;
    }
  }

  /**
   * Fetch compliance metrics specifically
   */
  async getComplianceMetrics(timeRange: TimeRangeOptions = { range: '30d' }): Promise<ApiResponse<{
    nitda_compliance: {
      status: string;
      score: number;
      expiry_date: string;
      last_audit: string;
    };
    ndpr_compliance: {
      score: number;
      data_categories_compliant: number;
      total_data_categories: number;
      last_assessment: string;
    };
    iso_compliance: {
      status: string;
      certification_date: string;
      next_audit: string;
      non_conformities: number;
    };
    firs_penalties: {
      total_amount: number;
      active_penalties: number;
      resolved_penalties: number;
      payment_plans_active: number;
    };
  }>> {
    try {
      const params = new URLSearchParams({ range: timeRange.range });
      const response = await apiClient.get(`${this.baseUrl}/compliance?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch compliance metrics:', error);
      throw error;
    }
  }

  /**
   * Fetch regional performance data
   */
  async getRegionalMetrics(timeRange: TimeRangeOptions = { range: '30d' }): Promise<ApiResponse<{
    state_performance: Array<{
      state: string;
      state_code: string;
      region: string;
      businesses: number;
      revenue: number;
      growth_rate: number;
      compliance_rate: number;
      top_industries: string[];
    }>;
    lga_performance: Array<{
      lga: string;
      state: string;
      businesses: number;
      revenue: number;
      compliance_rate: number;
    }>;
    regional_summary: Array<{
      region: string;
      total_businesses: number;
      total_revenue: number;
      average_compliance_rate: number;
    }>;
  }>> {
    try {
      const params = new URLSearchParams({ range: timeRange.range });
      const response = await apiClient.get(`${this.baseUrl}/regional?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch regional metrics:', error);
      throw error;
    }
  }

  /**
   * Fetch cultural adoption analytics
   */
  async getCulturalMetrics(timeRange: TimeRangeOptions = { range: '30d' }): Promise<ApiResponse<{
    language_preferences: Array<{
      language: string;
      users: number;
      percentage: number;
      engagement_rate: number;
      satisfaction_score: number;
    }>;
    communication_channels: Array<{
      channel: string;
      usage_count: number;
      satisfaction_rate: number;
      response_time: number;
    }>;
    cultural_features: Array<{
      feature: string;
      adoption_rate: number;
      satisfaction: number;
      frequency: string;
    }>;
    relationship_management: {
      total_assignments: number;
      average_satisfaction: number;
      cultural_alignment_score: number;
    };
  }>> {
    try {
      const params = new URLSearchParams({ range: timeRange.range });
      const response = await apiClient.get(`${this.baseUrl}/cultural?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch cultural metrics:', error);
      throw error;
    }
  }

  /**
   * Fetch payment method analytics
   */
  async getPaymentAnalytics(timeRange: TimeRangeOptions = { range: '30d' }): Promise<ApiResponse<{
    payment_methods: Array<{
      method: string;
      transaction_count: number;
      total_value: number;
      success_rate: number;
      average_amount: number;
      growth_rate: number;
    }>;
    ussd_analytics: {
      total_transactions: number;
      success_rate: number;
      average_response_time: number;
      popular_codes: Array<{
        code: string;
        usage_count: number;
      }>;
    };
    mobile_money: {
      total_transactions: number;
      providers: Array<{
        provider: string;
        transaction_count: number;
        success_rate: number;
      }>;
    };
  }>> {
    try {
      const params = new URLSearchParams({ range: timeRange.range });
      const response = await apiClient.get(`${this.baseUrl}/payments?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch payment analytics:', error);
      throw error;
    }
  }

  /**
   * Export analytics data
   */
  async exportData(
    format: 'csv' | 'xlsx' | 'pdf',
    timeRange: TimeRangeOptions = { range: '30d' },
    sections?: string[]
  ): Promise<Blob> {
    try {
      const params = new URLSearchParams({
        format,
        range: timeRange.range,
        ...(sections && { sections: sections.join(',') })
      });

      const response = await apiClient.get(`${this.baseUrl}/export?${params}`, {
        responseType: 'blob'
      });

      return response.data;
    } catch (error) {
      console.error('Failed to export analytics data:', error);
      throw error;
    }
  }

  /**
   * Get real-time metrics
   */
  async getRealTimeMetrics(): Promise<ApiResponse<{
    active_users: number;
    transactions_today: number;
    compliance_alerts: number;
    system_health: string;
    penalties_today: number;
    new_businesses_today: number;
  }>> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/realtime`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch real-time metrics:', error);
      throw error;
    }
  }

  /**
   * Get penalty details for FIRS tracking
   */
  async getPenaltyDetails(organizationId?: string): Promise<ApiResponse<{
    penalties: Array<{
      id: string;
      organization_id: string;
      penalty_type: string;
      amount: number;
      violation_date: string;
      status: string;
      payment_plan: string;
      remaining_balance: number;
      next_payment_date: string;
    }>;
    summary: {
      total_penalties: number;
      total_paid: number;
      outstanding_balance: number;
      active_count: number;
    };
  }>> {
    try {
      const params = organizationId ? new URLSearchParams({ organization_id: organizationId }) : '';
      const response = await apiClient.get(`${this.baseUrl}/penalties?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch penalty details:', error);
      throw error;
    }
  }

  /**
   * Get business intelligence recommendations
   */
  async getRecommendations(): Promise<ApiResponse<{
    compliance_recommendations: Array<{
      priority: 'high' | 'medium' | 'low';
      category: string;
      title: string;
      description: string;
      action_required: string;
    }>;
    growth_opportunities: Array<{
      opportunity: string;
      potential_impact: string;
      difficulty: string;
      timeline: string;
    }>;
    risk_alerts: Array<{
      risk_level: 'critical' | 'high' | 'medium' | 'low';
      category: string;
      description: string;
      mitigation_steps: string[];
    }>;
  }>> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/recommendations`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      throw error;
    }
  }
}

export const nigerianAnalyticsService = new NigerianAnalyticsService();
/**
 * HubSpot Deals Management Component
 * 
 * This component provides a comprehensive interface for viewing, filtering,
 * and managing deals from HubSpot CRM integration.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Search,
  Filter,
  RefreshCw,
  Download,
  ChevronDown,
  Calendar,
  DollarSign,
  User,
  FileText,
  MoreHorizontal,
  CheckSquare,
  Square,
  ArrowUpDown,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';

import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LegacySelect } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Table } from '@/components/ui/Table';
import { Checkbox } from '@/components/ui/Checkbox';
import { Modal } from '@/components/ui/Modal';
import { Alert } from '@/components/ui/Alert';
import { Spinner } from '@/components/ui/Spinner';
import { Tooltip } from '@/components/ui/Tooltip';

import CRMService from '@/services/crmService';
import {
  CRMConnection,
  CRMDeal,
  DealFilters,
  PaginationMeta,
  DealListItem
} from '@/types/crm';

// ==================== INTERFACES ====================

interface HubSpotDealsManagerProps {
  connection: CRMConnection;
  onDealSelect?: (deal: CRMDeal) => void;
  onDealsSelect?: (deals: CRMDeal[]) => void;
  onDealsUpdate?: () => void;
  className?: string;
}

interface DealFilterForm {
  search: string;
  stage: string;
  invoice_status: string;
  sort_by: string;
  sort_order: 'asc' | 'desc';
  date_range: {
    start_date: string;
    end_date: string;
  };
}

// ==================== CONSTANTS ====================

const DEAL_STAGES = [
  { value: '', label: 'All Stages' },
  { value: 'appointmentscheduled', label: 'Appointment Scheduled' },
  { value: 'qualifiedtobuy', label: 'Qualified to Buy' },
  { value: 'presentationscheduled', label: 'Presentation Scheduled' },
  { value: 'decisionmakerboughtin', label: 'Decision Maker Bought-in' },
  { value: 'contractsent', label: 'Contract Sent' },
  { value: 'closedwon', label: 'Closed Won' },
  { value: 'closedlost', label: 'Closed Lost' }
];

const INVOICE_STATUS_OPTIONS = [
  { value: 'all', label: 'All Deals' },
  { value: 'generated', label: 'Invoice Generated' },
  { value: 'pending', label: 'Invoice Pending' }
];

const SORT_OPTIONS = [
  { value: 'created_at', label: 'Date Created' },
  { value: 'amount', label: 'Deal Amount' },
  { value: 'close_date', label: 'Close Date' },
  { value: 'deal_title', label: 'Deal Name' }
];

// ==================== MAIN COMPONENT ====================

const HubSpotDealsManager: React.FC<HubSpotDealsManagerProps> = ({
  connection,
  onDealSelect,
  onDealsSelect,
  className = ''
}) => {
  // ==================== STATE MANAGEMENT ====================
  
  const [deals, setDeals] = useState<CRMDeal[]>([]);
  const [selectedDeals, setSelectedDeals] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState<PaginationMeta>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0
  });
  const [showFilters, setShowFilters] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState<CRMDeal | null>(null);
  const [showDealModal, setShowDealModal] = useState(false);

  // ==================== FORM SETUP ====================

  const { control, watch, setValue, getValues, reset } = useForm<DealFilterForm>({
    defaultValues: {
      search: '',
      stage: '',
      invoice_status: 'all',
      sort_by: 'created_at',
      sort_order: 'desc',
      date_range: {
        start_date: '',
        end_date: ''
      }
    }
  });

  const filters = watch();

  // ==================== DATA FETCHING ====================

  const fetchDeals = useCallback(async (page: number = 1, showLoading: boolean = true) => {
    try {
      if (showLoading) setIsLoading(true);
      setError(null);

      const filterParams: DealFilters = {
        ...(filters.search && { search: filters.search }),
        ...(filters.stage && { stage: filters.stage }),
        ...(filters.invoice_status !== 'all' && { invoice_status: filters.invoice_status as any }),
        sort_by: filters.sort_by as any,
        sort_order: filters.sort_order
      };

      if (filters.date_range.start_date || filters.date_range.end_date) {
        filterParams.date_range = {
          start_date: filters.date_range.start_date,
          end_date: filters.date_range.end_date
        };
      }

      const response = await CRMService.getDeals(
        connection.id,
        filterParams,
        { page, page_size: pagination.page_size }
      );

      setDeals(response.deals);
      setPagination(response.pagination);
      setSelectedDeals(new Set());

    } catch (error: any) {
      console.error('Error fetching deals:', error);
      setError(error.message || 'Failed to fetch deals');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [connection.id, filters, pagination.page_size]);

  const refreshDeals = async () => {
    setIsRefreshing(true);
    await fetchDeals(pagination.page, false);
  };

  const syncConnection = async () => {
    try {
      setIsRefreshing(true);
      await CRMService.syncConnection(connection.id, 30);
      await fetchDeals(1);
    } catch (error: any) {
      console.error('Error syncing connection:', error);
      setError(error.message || 'Failed to sync deals');
      setIsRefreshing(false);
    }
  };

  // ==================== SELECTION HANDLERS ====================

  const toggleDealSelection = (dealId: string) => {
    const newSelection = new Set(selectedDeals);
    if (newSelection.has(dealId)) {
      newSelection.delete(dealId);
    } else {
      newSelection.add(dealId);
    }
    setSelectedDeals(newSelection);
    
    const selectedDealObjects = deals.filter(deal => newSelection.has(deal.id));
    onDealsSelect?.(selectedDealObjects);
  };

  const toggleAllDeals = () => {
    if (selectedDeals.size === deals.length) {
      setSelectedDeals(new Set());
      onDealsSelect?.([]);
    } else {
      const allIds = new Set(deals.map(deal => deal.id));
      setSelectedDeals(allIds);
      onDealsSelect?.(deals);
    }
  };

  const viewDealDetails = (deal: CRMDeal) => {
    setSelectedDeal(deal);
    setShowDealModal(true);
    onDealSelect?.(deal);
  };

  // ==================== EFFECT HOOKS ====================

  useEffect(() => {
    fetchDeals(1);
  }, [connection.id]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (pagination.page === 1) {
        fetchDeals(1);
      } else {
        setPagination(prev => ({ ...prev, page: 1 }));
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [filters]);

  // ==================== RENDER HELPERS ====================

  const renderFilters = () => (
    <Card className="mb-6">
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Search</label>
            <Controller
              name="search"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  placeholder="Search deals..."
                  icon={<Search className="w-4 h-4" />}
                />
              )}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Deal Stage</label>
            <Controller
              name="stage"
              control={control}
              render={({ field }) => (
                <LegacySelect
                  {...field}
                  options={DEAL_STAGES}
                  placeholder="All stages"
                />
              )}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Invoice Status</label>
            <Controller
              name="invoice_status"
              control={control}
              render={({ field }) => (
                <LegacySelect
                  {...field}
                  options={INVOICE_STATUS_OPTIONS}
                />
              )}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Sort By</label>
            <div className="flex gap-2">
              <Controller
                name="sort_by"
                control={control}
                render={({ field }) => (
                  <LegacySelect
                    {...field}
                    options={SORT_OPTIONS}
                    className="flex-1"
                  />
                )}
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => setValue('sort_order', filters.sort_order === 'asc' ? 'desc' : 'asc')}
              >
                <ArrowUpDown className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        <div className="flex justify-between items-center mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => reset()}
          >
            Clear Filters
          </Button>
          
          <div className="text-sm text-gray-600">
            {pagination.total} deals found
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const formatCurrency = (amount: number | undefined): string => {
    if (!amount) return 'N/A';
    return CRMService.formatCurrency(amount);
  };

  const formatDate = (dateString: string | undefined): string => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getStageColor = (stage: string): string => {
    const stageColors: Record<string, string> = {
      'closedwon': 'success',
      'closedlost': 'error',
      'contractsent': 'warning',
      'appointmentscheduled': 'info',
      'qualifiedtobuy': 'info',
      'presentationscheduled': 'warning',
      'decisionmakerboughtin': 'warning'
    };
    return stageColors[stage] || 'default';
  };

  const renderDealsTable = () => (
    <Card>
      <CardHeader
        title={`Deals (${pagination.total})`}
        action={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={refreshDeals}
              disabled={isRefreshing}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={syncConnection}
              disabled={isRefreshing}
            >
              <Download className="w-4 h-4 mr-2" />
              Sync from HubSpot
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
              <ChevronDown className={`w-4 h-4 ml-1 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
            </Button>
          </div>
        }
      />

      {showFilters && renderFilters()}

      <CardContent>
        {isLoading ? (
          <div className="text-center py-8">
            <Spinner className="w-8 h-8 mx-auto mb-4" />
            <p>Loading deals...</p>
          </div>
        ) : error ? (
          <Alert variant="error" className="mb-6">
            <div>
              <p className="font-medium">Error Loading Deals</p>
              <p className="text-sm">{error}</p>
            </div>
          </Alert>
        ) : deals.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No deals found</h3>
            <p className="text-gray-600 mb-4">
              {filters.search || filters.stage || filters.invoice_status !== 'all' 
                ? 'Try adjusting your filters'
                : 'No deals have been synced from HubSpot yet'}
            </p>
            <Button onClick={syncConnection} disabled={isRefreshing}>
              Sync Deals from HubSpot
            </Button>
          </div>
        ) : (
          <>
            <Table>
              <thead>
                <tr>
                  <th className="w-8">
                    <Checkbox
                      checked={selectedDeals.size === deals.length && deals.length > 0}
                      onCheckedChange={toggleAllDeals}
                    />
                  </th>
                  <th>Deal Name</th>
                  <th>Amount</th>
                  <th>Stage</th>
                  <th>Close Date</th>
                  <th>Invoice Status</th>
                  <th>Created</th>
                  <th className="w-8"></th>
                </tr>
              </thead>
              <tbody>
                {deals.map((deal) => (
                  <tr key={deal.id} className="hover:bg-gray-50">
                    <td>
                      <Checkbox
                        checked={selectedDeals.has(deal.id)}
                        onCheckedChange={() => toggleDealSelection(deal.id)}
                      />
                    </td>
                    <td>
                      <div>
                        <p className="font-medium">{deal.deal_title || 'Untitled Deal'}</p>
                        <p className="text-sm text-gray-600">ID: {deal.external_deal_id}</p>
                      </div>
                    </td>
                    <td>
                      <span className="font-medium">
                        {formatCurrency(deal.deal_amount)}
                      </span>
                    </td>
                    <td>
                      <Badge variant={getStageColor(deal.deal_stage || '') as any}>
                        {CRMService.formatDealStage(deal.deal_stage || '')}
                      </Badge>
                    </td>
                    <td>{formatDate(deal.expected_close_date)}</td>
                    <td>
                      {deal.invoice_generated ? (
                        <Badge variant="success">Generated</Badge>
                      ) : (
                        <Badge variant="secondary">Pending</Badge>
                      )}
                    </td>
                    <td>{formatDate(deal.created_at)}</td>
                    <td>
                      <Tooltip content="View details">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewDealDetails(deal)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </Tooltip>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>

            {/* Pagination */}
            {pagination.total_pages > 1 && (
              <div className="flex justify-between items-center mt-6">
                <p className="text-sm text-gray-600">
                  Showing {((pagination.page - 1) * pagination.page_size) + 1} to{' '}
                  {Math.min(pagination.page * pagination.page_size, pagination.total)} of{' '}
                  {pagination.total} deals
                </p>
                
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fetchDeals(pagination.page - 1)}
                    disabled={pagination.page === 1 || isLoading}
                  >
                    Previous
                  </Button>
                  
                  <span className="px-3 py-1 text-sm">
                    Page {pagination.page} of {pagination.total_pages}
                  </span>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fetchDeals(pagination.page + 1)}
                    disabled={pagination.page === pagination.total_pages || isLoading}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );

  // ==================== DEAL DETAIL MODAL ====================

  const renderDealModal = () => (
    <Modal
      isOpen={showDealModal}
      onClose={() => {
        setShowDealModal(false);
        setSelectedDeal(null);
      }}
      title="Deal Details"
      size="large"
    >
      {selectedDeal && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium mb-3">Basic Information</h4>
              <div className="space-y-2">
                <div>
                  <span className="text-sm text-gray-600">Deal Name:</span>
                  <p className="font-medium">{selectedDeal.deal_title || 'Untitled Deal'}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Amount:</span>
                  <p className="font-medium">{formatCurrency(selectedDeal.deal_amount)}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Stage:</span>
                  <Badge variant={getStageColor(selectedDeal.deal_stage || '') as any}>
                    {CRMService.formatDealStage(selectedDeal.deal_stage || '')}
                  </Badge>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Expected Close Date:</span>
                  <p>{formatDate(selectedDeal.expected_close_date)}</p>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-3">Invoice Status</h4>
              <div className="space-y-2">
                <div>
                  <span className="text-sm text-gray-600">Invoice Generated:</span>
                  <Badge variant={selectedDeal.invoice_generated ? 'success' : 'secondary'}>
                    {selectedDeal.invoice_generated ? 'Yes' : 'No'}
                  </Badge>
                </div>
                {selectedDeal.invoice_id && (
                  <div>
                    <span className="text-sm text-gray-600">Invoice ID:</span>
                    <p className="font-mono text-sm">{selectedDeal.invoice_id}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {selectedDeal.customer_data && (
            <div>
              <h4 className="font-medium mb-3">Customer Information</h4>
              <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
                {JSON.stringify(selectedDeal.customer_data, null, 2)}
              </pre>
            </div>
          )}

          {selectedDeal.deal_metadata && (
            <div>
              <h4 className="font-medium mb-3">Additional Metadata</h4>
              <pre className="bg-gray-50 p-3 rounded text-sm overflow-auto">
                {JSON.stringify(selectedDeal.deal_metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </Modal>
  );

  // ==================== MAIN RENDER ====================

  return (
    <div className={className}>
      {renderDealsTable()}
      {renderDealModal()}
    </div>
  );
};

export default HubSpotDealsManager;
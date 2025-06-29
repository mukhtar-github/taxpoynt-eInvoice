import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Separator } from '../ui/separator';
import { Textarea } from '../ui/textarea';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import {
  CheckCircle,
  XCircle,
  Clock,
  ArrowUp,
  User,
  Users,
  AlertTriangle,
  FileText,
  DollarSign,
  Calendar,
  MessageSquare,
  Building,
  Shield,
  TrendingUp
} from 'lucide-react';

interface ApprovalLevel {
  id: string;
  level_name: string;
  level_order: number;
  amount_limit_ngn: number;
  requires_superior_approval: boolean;
  requires_board_approval: boolean;
  requires_board_ratification: boolean;
  conditions: {
    requires_documentation?: boolean;
    requires_receipt?: boolean;
    requires_justification?: boolean;
    requires_budget_allocation?: boolean;
    requires_detailed_proposal?: boolean;
    requires_financial_impact_analysis?: boolean;
    requires_risk_assessment?: boolean;
    requires_board_meeting?: boolean;
    requires_unanimous_consent?: boolean;
    requires_external_audit?: boolean;
    max_frequency?: string;
  };
  is_active: boolean;
}

interface ApprovalRequest {
  id: string;
  request_type: string;
  request_reference: string;
  amount_ngn?: number;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'escalated';
  submitted_at: string;
  approved_at?: string;
  rejection_reason?: string;
  escalation_level: number;
  escalated_at?: string;
  escalation_reason?: string;
  approval_level: ApprovalLevel;
  requester: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
  approver?: {
    id: string;
    name: string;
    email: string;
    role: string;
  };
  request_data?: any;
}

interface HierarchicalApprovalWorkflowProps {
  organizationId: string;
  currentUserRole: string;
  onCreateRequest?: (requestData: Partial<ApprovalRequest>) => void;
  onProcessApproval?: (requestId: string, action: 'approve' | 'reject' | 'escalate', reason?: string) => void;
}

const NAIRA_FORMATTER = new Intl.NumberFormat('en-NG', {
  style: 'currency',
  currency: 'NGN',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'approved':
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    case 'rejected':
      return <XCircle className="w-5 h-5 text-red-600" />;
    case 'escalated':
      return <ArrowUp className="w-5 h-5 text-orange-600" />;
    default:
      return <Clock className="w-5 h-5 text-yellow-600" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'approved':
      return 'bg-green-100 text-green-800';
    case 'rejected':
      return 'bg-red-100 text-red-800';
    case 'escalated':
      return 'bg-orange-100 text-orange-800';
    default:
      return 'bg-yellow-100 text-yellow-800';
  }
};

const getApprovalLevelIcon = (levelName: string) => {
  if (levelName.toLowerCase().includes('junior')) return <User className="w-4 h-4" />;
  if (levelName.toLowerCase().includes('middle')) return <Users className="w-4 h-4" />;
  if (levelName.toLowerCase().includes('senior')) return <Building className="w-4 h-4" />;
  if (levelName.toLowerCase().includes('executive')) return <Shield className="w-4 h-4" />;
  return <User className="w-4 h-4" />;
};

const ApprovalRequestCard: React.FC<{
  request: ApprovalRequest;
  currentUserRole: string;
  onProcess?: (action: 'approve' | 'reject' | 'escalate', reason?: string) => void;
}> = ({ request, currentUserRole, onProcess }) => {
  const [showProcessing, setShowProcessing] = useState(false);
  const [action, setAction] = useState<'approve' | 'reject' | 'escalate'>('approve');
  const [reason, setReason] = useState('');

  const canProcess = request.status === 'pending' && 
    (currentUserRole === 'admin' || currentUserRole === 'manager');

  const handleSubmitAction = () => {
    onProcess?.(action, reason);
    setShowProcessing(false);
    setReason('');
  };

  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <CardTitle className="text-lg">{request.request_reference}</CardTitle>
              <Badge className={getStatusColor(request.status)}>
                {getStatusIcon(request.status)}
                <span className="ml-1 capitalize">{request.status}</span>
              </Badge>
            </div>
            <CardDescription>{request.description}</CardDescription>
          </div>
          
          <div className="text-right">
            {request.amount_ngn && (
              <div className="text-lg font-bold text-green-600">
                {NAIRA_FORMATTER.format(request.amount_ngn)}
              </div>
            )}
            <div className="text-sm text-gray-500">
              {getTimeAgo(request.submitted_at)}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Request Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-gray-500" />
            <span>Type: {request.request_type}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            {getApprovalLevelIcon(request.approval_level.level_name)}
            <span>Level: {request.approval_level.level_name}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <User className="w-4 h-4 text-gray-500" />
            <span>Requester: {request.requester.name}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span>Submitted: {new Date(request.submitted_at).toLocaleDateString()}</span>
          </div>
        </div>

        {/* Approval Level Requirements */}
        <div className="bg-gray-50 p-3 rounded-lg">
          <h4 className="font-medium text-sm mb-2">Approval Requirements</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            <div className="flex items-center space-x-2">
              <DollarSign className="w-3 h-3 text-gray-500" />
              <span>Limit: {NAIRA_FORMATTER.format(request.approval_level.amount_limit_ngn)}</span>
            </div>
            
            {request.approval_level.requires_superior_approval && (
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-3 h-3 text-orange-500" />
                <span>Requires Superior Approval</span>
              </div>
            )}
            
            {request.approval_level.requires_board_approval && (
              <div className="flex items-center space-x-2">
                <Shield className="w-3 h-3 text-red-500" />
                <span>Requires Board Approval</span>
              </div>
            )}
            
            {request.approval_level.conditions.requires_documentation && (
              <div className="flex items-center space-x-2">
                <FileText className="w-3 h-3 text-blue-500" />
                <span>Documentation Required</span>
              </div>
            )}
            
            {request.approval_level.conditions.requires_justification && (
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-3 h-3 text-purple-500" />
                <span>Justification Required</span>
              </div>
            )}
          </div>
        </div>

        {/* Escalation Info */}
        {request.escalation_level > 0 && (
          <div className="bg-orange-50 border border-orange-200 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <ArrowUp className="w-4 h-4 text-orange-600" />
              <span className="font-medium text-orange-800">
                Escalated (Level {request.escalation_level})
              </span>
            </div>
            {request.escalation_reason && (
              <p className="text-sm text-orange-700">{request.escalation_reason}</p>
            )}
          </div>
        )}

        {/* Rejection Reason */}
        {request.status === 'rejected' && request.rejection_reason && (
          <div className="bg-red-50 border border-red-200 p-3 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <XCircle className="w-4 h-4 text-red-600" />
              <span className="font-medium text-red-800">Rejection Reason</span>
            </div>
            <p className="text-sm text-red-700">{request.rejection_reason}</p>
          </div>
        )}

        {/* Approver Info */}
        {request.approver && (
          <div className="flex items-center space-x-2 text-sm">
            <User className="w-4 h-4 text-gray-500" />
            <span>
              {request.status === 'approved' ? 'Approved by' : 'Processed by'}: {request.approver.name}
            </span>
            {request.approved_at && (
              <span className="text-gray-500">
                on {new Date(request.approved_at).toLocaleDateString()}
              </span>
            )}
          </div>
        )}

        {/* Process Actions */}
        {canProcess && !showProcessing && (
          <div className="flex space-x-2 pt-2">
            <Button 
              variant="default" 
              size="sm"
              onClick={() => {
                setAction('approve');
                setShowProcessing(true);
              }}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Approve
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setAction('reject');
                setShowProcessing(true);
              }}
              className="text-red-600 border-red-300 hover:bg-red-50"
            >
              <XCircle className="w-4 h-4 mr-1" />
              Reject
            </Button>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => {
                setAction('escalate');
                setShowProcessing(true);
              }}
              className="text-orange-600 border-orange-300 hover:bg-orange-50"
            >
              <ArrowUp className="w-4 h-4 mr-1" />
              Escalate
            </Button>
          </div>
        )}

        {/* Processing Form */}
        {showProcessing && (
          <div className="border-t pt-4 space-y-3">
            <div>
              <Label htmlFor="reason">
                {action === 'approve' ? 'Approval Notes (Optional)' : 
                 action === 'reject' ? 'Rejection Reason' : 'Escalation Reason'}
              </Label>
              <Textarea
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder={
                  action === 'approve' ? 'Add any notes about this approval...' :
                  action === 'reject' ? 'Please provide a reason for rejection...' :
                  'Please provide a reason for escalation...'
                }
                rows={3}
              />
            </div>
            
            <div className="flex space-x-2">
              <Button 
                variant="default" 
                size="sm"
                onClick={handleSubmitAction}
                disabled={action !== 'approve' && !reason.trim()}
              >
                Submit {action}
              </Button>
              
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  setShowProcessing(false);
                  setReason('');
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const NewApprovalRequestForm: React.FC<{
  approvalLevels: ApprovalLevel[];
  onSubmit: (requestData: Partial<ApprovalRequest>) => void;
  onCancel: () => void;
}> = ({ approvalLevels, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    request_type: '',
    description: '',
    amount_ngn: '',
    request_reference: ''
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      amount_ngn: formData.amount_ngn ? parseFloat(formData.amount_ngn) : undefined
    });
  };

  const getApprovalLevel = () => {
    const amount = parseFloat(formData.amount_ngn) || 0;
    return approvalLevels.find(level => level.amount_limit_ngn >= amount) || 
           approvalLevels[approvalLevels.length - 1];
  };

  const approvalLevel = getApprovalLevel();

  return (
    <Card>
      <CardHeader>
        <CardTitle>New Approval Request</CardTitle>
        <CardDescription>
          Submit a new request for approval following Nigerian corporate hierarchy
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="request_type">Request Type</Label>
              <Input
                id="request_type"
                value={formData.request_type}
                onChange={(e) => setFormData(prev => ({ ...prev, request_type: e.target.value }))}
                placeholder="e.g., Invoice, Payment, Contract"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="request_reference">Reference Number</Label>
              <Input
                id="request_reference"
                value={formData.request_reference}
                onChange={(e) => setFormData(prev => ({ ...prev, request_reference: e.target.value }))}
                placeholder="e.g., INV-2024-001"
                required
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="amount_ngn">Amount (₦)</Label>
            <Input
              id="amount_ngn"
              type="number"
              value={formData.amount_ngn}
              onChange={(e) => setFormData(prev => ({ ...prev, amount_ngn: e.target.value }))}
              placeholder="Enter amount in Naira"
              min="0"
              step="0.01"
            />
          </div>
          
          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Provide detailed description of the request..."
              rows={4}
              required
            />
          </div>
          
          {approvalLevel && formData.amount_ngn && (
            <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                {getApprovalLevelIcon(approvalLevel.level_name)}
                <span className="font-medium text-blue-800">
                  Approval Level: {approvalLevel.level_name}
                </span>
              </div>
              <div className="text-sm text-blue-700">
                <p>Amount Limit: {NAIRA_FORMATTER.format(approvalLevel.amount_limit_ngn)}</p>
                {approvalLevel.requires_superior_approval && (
                  <p>• Requires superior approval</p>
                )}
                {approvalLevel.requires_board_approval && (
                  <p>• Requires board approval</p>
                )}
              </div>
            </div>
          )}
          
          <div className="flex space-x-2 pt-4">
            <Button type="submit" variant="default">
              Submit Request
            </Button>
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export const HierarchicalApprovalWorkflow: React.FC<HierarchicalApprovalWorkflowProps> = ({
  organizationId,
  currentUserRole,
  onCreateRequest,
  onProcessApproval
}) => {
  const [approvalRequests, setApprovalRequests] = useState<ApprovalRequest[]>([]);
  const [approvalLevels, setApprovalLevels] = useState<ApprovalLevel[]>([]);
  const [showNewRequestForm, setShowNewRequestForm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');

  useEffect(() => {
    loadApprovalData();
  }, [organizationId]);

  const loadApprovalData = async () => {
    try {
      const [requestsRes, levelsRes] = await Promise.all([
        fetch(`/api/nigerian/approval-requests/${organizationId}`),
        fetch(`/api/nigerian/approval-levels/${organizationId}`)
      ]);

      if (requestsRes.ok && levelsRes.ok) {
        const [requestsData, levelsData] = await Promise.all([
          requestsRes.json(),
          levelsRes.json()
        ]);
        
        setApprovalRequests(requestsData.requests || []);
        setApprovalLevels(levelsData.levels || []);
      }
    } catch (error) {
      console.error('Failed to load approval data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRequest = (requestData: Partial<ApprovalRequest>) => {
    onCreateRequest?.(requestData);
    setShowNewRequestForm(false);
    loadApprovalData();
  };

  const handleProcessApproval = (requestId: string, action: 'approve' | 'reject' | 'escalate', reason?: string) => {
    onProcessApproval?.(requestId, action, reason);
    loadApprovalData();
  };

  const filteredRequests = approvalRequests.filter(request => {
    if (filter === 'all') return true;
    return request.status === filter;
  });

  const getStats = () => {
    const total = approvalRequests.length;
    const pending = approvalRequests.filter(r => r.status === 'pending').length;
    const approved = approvalRequests.filter(r => r.status === 'approved').length;
    const rejected = approvalRequests.filter(r => r.status === 'rejected').length;
    
    return { total, pending, approved, rejected };
  };

  const stats = getStats();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-yellow-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Approved</p>
                <p className="text-2xl font-bold text-green-600">{stats.approved}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Rejected</p>
                <p className="text-2xl font-bold text-red-600">{stats.rejected}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Actions and Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-2">
          <Button
            variant={filter === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('all')}
          >
            All
          </Button>
          <Button
            variant={filter === 'pending' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('pending')}
          >
            Pending
          </Button>
          <Button
            variant={filter === 'approved' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('approved')}
          >
            Approved
          </Button>
          <Button
            variant={filter === 'rejected' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter('rejected')}
          >
            Rejected
          </Button>
        </div>
        
        <Button onClick={() => setShowNewRequestForm(true)}>
          <FileText className="w-4 h-4 mr-2" />
          New Request
        </Button>
      </div>

      {/* New Request Form */}
      {showNewRequestForm && (
        <NewApprovalRequestForm
          approvalLevels={approvalLevels}
          onSubmit={handleCreateRequest}
          onCancel={() => setShowNewRequestForm(false)}
        />
      )}

      {/* Approval Requests */}
      <div className="space-y-4">
        {filteredRequests.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No approval requests found
              </h3>
              <p className="text-gray-600 mb-4">
                {filter === 'all' 
                  ? "Create your first approval request to get started with the Nigerian hierarchical approval system."
                  : `No ${filter} approval requests at this time.`
                }
              </p>
              {filter === 'all' && (
                <Button onClick={() => setShowNewRequestForm(true)}>
                  Create Request
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          filteredRequests.map((request) => (
            <ApprovalRequestCard
              key={request.id}
              request={request}
              currentUserRole={currentUserRole}
              onProcess={(action, reason) => handleProcessApproval(request.id, action, reason)}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default HierarchicalApprovalWorkflow;
/**
 * Validation Engine Component
 * ===========================
 * 
 * Pre-submission validation center for document quality assurance.
 * Connects to app_services/validation/ backend services for comprehensive validation.
 * 
 * Features:
 * - Multi-tier validation pipeline (Format, Business, Compliance, FIRS)
 * - Real-time validation feedback
 * - Validation rule management
 * - Error categorization and resolution guidance
 * - Batch validation processing
 * - Validation quality scoring
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Badge,
  Progress,
  ScrollArea,
  Alert,
  AlertDescription,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Textarea,
  Switch
} from '@/components/ui';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Info,
  Shield,
  FileText,
  Settings,
  Play,
  Pause,
  RefreshCw,
  Search,
  Filter,
  Download,
  Upload,
  Eye,
  Edit,
  Trash2,
  Plus,
  BarChart3,
  Zap,
  Clock,
  Target
} from 'lucide-react';

import { 
  ValidationRule, 
  ValidationSession, 
  ValidationResult,
  ValidationConfig,
  ValidationSeverity
} from '../../types';

// Mock data
const mockValidationRules: ValidationRule[] = [
  {
    id: 'rule_001',
    name: 'Invoice Number Format',
    description: 'Invoice number must follow the required format pattern',
    category: 'format',
    severity: 'critical',
    active: true,
    rule_logic: '^[A-Z]{2,3}-[0-9]{4,8}$',
    error_message: 'Invalid invoice number format',
    suggestion: 'Use format: ABC-12345 or AB-1234567'
  },
  {
    id: 'rule_002',
    name: 'Nigerian VAT Rate',
    description: 'VAT rate must be 7.5% for Nigerian transactions',
    category: 'business',
    severity: 'critical',
    active: true,
    rule_logic: 'vat_rate === 0.075',
    error_message: 'Invalid VAT rate for Nigerian transactions',
    suggestion: 'Set VAT rate to 7.5% (0.075) for domestic transactions'
  },
  {
    id: 'rule_003',
    name: 'TIN Format Validation',
    description: 'Tax Identification Number must be 14 digits',
    category: 'compliance',
    severity: 'critical',
    active: true,
    rule_logic: '^[0-9]{14}$',
    error_message: 'Invalid TIN format',
    suggestion: 'TIN must be exactly 14 digits'
  },
  {
    id: 'rule_004',
    name: 'Invoice Date Range',
    description: 'Invoice date should not be more than 30 days old',
    category: 'business',
    severity: 'warning',
    active: true,
    rule_logic: 'invoice_date >= (current_date - 30 days)',
    error_message: 'Invoice date is more than 30 days old',
    suggestion: 'Verify invoice date is within acceptable range'
  },
  {
    id: 'rule_005',
    name: 'Currency Code Validation',
    description: 'Currency code must be valid ISO 4217 code',
    category: 'format',
    severity: 'error',
    active: true,
    rule_logic: 'currency in ["NGN", "USD", "EUR", "GBP"]',
    error_message: 'Invalid currency code',
    suggestion: 'Use valid ISO 4217 currency codes (NGN, USD, EUR, GBP)'
  }
];

const mockValidationSessions: ValidationSession[] = [
  {
    id: 'session_001',
    document_id: 'doc_12345',
    document_type: 'invoice',
    timestamp: new Date(),
    status: 'completed',
    total_rules: 25,
    passed_rules: 22,
    failed_rules: 3,
    warnings: 2,
    overall_score: 88,
    results: [],
    duration: 2.3
  },
  {
    id: 'session_002',
    document_id: 'doc_12346',
    document_type: 'credit_note',
    timestamp: new Date(Date.now() - 300000),
    status: 'completed',
    total_rules: 25,
    passed_rules: 25,
    failed_rules: 0,
    warnings: 1,
    overall_score: 98,
    results: [],
    duration: 1.8
  },
  {
    id: 'session_003',
    document_id: 'doc_12347',
    document_type: 'invoice',
    timestamp: new Date(Date.now() - 600000),
    status: 'failed',
    total_rules: 25,
    passed_rules: 18,
    failed_rules: 7,
    warnings: 3,
    overall_score: 65,
    results: [],
    duration: 3.1
  }
];

const mockValidationResults: ValidationResult[] = [
  {
    rule_id: 'rule_001',
    rule_name: 'Invoice Number Format',
    status: 'failed',
    severity: 'critical',
    message: 'Invoice number "INV123" does not match required format',
    field_path: 'invoice.invoiceNumber',
    expected_value: 'ABC-12345 format',
    actual_value: 'INV123',
    suggestion: 'Use format: ABC-12345 or AB-1234567',
    documentation_link: 'https://docs.firs.gov.ng/invoice-format'
  },
  {
    rule_id: 'rule_002',
    rule_name: 'Nigerian VAT Rate',
    status: 'failed',
    severity: 'critical',
    message: 'VAT rate 0.05 is incorrect for Nigerian transactions',
    field_path: 'invoice.tax.vatRate',
    expected_value: 0.075,
    actual_value: 0.05,
    suggestion: 'Set VAT rate to 7.5% (0.075) for domestic transactions'
  },
  {
    rule_id: 'rule_004',
    rule_name: 'Invoice Date Range',
    status: 'failed',
    severity: 'warning',
    message: 'Invoice date is 45 days old',
    field_path: 'invoice.issueDate',
    expected_value: 'Within 30 days',
    actual_value: '45 days ago',
    suggestion: 'Verify invoice date is within acceptable range'
  }
];

export const ValidationEngine: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [validationRules, setValidationRules] = useState<ValidationRule[]>(mockValidationRules);
  const [validationSessions, setValidationSessions] = useState<ValidationSession[]>(mockValidationSessions);
  const [currentResults, setCurrentResults] = useState<ValidationResult[]>(mockValidationResults);
  const [isValidating, setIsValidating] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [documentContent, setDocumentContent] = useState('');

  const getSeverityIcon = (severity: ValidationSeverity) => {
    switch (severity) {
      case 'critical': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'error': return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info': return <Info className="h-4 w-4 text-blue-500" />;
      default: return <Info className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity: ValidationSeverity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'error': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'skipped': return <Info className="h-4 w-4 text-gray-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 85) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleValidateDocument = async () => {
    if (!documentContent.trim()) return;

    setIsValidating(true);
    
    try {
      // Simulate validation API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      console.log('Document validation completed');
      // In real implementation, this would call validation API
      
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setIsValidating(false);
    }
  };

  const handleToggleRule = (ruleId: string) => {
    setValidationRules(prev => 
      prev.map(rule => 
        rule.id === ruleId 
          ? { ...rule, active: !rule.active }
          : rule
      )
    );
  };

  const filteredRules = validationRules.filter(rule => 
    (selectedCategory === 'all' || rule.category === selectedCategory) &&
    (selectedSeverity === 'all' || rule.severity === selectedSeverity) &&
    (searchTerm === '' || 
     rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
     rule.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const filteredResults = currentResults.filter(result => 
    (selectedSeverity === 'all' || result.severity === selectedSeverity) &&
    (searchTerm === '' || 
     result.rule_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
     result.message.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            Validation Engine
          </h2>
          <p className="text-gray-600 mt-1">
            Pre-submission validation and quality assurance center
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            🇳🇬 Nigerian Compliant
          </Badge>
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            {validationRules.filter(r => r.active).length} Active Rules
          </Badge>
        </div>
      </div>

      {/* Validation Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Validations</p>
                <p className="text-2xl font-bold text-blue-600">
                  {validationSessions.length.toLocaleString()}
                </p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
            <div className="mt-2">
              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                +12% this week
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-green-600">
                  {Math.round(validationSessions.filter(s => s.overall_score >= 85).length / validationSessions.length * 100)}%
                </p>
              </div>
              <Target className="h-8 w-8 text-green-600" />
            </div>
            <Progress value={83.3} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Avg Processing Time</p>
                <p className="text-2xl font-bold text-purple-600">
                  {(validationSessions.reduce((sum, s) => sum + s.duration, 0) / validationSessions.length).toFixed(1)}s
                </p>
              </div>
              <Clock className="h-8 w-8 text-purple-600" />
            </div>
            <div className="mt-2">
              <Badge variant="outline" className="bg-green-50 text-green-700">
                Within SLA
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Rules</p>
                <p className="text-2xl font-bold text-orange-600">
                  {validationRules.filter(r => r.active).length}
                </p>
              </div>
              <Zap className="h-8 w-8 text-orange-600" />
            </div>
            <div className="mt-2 text-sm text-gray-600">
              of {validationRules.length} total
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="validate">Validate Document</TabsTrigger>
          <TabsTrigger value="rules">Validation Rules</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-6">
          {/* Recent Validation Sessions */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Validation Sessions</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document ID</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Score</TableHead>
                    <TableHead>Rules</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {validationSessions.map(session => (
                    <TableRow key={session.id}>
                      <TableCell className="font-mono">{session.document_id}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {session.document_type.replace('_', ' ')}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className={`font-bold ${getScoreColor(session.overall_score)}`}>
                            {session.overall_score}%
                          </span>
                          <Progress value={session.overall_score} className="w-16 h-2" />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <span className="text-green-600">{session.passed_rules} passed</span>
                          {session.failed_rules > 0 && (
                            <span className="text-red-600 ml-2">{session.failed_rules} failed</span>
                          )}
                          {session.warnings > 0 && (
                            <span className="text-yellow-600 ml-2">{session.warnings} warnings</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{session.duration}s</TableCell>
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={
                            session.status === 'completed' ? 'bg-green-100 text-green-800' :
                            session.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }
                        >
                          {session.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{session.timestamp.toLocaleTimeString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="validate" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Document Input */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Document Input
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Document Content (JSON)</label>
                  <Textarea
                    placeholder="Paste your document JSON here..."
                    value={documentContent}
                    onChange={(e) => setDocumentContent(e.target.value)}
                    rows={12}
                    className="font-mono text-sm"
                  />
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={handleValidateDocument}
                    disabled={isValidating || !documentContent.trim()}
                    className="flex-1"
                  >
                    {isValidating ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Validating...
                      </>
                    ) : (
                      <>
                        <Shield className="h-4 w-4 mr-2" />
                        Validate Document
                      </>
                    )}
                  </Button>
                  <Button variant="outline" size="icon">
                    <Upload className="h-4 w-4" />
                  </Button>
                </div>

                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    Upload your document in JSON format for comprehensive validation against Nigerian compliance rules.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            {/* Validation Progress */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Validation Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isValidating ? (
                  <div className="space-y-4">
                    <div className="text-center">
                      <RefreshCw className="h-12 w-12 mx-auto mb-4 animate-spin text-blue-600" />
                      <p className="font-medium">Running validation...</p>
                      <p className="text-sm text-gray-600">Checking against {validationRules.filter(r => r.active).length} active rules</p>
                    </div>
                    <Progress value={65} className="h-2" />
                  </div>
                ) : currentResults.length > 0 ? (
                  <div className="space-y-4">
                    {/* Validation Summary */}
                    <div className="text-center">
                      <div className="text-3xl font-bold text-orange-600">75%</div>
                      <p className="text-sm text-gray-600">Validation Score</p>
                    </div>

                    {/* Results Summary */}
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div className="p-3 bg-red-50 rounded-lg">
                        <div className="text-lg font-bold text-red-600">2</div>
                        <div className="text-xs text-gray-600">Critical</div>
                      </div>
                      <div className="p-3 bg-orange-50 rounded-lg">
                        <div className="text-lg font-bold text-orange-600">0</div>
                        <div className="text-xs text-gray-600">Errors</div>
                      </div>
                      <div className="p-3 bg-yellow-50 rounded-lg">
                        <div className="text-lg font-bold text-yellow-600">1</div>
                        <div className="text-xs text-gray-600">Warnings</div>
                      </div>
                    </div>

                    {/* Issues List */}
                    <ScrollArea className="h-48">
                      <div className="space-y-2">
                        {currentResults.map((result, index) => (
                          <div
                            key={index}
                            className={`p-3 border rounded-lg ${
                              result.status === 'failed' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              {getSeverityIcon(result.severity)}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-sm">{result.rule_name}</span>
                                  <Badge variant="outline" className={getSeverityColor(result.severity)}>
                                    {result.severity}
                                  </Badge>
                                </div>
                                <p className="text-xs text-gray-600 mb-1">{result.message}</p>
                                {result.suggestion && (
                                  <p className="text-xs text-blue-600">💡 {result.suggestion}</p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No validation results yet</p>
                    <p className="text-sm">Upload a document and run validation</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rules" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Validation Rules</span>
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Input
                      placeholder="Search rules..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-48"
                    />
                    <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Categories</SelectItem>
                        <SelectItem value="format">Format</SelectItem>
                        <SelectItem value="business">Business</SelectItem>
                        <SelectItem value="compliance">Compliance</SelectItem>
                        <SelectItem value="security">Security</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={selectedSeverity} onValueChange={setSelectedSeverity}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Severities</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                        <SelectItem value="error">Error</SelectItem>
                        <SelectItem value="warning">Warning</SelectItem>
                        <SelectItem value="info">Info</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Rule
                  </Button>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredRules.map(rule => (
                  <div key={rule.id} className="p-4 border rounded-lg">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-start gap-3">
                        <div className="flex items-center gap-2 mt-1">
                          <Switch
                            checked={rule.active}
                            onCheckedChange={() => handleToggleRule(rule.id)}
                          />
                          {getSeverityIcon(rule.severity)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-medium">{rule.name}</h4>
                            <Badge variant="outline" className={getSeverityColor(rule.severity)}>
                              {rule.severity}
                            </Badge>
                            <Badge variant="outline" className="text-xs capitalize">
                              {rule.category}
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{rule.description}</p>
                          <div className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded">
                            {rule.rule_logic}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          <Eye className="h-3 w-3" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button variant="outline" size="sm">
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Error: {rule.error_message}</span>
                      <span>Rule ID: {rule.id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Detailed Validation Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredResults.map((result, index) => (
                  <div
                    key={index}
                    className={`p-4 border-l-4 rounded-r-lg ${
                      result.severity === 'critical' ? 'border-red-400 bg-red-50' :
                      result.severity === 'error' ? 'border-orange-400 bg-orange-50' :
                      result.severity === 'warning' ? 'border-yellow-400 bg-yellow-50' :
                      'border-blue-400 bg-blue-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {getSeverityIcon(result.severity)}
                          <h4 className="font-medium">{result.rule_name}</h4>
                          <Badge variant="outline" className={getSeverityColor(result.severity)}>
                            {result.severity}
                          </Badge>
                        </div>
                        <p className="text-sm mb-2">{result.message}</p>
                        
                        {result.field_path && (
                          <div className="mb-2">
                            <span className="text-xs text-gray-600">Field: </span>
                            <code className="text-xs bg-white px-2 py-1 rounded">{result.field_path}</code>
                          </div>
                        )}
                        
                        {result.expected_value && result.actual_value && (
                          <div className="grid grid-cols-2 gap-4 mb-2 text-xs">
                            <div>
                              <span className="text-gray-600">Expected: </span>
                              <code className="bg-white px-2 py-1 rounded">{String(result.expected_value)}</code>
                            </div>
                            <div>
                              <span className="text-gray-600">Actual: </span>
                              <code className="bg-white px-2 py-1 rounded">{String(result.actual_value)}</code>
                            </div>
                          </div>
                        )}
                        
                        {result.suggestion && (
                          <div className="p-3 bg-blue-50 rounded border border-blue-200">
                            <div className="text-sm font-medium text-blue-900 mb-1">Suggestion:</div>
                            <div className="text-sm text-blue-800">{result.suggestion}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Validation Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-3">Validation Strictness</h4>
                <Select defaultValue="standard">
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="strict">Strict (All rules)</SelectItem>
                    <SelectItem value="standard">Standard (Critical + Error)</SelectItem>
                    <SelectItem value="permissive">Permissive (Critical only)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <h4 className="font-medium mb-3">Processing Options</h4>
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Stop validation on first critical error</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Enable auto-fix for correctable issues</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">Generate detailed validation reports</span>
                  </label>
                </div>
              </div>

              <div className="flex gap-3">
                <Button>Save Settings</Button>
                <Button variant="outline">Reset to Defaults</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
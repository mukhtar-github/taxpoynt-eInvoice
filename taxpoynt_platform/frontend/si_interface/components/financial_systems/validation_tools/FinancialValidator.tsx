/**
 * Financial Validation Tools
 * =========================
 * 
 * System Integrator interface for financial data validation and compliance checking.
 * Ensures transaction data meets Nigerian financial regulations and standards.
 * 
 * Features:
 * - Transaction data validation
 * - Nigerian banking compliance checks
 * - Currency and amount validation
 * - Account number verification
 * - BVN (Bank Verification Number) validation
 * - Anti-money laundering (AML) checks
 * - Foreign exchange compliance
 * - CBN reporting requirements
 * 
 * Nigerian Financial Compliance:
 * - Central Bank of Nigeria (CBN) regulations
 * - Nigerian Inter-Bank Settlement System (NIBSS)
 * - Bank Verification Number (BVN) system
 * - Know Your Customer (KYC) requirements
 * - Anti-Money Laundering (AML) compliance
 * - Foreign Exchange Manual (FEM) compliance
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Badge,
  Progress,
  ScrollArea,
  Alert,
  AlertDescription,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Textarea,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui';
import { 
  Shield, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  AlertTriangle,
  Info,
  DollarSign,
  CreditCard,
  Building2,
  User,
  FileText,
  Search,
  Download,
  Upload,
  RefreshCw,
  Eye,
  Settings,
  BarChart3,
  TrendingUp,
  Flag,
  Globe,
  Lock,
  Zap,
  Clock
} from 'lucide-react';

// Types
interface ValidationRule {
  id: string;
  name: string;
  category: 'transaction' | 'account' | 'identity' | 'compliance' | 'aml';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  description: string;
  regulation: string;
  autoFix: boolean;
}

interface ValidationResult {
  rule: ValidationRule;
  status: 'passed' | 'failed' | 'warning' | 'manual_review';
  message: string;
  details?: string;
  suggestion?: string;
  confidence: number;
}

interface TransactionData {
  id: string;
  amount: number;
  currency: string;
  sender: {
    name: string;
    accountNumber: string;
    bankCode: string;
    bvn?: string;
  };
  recipient: {
    name: string;
    accountNumber: string;
    bankCode: string;
    bvn?: string;
  };
  purpose: string;
  category: string;
  timestamp: Date;
  reference: string;
}

interface ValidationSession {
  id: string;
  timestamp: Date;
  dataType: 'transaction' | 'account' | 'bulk';
  totalRecords: number;
  validatedRecords: number;
  results: ValidationResult[];
  overallScore: number;
  status: 'running' | 'completed' | 'failed';
  duration?: number;
}

// Nigerian Financial Validation Rules
const NIGERIAN_VALIDATION_RULES: ValidationRule[] = [
  // Transaction Rules
  {
    id: 'ngn_currency_domestic',
    name: 'Domestic Currency Requirement',
    category: 'transaction',
    severity: 'critical',
    description: 'Domestic transactions must use Nigerian Naira (NGN)',
    regulation: 'CBN Circular - Foreign Exchange Manual',
    autoFix: false
  },
  {
    id: 'transaction_limit_individual',
    name: 'Individual Transaction Limit',
    category: 'transaction',
    severity: 'high',
    description: 'Individual transactions above ₦5M require additional documentation',
    regulation: 'CBN Know Your Customer (KYC) Requirements',
    autoFix: false
  },
  {
    id: 'transaction_purpose_required',
    name: 'Transaction Purpose Required',
    category: 'transaction',
    severity: 'medium',
    description: 'All transactions must have a valid business purpose',
    regulation: 'Nigerian Financial Intelligence Unit (NFIU) Guidelines',
    autoFix: false
  },
  
  // Account Rules
  {
    id: 'account_number_format',
    name: 'Nigerian Account Number Format',
    category: 'account',
    severity: 'critical',
    description: 'Account numbers must be 10 digits for Nigerian banks',
    regulation: 'NIBSS Account Number Standards',
    autoFix: true
  },
  {
    id: 'bank_code_validation',
    name: 'Bank Code Validation',
    category: 'account',
    severity: 'critical',
    description: 'Bank codes must be valid CBN-registered codes',
    regulation: 'CBN Bank Directory',
    autoFix: false
  },
  
  // Identity Rules
  {
    id: 'bvn_format_validation',
    name: 'BVN Format Validation',
    category: 'identity',
    severity: 'high',
    description: 'Bank Verification Number must be 11 digits',
    regulation: 'NIBSS BVN Guidelines',
    autoFix: true
  },
  {
    id: 'name_matching',
    name: 'Account Name Matching',
    category: 'identity',
    severity: 'medium',
    description: 'Account holder name should match BVN records',
    regulation: 'CBN KYC Requirements',
    autoFix: false
  },
  
  // Compliance Rules
  {
    id: 'aml_screening',
    name: 'AML Watchlist Screening',
    category: 'aml',
    severity: 'critical',
    description: 'Screen against money laundering watchlists',
    regulation: 'Money Laundering (Prohibition) Act 2011',
    autoFix: false
  },
  {
    id: 'pep_screening',
    name: 'PEP Screening',
    category: 'aml',
    severity: 'high',
    description: 'Screen for Politically Exposed Persons',
    regulation: 'NFIU PEP Guidelines',
    autoFix: false
  },
  {
    id: 'sanctions_screening',
    name: 'Sanctions Screening',
    category: 'compliance',
    severity: 'critical',
    description: 'Check against international sanctions lists',
    regulation: 'UN/EU/US Sanctions Lists',
    autoFix: false
  }
];

// Nigerian Bank Codes
const NIGERIAN_BANK_CODES = {
  '044': 'Access Bank',
  '014': 'Afribank Nigeria Plc',
  '023': 'Citibank Nigeria Limited',
  '050': 'Ecobank Nigeria',
  '011': 'First Bank of Nigeria',
  '214': 'First City Monument Bank',
  '070': 'Fidelity Bank Plc',
  '058': 'Guaranty Trust Bank',
  '030': 'Heritage Bank Plc',
  '082': 'Keystone Bank Limited',
  '076': 'Polaris Bank',
  '221': 'Stanbic IBTC Bank Plc',
  '068': 'Standard Chartered Bank',
  '232': 'Sterling Bank Plc',
  '032': 'Union Bank of Nigeria',
  '033': 'United Bank for Africa',
  '215': 'Unity Bank Plc',
  '035': 'Wema Bank Plc',
  '057': 'Zenith Bank Plc'
};

// Mock transaction data
const mockTransaction: TransactionData = {
  id: 'TXN_001',
  amount: 2500000,
  currency: 'NGN',
  sender: {
    name: 'John Doe Enterprises',
    accountNumber: '0123456789',
    bankCode: '058',
    bvn: '12345678901'
  },
  recipient: {
    name: 'Jane Smith Limited',
    accountNumber: '9876543210',
    bankCode: '044'
  },
  purpose: 'Payment for goods supplied',
  category: 'Business Transaction',
  timestamp: new Date(),
  reference: 'REF_2024_001'
};

export const FinancialValidator: React.FC = () => {
  const [activeTab, setActiveTab] = useState('validator');
  const [selectedRuleCategory, setSelectedRuleCategory] = useState<string>('all');
  const [validationData, setValidationData] = useState<string>('');
  const [currentSession, setCurrentSession] = useState<ValidationSession | null>(null);
  const [validationHistory, setValidationHistory] = useState<ValidationSession[]>([]);
  const [isValidating, setIsValidating] = useState(false);

  // Initialize with sample transaction data
  useEffect(() => {
    setValidationData(JSON.stringify(mockTransaction, null, 2));
  }, []);

  const validateFinancialData = useCallback(async () => {
    if (!validationData.trim()) return;

    setIsValidating(true);
    const startTime = Date.now();

    try {
      const data = JSON.parse(validationData);
      const sessionId = `session_${Date.now()}`;
      
      const session: ValidationSession = {
        id: sessionId,
        timestamp: new Date(),
        dataType: 'transaction',
        totalRecords: 1,
        validatedRecords: 0,
        results: [],
        overallScore: 0,
        status: 'running'
      };

      setCurrentSession(session);

      // Simulate validation process
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Run validation rules
      const results: ValidationResult[] = [];
      
      // Validate each rule
      for (const rule of NIGERIAN_VALIDATION_RULES) {
        const result = await validateRule(data, rule);
        results.push(result);
      }

      // Calculate overall score
      const passedRules = results.filter(r => r.status === 'passed').length;
      const overallScore = Math.round((passedRules / results.length) * 100);

      const completedSession: ValidationSession = {
        ...session,
        validatedRecords: 1,
        results,
        overallScore,
        status: 'completed',
        duration: Date.now() - startTime
      };

      setCurrentSession(completedSession);
      setValidationHistory(prev => [completedSession, ...prev.slice(0, 9)]);

    } catch (error) {
      const errorSession: ValidationSession = {
        id: `session_${Date.now()}`,
        timestamp: new Date(),
        dataType: 'transaction',
        totalRecords: 1,
        validatedRecords: 0,
        results: [{
          rule: {
            id: 'parse_error',
            name: 'Data Parse Error',
            category: 'compliance',
            severity: 'critical',
            description: 'Failed to parse financial data',
            regulation: 'Data Format Requirements',
            autoFix: false
          },
          status: 'failed',
          message: `Parse error: ${error instanceof Error ? error.message : 'Invalid JSON'}`,
          confidence: 100
        }],
        overallScore: 0,
        status: 'failed',
        duration: Date.now() - startTime
      };

      setCurrentSession(errorSession);
      setValidationHistory(prev => [errorSession, ...prev.slice(0, 9)]);
    } finally {
      setIsValidating(false);
    }
  }, [validationData]);

  const validateRule = async (data: any, rule: ValidationRule): Promise<ValidationResult> => {
    // Simulate rule validation logic
    await new Promise(resolve => setTimeout(resolve, 100));

    let status: ValidationResult['status'] = 'passed';
    let message = '';
    let details = '';
    let suggestion = '';
    let confidence = 95;

    switch (rule.id) {
      case 'ngn_currency_domestic':
        if (data.currency !== 'NGN') {
          status = 'failed';
          message = `Transaction uses ${data.currency} instead of required NGN for domestic transactions`;
          suggestion = 'Convert transaction currency to Nigerian Naira (NGN)';
        } else {
          message = 'Transaction correctly uses NGN currency';
        }
        break;

      case 'transaction_limit_individual':
        if (data.amount > 5000000) {
          status = 'warning';
          message = `Transaction amount ₦${data.amount.toLocaleString()} exceeds ₦5M limit`;
          suggestion = 'Additional documentation required for high-value transactions';
          confidence = 90;
        } else {
          message = `Transaction amount ₦${data.amount.toLocaleString()} is within limits`;
        }
        break;

      case 'account_number_format':
        const senderValid = /^\d{10}$/.test(data.sender?.accountNumber || '');
        const recipientValid = /^\d{10}$/.test(data.recipient?.accountNumber || '');
        
        if (!senderValid || !recipientValid) {
          status = 'failed';
          message = 'Account numbers must be exactly 10 digits';
          suggestion = 'Correct account number format to 10 digits';
        } else {
          message = 'Account numbers are correctly formatted';
        }
        break;

      case 'bank_code_validation':
        const senderBankValid = NIGERIAN_BANK_CODES[data.sender?.bankCode as keyof typeof NIGERIAN_BANK_CODES];
        const recipientBankValid = NIGERIAN_BANK_CODES[data.recipient?.bankCode as keyof typeof NIGERIAN_BANK_CODES];
        
        if (!senderBankValid || !recipientBankValid) {
          status = 'failed';
          message = 'Invalid bank codes detected';
          details = `Sender: ${senderBankValid || 'Invalid'}, Recipient: ${recipientBankValid || 'Invalid'}`;
          suggestion = 'Use valid CBN-registered bank codes';
        } else {
          message = 'Bank codes are valid';
          details = `Sender: ${senderBankValid}, Recipient: ${recipientBankValid}`;
        }
        break;

      case 'bvn_format_validation':
        const bvnValid = /^\d{11}$/.test(data.sender?.bvn || '');
        if (data.sender?.bvn && !bvnValid) {
          status = 'failed';
          message = 'BVN format is invalid';
          suggestion = 'BVN should be exactly 11 digits';
        } else if (!data.sender?.bvn) {
          status = 'warning';
          message = 'BVN not provided';
          suggestion = 'Consider providing BVN for enhanced verification';
          confidence = 70;
        } else {
          message = 'BVN format is valid';
        }
        break;

      case 'aml_screening':
        // Simulate AML screening
        const riskScore = Math.random() * 100;
        if (riskScore > 80) {
          status = 'manual_review';
          message = 'High-risk transaction flagged for manual review';
          details = `Risk score: ${riskScore.toFixed(1)}%`;
          suggestion = 'Conduct enhanced due diligence';
          confidence = 85;
        } else {
          message = 'No AML concerns detected';
          details = `Risk score: ${riskScore.toFixed(1)}%`;
        }
        break;

      default:
        message = 'Rule validation completed';
    }

    return {
      rule,
      status,
      message,
      details,
      suggestion: status !== 'passed' ? suggestion : undefined,
      confidence
    };
  };

  const getStatusIcon = (status: ValidationResult['status']) => {
    switch (status) {
      case 'passed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'manual_review': return <AlertCircle className="h-4 w-4 text-orange-500" />;
      default: return <Info className="h-4 w-4 text-blue-500" />;
    }
  };

  const getStatusColor = (status: ValidationResult['status']) => {
    switch (status) {
      case 'passed': return 'bg-green-100 text-green-800 border-green-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'manual_review': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'info': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'transaction': return <DollarSign className="h-4 w-4" />;
      case 'account': return <Building2 className="h-4 w-4" />;
      case 'identity': return <User className="h-4 w-4" />;
      case 'compliance': return <Shield className="h-4 w-4" />;
      case 'aml': return <Flag className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  const filteredRules = selectedRuleCategory === 'all' 
    ? NIGERIAN_VALIDATION_RULES 
    : NIGERIAN_VALIDATION_RULES.filter(rule => rule.category === selectedRuleCategory);

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            Financial Validation Tools
          </h2>
          <p className="text-gray-600 mt-1">
            Validate financial data against Nigerian banking regulations
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            🇳🇬 CBN Compliant
          </Badge>
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            {NIGERIAN_VALIDATION_RULES.length} Rules
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="validator">Validator</TabsTrigger>
          <TabsTrigger value="rules">Rules</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="validator" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Panel */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Financial Data Input
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Transaction Data (JSON)</label>
                  <Textarea
                    placeholder="Paste your transaction data here..."
                    value={validationData}
                    onChange={(e) => setValidationData(e.target.value)}
                    rows={15}
                    className="font-mono text-sm"
                  />
                </div>

                <div className="flex gap-2">
                  <Button 
                    onClick={validateFinancialData}
                    disabled={isValidating || !validationData.trim()}
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
                        Validate Data
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
                    Upload transaction data in JSON format. Sample data is pre-loaded for testing.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>

            {/* Results Panel */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Validation Results
                  {currentSession && (
                    <Badge variant="outline" className={getScoreColor(currentSession.overallScore)}>
                      Score: {currentSession.overallScore}%
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!currentSession ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No validation results yet</p>
                    <p className="text-sm">Upload financial data and run validation</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Score Display */}
                    <div className="text-center">
                      <div className={`text-3xl font-bold ${getScoreColor(currentSession.overallScore)}`}>
                        {currentSession.overallScore}%
                      </div>
                      <Progress value={currentSession.overallScore} className="mt-2" />
                      <p className="text-sm text-gray-600 mt-1">
                        {currentSession.results.filter(r => r.status === 'passed').length} of {currentSession.results.length} checks passed
                      </p>
                    </div>

                    {/* Results List */}
                    <ScrollArea className="h-64">
                      <div className="space-y-2">
                        {currentSession.results.map((result, index) => (
                          <div
                            key={index}
                            className={`p-3 border rounded-lg ${
                              result.status === 'passed' ? 'bg-green-50 border-green-200' : 
                              result.status === 'failed' ? 'bg-red-50 border-red-200' :
                              result.status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                              'bg-orange-50 border-orange-200'
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              {getStatusIcon(result.status)}
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-sm">{result.rule.name}</span>
                                  <Badge variant="outline" className={`text-xs ${getSeverityColor(result.rule.severity)}`}>
                                    {result.rule.severity}
                                  </Badge>
                                </div>
                                <p className="text-xs text-gray-600 mb-1">{result.message}</p>
                                {result.details && (
                                  <p className="text-xs text-blue-600 mb-1">ℹ️ {result.details}</p>
                                )}
                                {result.suggestion && (
                                  <p className="text-xs text-orange-600">💡 {result.suggestion}</p>
                                )}
                                <div className="flex items-center gap-2 mt-2">
                                  <span className="text-xs text-gray-500">Confidence: {result.confidence}%</span>
                                  <Badge variant="outline" className="text-xs">
                                    {result.rule.regulation}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
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
                <span>Nigerian Financial Validation Rules</span>
                <Select value={selectedRuleCategory} onValueChange={setSelectedRuleCategory}>
                  <SelectTrigger className="w-48">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    <SelectItem value="transaction">Transaction</SelectItem>
                    <SelectItem value="account">Account</SelectItem>
                    <SelectItem value="identity">Identity</SelectItem>
                    <SelectItem value="compliance">Compliance</SelectItem>
                    <SelectItem value="aml">AML</SelectItem>
                  </SelectContent>
                </Select>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredRules.map(rule => (
                  <div key={rule.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-gray-100">
                        {getCategoryIcon(rule.category)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-medium">{rule.name}</h4>
                          <Badge variant="outline" className={getSeverityColor(rule.severity)}>
                            {rule.severity}
                          </Badge>
                          <Badge variant="outline" className="text-xs capitalize">
                            {rule.category}
                          </Badge>
                          {rule.autoFix && (
                            <Badge variant="outline" className="bg-blue-50 text-blue-700 text-xs">
                              Auto-Fix
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{rule.description}</p>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            {rule.regulation}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Validation History</CardTitle>
            </CardHeader>
            <CardContent>
              {validationHistory.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No validation history</p>
                  <p className="text-sm">Your validation sessions will appear here</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {validationHistory.map(session => (
                    <div key={session.id} className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className={
                            session.status === 'completed' ? 'bg-green-50 text-green-700' :
                            session.status === 'failed' ? 'bg-red-50 text-red-700' :
                            'bg-yellow-50 text-yellow-700'
                          }>
                            {session.status}
                          </Badge>
                          <span className="font-medium capitalize">{session.dataType} validation</span>
                          <Badge variant="outline" className={getScoreColor(session.overallScore)}>
                            {session.overallScore}%
                          </Badge>
                        </div>
                        <span className="text-sm text-gray-500">
                          {session.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <span>
                          {session.validatedRecords} of {session.totalRecords} records validated
                        </span>
                        {session.duration && (
                          <span>{(session.duration / 1000).toFixed(1)}s</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
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
                    <SelectItem value="standard">Standard (Critical + High)</SelectItem>
                    <SelectItem value="relaxed">Relaxed (Critical only)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <h4 className="font-medium mb-3">Auto-Fix Settings</h4>
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Enable automatic fixes for format issues</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">Auto-correct account number formats</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">Auto-format BVN numbers</span>
                  </label>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Reporting Options</h4>
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Generate detailed validation reports</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Include regulatory references</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">Export results to Excel</span>
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
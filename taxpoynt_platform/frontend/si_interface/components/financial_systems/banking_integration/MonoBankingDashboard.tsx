/**
 * Mono Banking Integration Dashboard
 * =================================
 * 
 * System Integrator interface for managing Mono Open Banking connections.
 * Provides comprehensive banking integration capabilities for Nigerian banks
 * through Mono's Open Banking API.
 * 
 * Features:
 * - Account linking and management
 * - Transaction data collection and analysis
 * - Real-time transaction monitoring
 * - Automated invoice generation triggers
 * - Banking compliance and security
 * - Multi-bank integration support
 */

import React, { useState, useEffect } from 'react';
import { useRoleDetector } from '../../../role_management';

// Types based on backend Mono integration
interface MonoAccount {
  id: string;
  name: string;
  accountNumber: string;
  accountType: 'SAVINGS' | 'CURRENT' | 'DOMICILIARY' | 'FIXED_DEPOSIT';
  bank: {
    name: string;
    code: string;
    logo?: string;
  };
  balance: {
    current: number;
    available: number;
    currency: string;
  };
  status: 'connected' | 'disconnected' | 'reauthorization_required';
  lastSync: Date;
  linkedAt: Date;
}

interface MonoTransaction {
  id: string;
  amount: number;
  type: 'credit' | 'debit';
  narration: string;
  date: Date;
  reference: string;
  category: string;
  balance: number;
  meta?: {
    customerName?: string;
    customerPhone?: string;
    invoiceGenerated?: boolean;
  };
}

interface BankingConnectionStats {
  totalAccounts: number;
  connectedBanks: number;
  totalTransactions: number;
  monthlyVolume: number;
  invoicesGenerated: number;
  lastSyncTime: Date;
}

// Nigerian Banks supported by Mono
const SUPPORTED_BANKS = [
  { code: '044', name: 'Access Bank', logo: '🏦' },
  { code: '014', name: 'Afribank', logo: '🏛️' },
  { code: '030', name: 'Heritage Bank', logo: '🏢' },
  { code: '058', name: 'GTBank', logo: '💎' },
  { code: '032', name: 'Union Bank', logo: '🏪' },
  { code: '011', name: 'First Bank', logo: '🏛️' },
  { code: '221', name: 'Stanbic IBTC', logo: '⭐' },
  { code: '068', name: 'Standard Chartered', logo: '🌟' },
  { code: '035', name: 'Wema Bank', logo: '💚' },
  { code: '057', name: 'Zenith Bank', logo: '🔵' }
];

export const MonoBankingDashboard: React.FC = () => {
  const { detectionResult } = useRoleDetector();
  
  const [accounts, setAccounts] = useState<MonoAccount[]>([]);
  const [transactions, setTransactions] = useState<MonoTransaction[]>([]);
  const [stats, setStats] = useState<BankingConnectionStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAccount, setSelectedAccount] = useState<string | null>(null);
  const [showLinkAccount, setShowLinkAccount] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load banking data
  useEffect(() => {
    loadBankingData();
  }, []);

  const loadBankingData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch from SI banking endpoints
      const [accountsRes, statsRes] = await Promise.all([
        fetch('/api/v1/si/banking/open-banking', {
          headers: { 
            'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
            'Content-Type': 'application/json'
          }
        }),
        fetch('/api/v1/si/banking/stats', {
          headers: { 
            'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
            'Content-Type': 'application/json'
          }
        })
      ]);

      if (!accountsRes.ok || !statsRes.ok) {
        throw new Error('Failed to load banking data');
      }

      const accountsData = await accountsRes.json();
      const statsData = await statsRes.json();

      setAccounts(accountsData.data?.connections || []);
      setStats(statsData.data || null);

      // Load transactions for first account
      if (accountsData.data?.connections?.length > 0) {
        setSelectedAccount(accountsData.data.connections[0].id);
        loadTransactions(accountsData.data.connections[0].id);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load banking data');
    } finally {
      setIsLoading(false);
    }
  };

  const loadTransactions = async (accountId: string) => {
    try {
      const response = await fetch(`/api/v1/si/banking/open-banking/${accountId}/transactions?limit=50`, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load transactions');
      }

      const data = await response.json();
      setTransactions(data.data?.transactions || []);
      
    } catch (err) {
      console.error('Failed to load transactions:', err);
    }
  };

  const initiateAccountLinking = async (bankCode: string) => {
    try {
      const response = await fetch('/api/v1/si/banking/open-banking/mono/link', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer: {
            name: detectionResult?.organizationId || 'Unknown',
            email: 'admin@organization.com'
          },
          redirect_url: `${window.location.origin}/si/banking/callback`,
          meta: {
            ref: `taxpoynt_${Date.now()}`,
            bank_code: bankCode
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to initiate account linking');
      }

      const data = await response.json();
      
      // Redirect to Mono's account linking page
      if (data.data?.mono_url) {
        window.open(data.data.mono_url, '_blank');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to link account');
    }
  };

  const syncAccount = async (accountId: string) => {
    try {
      const response = await fetch(`/api/v1/si/banking/open-banking/${accountId}/sync`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to sync account');
      }

      // Reload data after sync
      await loadBankingData();
      if (selectedAccount) {
        await loadTransactions(selectedAccount);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync account');
    }
  };

  const generateInvoiceFromTransaction = async (transactionId: string) => {
    try {
      const response = await fetch('/api/v1/si/banking/transactions/generate-invoice', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transaction_id: transactionId,
          auto_submit: false
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate invoice');
      }

      const data = await response.json();
      
      // Update transaction to show invoice generated
      setTransactions(prev => prev.map(tx => 
        tx.id === transactionId 
          ? { ...tx, meta: { ...tx.meta, invoiceGenerated: true } }
          : tx
      ));

      alert(`Invoice generated successfully: ${data.data?.invoice_id}`);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate invoice');
    }
  };

  const formatCurrency = (amount: number, currency = 'NGN') => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString('en-NG', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
          <div className="h-96 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Banking Integration Dashboard
          </h1>
          <p className="text-gray-600">
            Manage Nigerian bank connections via Mono Open Banking
          </p>
        </div>
        <button
          onClick={() => setShowLinkAccount(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Link New Account
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <span className="text-red-600 mr-2">⚠️</span>
            <span className="text-red-800">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.totalAccounts}
                </div>
                <div className="text-gray-600">Connected Accounts</div>
              </div>
              <div className="text-blue-600 text-3xl">🏦</div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.connectedBanks}
                </div>
                <div className="text-gray-600">Nigerian Banks</div>
              </div>
              <div className="text-green-600 text-3xl">🏛️</div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatCurrency(stats.monthlyVolume)}
                </div>
                <div className="text-gray-600">Monthly Volume</div>
              </div>
              <div className="text-purple-600 text-3xl">💰</div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {stats.invoicesGenerated}
                </div>
                <div className="text-gray-600">Invoices Generated</div>
              </div>
              <div className="text-orange-600 text-3xl">📄</div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Connected Accounts */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Connected Accounts ({accounts.length})
            </h3>
            
            <div className="space-y-4">
              {accounts.map((account) => (
                <div
                  key={account.id}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                    selectedAccount === account.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => {
                    setSelectedAccount(account.id);
                    loadTransactions(account.id);
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      <span className="text-2xl mr-3">{account.bank.logo || '🏦'}</span>
                      <div>
                        <div className="font-medium text-gray-900">
                          {account.bank.name}
                        </div>
                        <div className="text-sm text-gray-600">
                          ****{account.accountNumber.slice(-4)}
                        </div>
                      </div>
                    </div>
                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                      account.status === 'connected' 
                        ? 'bg-green-100 text-green-800'
                        : account.status === 'reauthorization_required'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {account.status.replace('_', ' ')}
                    </div>
                  </div>
                  
                  <div className="text-lg font-semibold text-gray-900 mb-1">
                    {formatCurrency(account.balance.available)}
                  </div>
                  
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>{account.accountType}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        syncAccount(account.id);
                      }}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      🔄 Sync
                    </button>
                  </div>
                </div>
              ))}
              
              {accounts.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">🏦</div>
                  <div className="text-lg font-medium mb-2">No accounts connected</div>
                  <div className="text-sm">Link your first Nigerian bank account to get started</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Transactions */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Recent Transactions
              </h3>
              {selectedAccount && (
                <button
                  onClick={() => loadTransactions(selectedAccount)}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  🔄 Refresh
                </button>
              )}
            </div>
            
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-center flex-1">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center mr-4 ${
                      transaction.type === 'credit' 
                        ? 'bg-green-100 text-green-600' 
                        : 'bg-red-100 text-red-600'
                    }`}>
                      {transaction.type === 'credit' ? '↓' : '↑'}
                    </div>
                    
                    <div className="flex-1">
                      <div className="font-medium text-gray-900 mb-1">
                        {transaction.narration}
                      </div>
                      <div className="text-sm text-gray-600">
                        {formatDate(transaction.date)} • Ref: {transaction.reference}
                      </div>
                      {transaction.meta?.customerName && (
                        <div className="text-sm text-blue-600">
                          Customer: {transaction.meta.customerName}
                        </div>
                      )}
                    </div>
                    
                    <div className="text-right mr-4">
                      <div className={`text-lg font-semibold ${
                        transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {transaction.type === 'credit' ? '+' : '-'}{formatCurrency(Math.abs(transaction.amount))}
                      </div>
                      <div className="text-sm text-gray-600">
                        Balance: {formatCurrency(transaction.balance)}
                      </div>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    {transaction.meta?.invoiceGenerated ? (
                      <span className="px-3 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                        Invoice Generated
                      </span>
                    ) : transaction.type === 'credit' && transaction.amount >= 1000 ? (
                      <button
                        onClick={() => generateInvoiceFromTransaction(transaction.id)}
                        className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
                      >
                        Generate Invoice
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
              
              {transactions.length === 0 && selectedAccount && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">📊</div>
                  <div className="text-lg font-medium mb-2">No transactions found</div>
                  <div className="text-sm">Transactions will appear here after account sync</div>
                </div>
              )}
              
              {!selectedAccount && (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-4">👈</div>
                  <div className="text-lg font-medium mb-2">Select an account</div>
                  <div className="text-sm">Choose a connected account to view transactions</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Link Account Modal */}
      {showLinkAccount && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Link Nigerian Bank Account
              </h3>
              <button
                onClick={() => setShowLinkAccount(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <p className="text-gray-600 mb-6">
              Select your bank to connect via Mono Open Banking. Your data is secure and encrypted.
            </p>
            
            <div className="grid grid-cols-2 gap-3">
              {SUPPORTED_BANKS.map((bank) => (
                <button
                  key={bank.code}
                  onClick={() => {
                    initiateAccountLinking(bank.code);
                    setShowLinkAccount(false);
                  }}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                >
                  <span className="text-2xl mr-3">{bank.logo}</span>
                  <span className="text-sm font-medium text-gray-900">
                    {bank.name}
                  </span>
                </button>
              ))}
            </div>
            
            <div className="mt-6 text-xs text-gray-500">
              <p>🔒 Powered by Mono • Bank-grade security • CBN licensed</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MonoBankingDashboard;
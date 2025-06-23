import React, { useEffect, useState } from 'react';
import { TransactionsList } from './TransactionsList';
import { POSConnectorCard } from './POSConnectorCard';
import { RealTimeStats } from './RealTimeStats';
import { useTransactions } from '../../../hooks/useTransactions';

const POSDashboard: React.FC = () => {
  const { transactions, isLoading, error, fetchTransactions } = useTransactions();
  const [refreshInterval, setRefreshInterval] = useState<number>(30); // seconds
  
  useEffect(() => {
    // Initial fetch
    fetchTransactions();
    
    // Setup polling interval for real-time updates
    const intervalId = setInterval(() => {
      fetchTransactions();
    }, refreshInterval * 1000);
    
    return () => clearInterval(intervalId);
  }, [refreshInterval]);
  
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-4">
        <h2 className="text-2xl font-semibold mb-4">POS Integration Dashboard</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <POSConnectorCard />
          <RealTimeStats />
        </div>
        
        <TransactionsList 
          transactions={transactions} 
          isLoading={isLoading} 
          error={error} 
        />
      </div>
    </div>
  );
};

export default POSDashboard;
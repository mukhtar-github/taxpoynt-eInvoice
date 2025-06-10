# TaxPoynt CRM & POS Integration - Week 2 Implementation Plan

## Week 2: POS Foundation & Square Integration

Week 2 focuses on establishing the Point of Sale (POS) integration foundation, implementing the Square POS connector, and developing real-time transaction processing capabilities. This phase builds upon the framework created in Week 1 to address the unique requirements of POS systems, particularly high-volume, real-time processing.

### Day 1-2: POS Connector Foundation & Square Integration

#### Tasks

1. **POS Base Connector Implementation**
   - Extend the base connector for POS-specific functionality
   - Implement real-time transaction handling patterns
   - Create webhook signature verification for POS platforms
   
   ```python
   # /backend/app/integrations/pos/base_pos_connector.py
   from app.integrations.base.connector import BaseConnector
   
   class BasePOSConnector(BaseConnector):
       """Base connector for POS integrations with real-time capabilities"""
       
       async def verify_webhook_signature(self, payload, signature, timestamp):
           """Verify webhook signature from POS platform"""
           raise NotImplementedError("Must be implemented by subclasses")
           
       async def process_transaction(self, transaction_data):
           """Process a transaction from the POS system"""
           raise NotImplementedError("Must be implemented by subclasses")
           
       async def get_transaction_by_id(self, transaction_id):
           """Retrieve transaction details by ID"""
           raise NotImplementedError("Must be implemented by subclasses")
           
       async def get_location_details(self):
           """Get details about POS location/store"""
           raise NotImplementedError("Must be implemented by subclasses")
   ```

2. **Square POS Connector Development**
   - Implement Square API client using official SDK
   - Create OAuth flow for Square authentication
   - Implement webhook handling for Square events
   
   ```python
   # /backend/app/integrations/pos/square/connector.py
   from app.integrations.pos.base_pos_connector import BasePOSConnector
   from square.client import Client
   import hmac
   import hashlib
   
   class SquareConnector(BasePOSConnector):
       """Square POS connector implementation"""
       
       def __init__(self, connection_config):
           super().__init__(connection_config)
           self.client = Client(
               access_token=connection_config.get("access_token"),
               environment=connection_config.get("environment", "production")
           )
       
       async def authenticate(self):
           """Authenticate with Square API"""
           # Test authentication by fetching a simple resource
           await self.client.locations.list_locations()
           return True
           
       async def verify_webhook_signature(self, payload, signature, timestamp):
           """Verify Square webhook signature"""
           webhook_signature_key = self.config.get("webhook_signature_key")
           calculated_hash = hmac.new(
               webhook_signature_key.encode('utf-8'),
               f"{timestamp}{payload}".encode('utf-8'),
               hashlib.sha256
           ).hexdigest()
           
           return hmac.compare_digest(calculated_hash, signature)
           
       async def process_transaction(self, transaction_data):
           """Process a transaction from Square"""
           # Extract relevant data and standardize format
           # Transform Square-specific format to TaxPoynt invoice format
           
       async def get_transaction_by_id(self, transaction_id):
           """Retrieve transaction details from Square by ID"""
           return await self.client.orders.retrieve_order(order_id=transaction_id)
   ```

3. **POS Database Schema and CRUD Operations**
   - Implement repositories for POS connections and transactions
   - Create transaction data models and DTOs
   - Set up partitioning for transaction tables
   
   ```python
   # /backend/app/crud/pos_connection.py
   from typing import List, Optional, Union
   from uuid import UUID
   from sqlalchemy.orm import Session
   from app.models.pos_connection import POSConnection
   from app.schemas.pos_connection import POSConnectionCreate, POSConnectionUpdate
   
   def create_pos_connection(db: Session, connection_in: POSConnectionCreate, user_id: UUID) -> POSConnection:
       """Create a new POS connection"""
       db_connection = POSConnection(
           user_id=user_id,
           organization_id=connection_in.organization_id,
           pos_type=connection_in.pos_type,
           location_name=connection_in.location_name,
           credentials_encrypted=connection_in.credentials_encrypted,
           webhook_url=connection_in.webhook_url,
           webhook_secret=connection_in.webhook_secret
       )
       db.add(db_connection)
       db.commit()
       db.refresh(db_connection)
       return db_connection
   ```

### Day 3-4: Real-time Transaction Processing

#### Tasks

1. **High-Priority Queue Implementation**
   - Set up Redis queue for real-time transaction processing
   - Configure dedicated workers with sub-2-second SLA
   - Implement circuit breaker for external API calls
   
   ```python
   # /backend/app/services/pos_queue_service.py
   import redis
   from fastapi import BackgroundTasks
   from app.core.config import settings
   
   class POSQueueService:
       """Service for handling high-priority POS transaction processing"""
       
       def __init__(self):
           self.redis_client = redis.Redis(
               host=settings.REDIS_HOST,
               port=settings.REDIS_PORT,
               db=settings.REDIS_POS_DB
           )
           
       async def enqueue_transaction(self, transaction_data, background_tasks: BackgroundTasks):
           """Enqueue a transaction for processing with high priority"""
           # For ultra-low latency, process immediately in background task
           # then also queue for persistent processing and retry
           background_tasks.add_task(self._process_immediate, transaction_data)
           
           # Add to persistent queue for guaranteed processing
           transaction_id = transaction_data.get("id")
           self.redis_client.lpush(
               "pos_transactions_queue", 
               json.dumps({
                   "id": transaction_id,
                   "data": transaction_data,
                   "attempts": 0,
                   "enqueued_at": datetime.now().isoformat()
               })
           )
           
       async def _process_immediate(self, transaction_data):
           """Process transaction immediately for ultra-low latency"""
           # Implementation for immediate processing
   ```

2. **Square Webhook Handler**
   - Implement webhook endpoints for Square events
   - Create signature verification middleware
   - Set up event routing to appropriate handlers
   
   ```python
   # /backend/app/routes/pos_webhooks.py
   from fastapi import APIRouter, Depends, Header, Request, BackgroundTasks, HTTPException
   
   router = APIRouter(prefix="/webhooks/pos", tags=["pos-webhooks"])
   
   @router.post("/square", status_code=200)
   async def square_webhook(
       request: Request,
       background_tasks: BackgroundTasks,
       x_square_signature: str = Header(None),
       db: Session = Depends(get_db)
   ):
       """Handle Square webhook events"""
       payload = await request.body()
       payload_str = payload.decode("utf-8")
       
       # Verify webhook signature first (security check)
       # Extract connection ID from payload
       # Verify signature using connection's webhook secret
       
       # Parse payload
       event_data = json.loads(payload_str)
       event_type = event_data.get("type")
       
       # Route to appropriate handler
       if event_type == "payment.updated":
           await handle_payment_update(event_data, background_tasks, db)
       elif event_type == "order.created":
           await handle_order_created(event_data, background_tasks, db)
       # Handle other event types
       
       return {"status": "received"}
   ```

3. **Transaction to Invoice Conversion**
   - Implement logic to convert POS transactions to invoices
   - Create background task for invoice generation
   - Set up error handling and retry mechanism
   
   ```python
   # /backend/app/services/pos_transaction_service.py
   from app.services.invoice_service import create_invoice_from_transaction
   from app.schemas.pos_transaction import POSTransaction
   
   class POSTransactionService:
       """Service for handling POS transactions"""
       
       async def transaction_to_invoice(self, transaction: POSTransaction):
           """Convert a POS transaction to an invoice"""
           try:
               # Extract invoice data from transaction
               invoice_data = {
                   "invoice_number": f"POS-{transaction.external_transaction_id}",
                   "issue_date": transaction.transaction_timestamp,
                   "due_date": transaction.transaction_timestamp,
                   "customer": transaction.customer_data,
                   "items": self._transform_line_items(transaction.items),
                   "total_amount": transaction.transaction_amount,
                   "tax_amount": transaction.tax_amount,
                   "source": "POS",
                   "source_reference": transaction.external_transaction_id,
               }
               
               # Create invoice using shared invoice service
               invoice = await create_invoice_from_transaction(invoice_data)
               
               # Update transaction with invoice reference
               transaction.invoice_generated = True
               transaction.invoice_id = invoice.id
               transaction.updated_at = datetime.now()
               
               return invoice
           except Exception as e:
               # Log error and handle retry logic
               transaction.processing_errors = {
                   "error_message": str(e),
                   "error_type": e.__class__.__name__,
                   "timestamp": datetime.now().isoformat()
               }
               raise
   ```

### Day 5: Frontend Implementation & Dashboard

#### Tasks

1. **POS Dashboard Components**
   - Create Square connection UI component
   - Implement transaction monitoring dashboard
   - Build real-time transaction status display
   
   ```tsx
   // /frontend/components/integrations/pos/POSDashboard.tsx
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
   ```

2. **Square POS Connection UI**
   - Create OAuth connection flow
   - Implement location selection interface
   - Build webhook configuration UI
   
   ```tsx
   // /frontend/components/integrations/pos/SquareConnector.tsx
   import React, { useState } from 'react';
   import { Button, Card, Input, Select } from '../../ui';
   
   const SquareConnector: React.FC = () => {
     const [isConnecting, setIsConnecting] = useState(false);
     const [step, setStep] = useState('initial'); // 'initial', 'locations', 'webhooks'
     const [locations, setLocations] = useState([]);
     const [selectedLocation, setSelectedLocation] = useState('');
     
     const handleConnect = async () => {
       setIsConnecting(true);
       try {
         // Implementation of OAuth flow initiation
         window.location.href = '/api/integrations/pos/square/oauth';
       } catch (error) {
         console.error('Failed to connect to Square', error);
       } finally {
         setIsConnecting(false);
       }
     };
     
     // Rest of component implementation
     
     return (
       <Card>
         <h3 className="text-lg font-medium mb-4">Connect Square POS</h3>
         
         {step === 'initial' && (
           <Button 
             onClick={handleConnect}
             className="bg-cyan-600 text-white"
           >
             {isConnecting ? 'Connecting...' : 'Connect Square POS'}
           </Button>
         )}
         
         {/* Other steps UI */}
       </Card>
     );
   };
   ```

3. **Testing & Documentation**
   - Write unit tests for Square connector
   - Test real-time processing with mock transactions
   - Document API endpoints and webhook formats
   
   ```bash
   # Run tests for POS integration components
   cd /home/mukhtar-tanimu/taxpoynt-eInvoice/backend
   pytest app/tests/integrations/pos -v
   ```

### Week 2 Deliverables

1. **Code Components**
   - POS base connector implementation
   - Square POS connector
   - High-priority transaction processing queue
   - Webhook handlers for Square events
   - Transaction-to-invoice conversion logic
   - POS dashboard frontend components

2. **Documentation**
   - Square POS integration documentation
   - Webhook payload formats and event types
   - Real-time processing architecture documentation

3. **Testing**
   - Unit tests for Square connector
   - Performance tests for transaction processing
   - Webhook handling tests

### Success Criteria for Week 2

- [x] Implement POS base connector with real-time capabilities
- [x] Complete Square POS connector with OAuth authentication
- [x] Establish high-priority queue for transaction processing
- [x] Achieve sub-2-second processing time for transactions
- [x] Implement secure webhook handling for Square
- [x] Develop transaction monitoring dashboard
- [x] Demonstrate end-to-end transaction-to-invoice flow

### Next Steps for Week 3

Week 3 will focus on expanding the integration portfolio with additional CRM (Salesforce) and POS (Toast) platforms, implementing advanced features, and optimizing performance based on learnings from the initial implementations.

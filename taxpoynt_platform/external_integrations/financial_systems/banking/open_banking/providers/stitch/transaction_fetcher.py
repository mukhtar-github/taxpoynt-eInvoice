"""
Stitch Transaction Fetcher with GraphQL
=======================================

GraphQL-based transaction fetcher for Stitch Money API.
Stitch uses GraphQL instead of REST, so this implementation provides
GraphQL query construction and response handling for enterprise customers.

Key Features:
- GraphQL query construction for financial data retrieval
- Bulk transaction processing with pagination
- Enterprise account management and filtering
- Real-time transaction streaming capabilities
- Advanced filtering and sorting options
- Comprehensive error handling for GraphQL responses
- Transaction categorization and enrichment

GraphQL Capabilities:
- User authentication and token management
- Bank account linking and management
- Transaction history queries with flexible filtering
- Balance inquiries and account information
- Bulk operations for enterprise customers
- Webhook subscription management
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass
from decimal import Decimal
import json

from .auth import StitchAuthHandler
from .models import (
    StitchTransaction,
    StitchAccount,
    StitchBulkOperationResult,
    StitchTransactionType,
    StitchTransactionStatus,
    StitchBulkOperationStatus
)
from .exceptions import (
    StitchAPIError,
    StitchDataError,
    StitchBulkOperationError,
    create_stitch_error
)

logger = logging.getLogger(__name__)


@dataclass
class GraphQLQuery:
    """GraphQL query structure for Stitch API"""
    query: str
    variables: Dict[str, Any]
    operation_name: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        """Convert to GraphQL request payload"""
        payload = {
            'query': self.query,
            'variables': self.variables
        }
        if self.operation_name:
            payload['operationName'] = self.operation_name
        return payload


@dataclass
class TransactionFilter:
    """Transaction filtering options for GraphQL queries"""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_ids: Optional[List[str]] = None
    transaction_types: Optional[List[StitchTransactionType]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    currencies: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    search_text: Optional[str] = None
    limit: int = 100
    offset: int = 0

    def to_graphql_variables(self) -> Dict[str, Any]:
        """Convert filter to GraphQL variables"""
        variables = {
            'limit': self.limit,
            'offset': self.offset
        }
        
        if self.start_date:
            variables['startDate'] = self.start_date.isoformat()
        if self.end_date:
            variables['endDate'] = self.end_date.isoformat()
        if self.account_ids:
            variables['accountIds'] = self.account_ids
        if self.transaction_types:
            variables['transactionTypes'] = [t.value for t in self.transaction_types]
        if self.min_amount:
            variables['minAmount'] = str(self.min_amount)
        if self.max_amount:
            variables['maxAmount'] = str(self.max_amount)
        if self.currencies:
            variables['currencies'] = self.currencies
        if self.categories:
            variables['categories'] = self.categories
        if self.search_text:
            variables['searchText'] = self.search_text
            
        return variables


class StitchGraphQLClient:
    """GraphQL client for Stitch Money API"""
    
    def __init__(self, auth_handler: StitchAuthHandler):
        self.auth_handler = auth_handler
        self.endpoint = f"{auth_handler.base_url}/graphql"
        
    async def execute_query(
        self, 
        query: GraphQLQuery,
        require_auth: bool = True
    ) -> Dict[str, Any]:
        """
        Execute GraphQL query against Stitch API
        
        Args:
            query: GraphQL query to execute
            require_auth: Whether query requires authentication
            
        Returns:
            GraphQL response data
            
        Raises:
            StitchAPIError: API request failed
            StitchDataError: Invalid GraphQL response
        """
        if require_auth:
            await self.auth_handler.ensure_valid_token()
        
        headers = self.auth_handler.get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        try:
            response = await self.auth_handler._make_auth_request(
                'POST',
                'graphql',
                data=query.to_payload(),
                headers=headers,
                require_auth=require_auth
            )
            
            # Check for GraphQL errors
            if 'errors' in response:
                errors = response['errors']
                error_messages = [error.get('message', 'Unknown GraphQL error') for error in errors]
                
                raise StitchDataError(
                    f"GraphQL errors: {'; '.join(error_messages)}",
                    validation_errors=errors,
                    enterprise_context={
                        'tenant_id': self.auth_handler.tenant_id,
                        'operation_type': 'graphql_query'
                    }
                )
            
            return response.get('data', {})
            
        except StitchAPIError:
            raise
        except Exception as e:
            raise StitchAPIError(
                f"GraphQL query execution failed: {str(e)}",
                enterprise_context={
                    'tenant_id': self.auth_handler.tenant_id,
                    'operation_type': 'graphql_query'
                }
            )


class StitchTransactionFetcher:
    """
    Enterprise-grade transaction fetcher using GraphQL for Stitch Money API.
    
    Provides comprehensive transaction data retrieval with enterprise features
    including bulk operations, advanced filtering, and real-time capabilities.
    """
    
    def __init__(self, auth_handler: StitchAuthHandler):
        """
        Initialize transaction fetcher with authentication handler.
        
        Args:
            auth_handler: Configured Stitch authentication handler
        """
        self.auth_handler = auth_handler
        self.graphql_client = StitchGraphQLClient(auth_handler)
        
        # Enterprise configuration
        self.max_batch_size = 1000
        self.default_page_size = 100
        self.max_concurrent_requests = 10
        
        logger.info("Initialized Stitch GraphQL transaction fetcher")
    
    def _build_user_query(self) -> GraphQLQuery:
        """Build GraphQL query to get authenticated user information"""
        query = """
        query GetUser {
            user {
                id
                clientId
                accounts {
                    id
                    name
                    accountNumber
                    accountType
                    bankId
                    balance {
                        amount
                        currency
                    }
                    holder {
                        name
                        email
                        phoneNumber
                    }
                }
            }
        }
        """
        
        return GraphQLQuery(
            query=query,
            variables={},
            operation_name="GetUser"
        )
    
    def _build_transactions_query(self, filter_options: TransactionFilter) -> GraphQLQuery:
        """Build GraphQL query for transaction retrieval"""
        query = """
        query GetTransactions(
            $accountIds: [ID!]
            $startDate: Date
            $endDate: Date
            $transactionTypes: [TransactionType!]
            $minAmount: String
            $maxAmount: String
            $currencies: [String!]
            $categories: [String!]
            $searchText: String
            $limit: Int!
            $offset: Int!
        ) {
            user {
                accounts(ids: $accountIds) {
                    id
                    name
                    accountNumber
                    transactions(
                        startDate: $startDate
                        endDate: $endDate
                        types: $transactionTypes
                        minAmount: $minAmount
                        maxAmount: $maxAmount
                        currencies: $currencies
                        categories: $categories
                        searchText: $searchText
                        limit: $limit
                        offset: $offset
                    ) {
                        edges {
                            node {
                                id
                                amount {
                                    amount
                                    currency
                                }
                                type
                                status
                                description
                                reference
                                date
                                runningBalance {
                                    amount
                                    currency
                                }
                                counterparty {
                                    name
                                    accountNumber
                                    bank {
                                        id
                                        name
                                    }
                                }
                                metadata
                            }
                        }
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                            startCursor
                            endCursor
                        }
                        totalCount
                    }
                }
            }
        }
        """
        
        return GraphQLQuery(
            query=query,
            variables=filter_options.to_graphql_variables(),
            operation_name="GetTransactions"
        )
    
    def _build_account_linking_query(self, redirect_uri: str, scopes: List[str]) -> GraphQLQuery:
        """Build GraphQL mutation for account linking"""
        mutation = """
        mutation CreateUserInitiateRequest(
            $redirectUri: String!
            $scopes: [Scope!]!
        ) {
            userInitiateRequest(input: {
                redirectUri: $redirectUri
                scopes: $scopes
            }) {
                authorizationRequestUrl
                state
            }
        }
        """
        
        return GraphQLQuery(
            query=mutation,
            variables={
                'redirectUri': redirect_uri,
                'scopes': scopes
            },
            operation_name="CreateUserInitiateRequest"
        )
    
    async def get_user_accounts(self) -> List[StitchAccount]:
        """
        Get all linked accounts for the authenticated user.
        
        Returns:
            List of StitchAccount objects
        """
        query = self._build_user_query()
        
        try:
            response = await self.graphql_client.execute_query(query)
            
            user_data = response.get('user', {})
            accounts_data = user_data.get('accounts', [])
            
            accounts = []
            for account_data in accounts_data:
                # Map GraphQL response to our StitchAccount model
                balance_data = account_data.get('balance', {})
                holder_data = account_data.get('holder', {})
                
                account = StitchAccount(
                    id=account_data['id'],
                    name=account_data.get('name', ''),
                    account_number=account_data.get('accountNumber', ''),
                    bank_code=account_data.get('bankId', ''),
                    bank_name='',  # Would need separate query for bank details
                    account_type=account_data.get('accountType', 'current'),
                    currency=balance_data.get('currency', 'NGN'),
                    balance=Decimal(str(balance_data.get('amount', '0'))),
                    available_balance=Decimal(str(balance_data.get('amount', '0'))),
                    account_holder_name=holder_data.get('name', ''),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                accounts.append(account)
            
            logger.info(f"Retrieved {len(accounts)} accounts from Stitch")
            return accounts
            
        except Exception as e:
            logger.error(f"Error fetching user accounts: {e}")
            raise StitchAPIError(
                f"Failed to fetch user accounts: {str(e)}",
                enterprise_context={
                    'tenant_id': self.auth_handler.tenant_id,
                    'operation_type': 'get_accounts'
                }
            )
    
    async def get_transactions(
        self,
        filter_options: Optional[TransactionFilter] = None
    ) -> List[StitchTransaction]:
        """
        Get transactions with filtering options.
        
        Args:
            filter_options: Transaction filtering criteria
            
        Returns:
            List of StitchTransaction objects
        """
        if filter_options is None:
            filter_options = TransactionFilter()
        
        query = self._build_transactions_query(filter_options)
        
        try:
            response = await self.graphql_client.execute_query(query)
            
            transactions = []
            user_data = response.get('user', {})
            accounts_data = user_data.get('accounts', [])
            
            for account_data in accounts_data:
                account_id = account_data['id']
                transactions_data = account_data.get('transactions', {})
                edges = transactions_data.get('edges', [])
                
                for edge in edges:
                    node = edge['node']
                    transaction = self._parse_transaction_node(node, account_id)
                    transactions.append(transaction)
            
            logger.info(f"Retrieved {len(transactions)} transactions from Stitch")
            return transactions
            
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            raise StitchAPIError(
                f"Failed to fetch transactions: {str(e)}",
                enterprise_context={
                    'tenant_id': self.auth_handler.tenant_id,
                    'operation_type': 'get_transactions'
                }
            )
    
    async def get_transactions_streaming(
        self,
        filter_options: Optional[TransactionFilter] = None,
        batch_size: int = 100
    ) -> AsyncGenerator[List[StitchTransaction], None]:
        """
        Stream transactions in batches for large datasets.
        
        Args:
            filter_options: Transaction filtering criteria
            batch_size: Number of transactions per batch
            
        Yields:
            Batches of StitchTransaction objects
        """
        if filter_options is None:
            filter_options = TransactionFilter()
        
        filter_options.limit = min(batch_size, self.max_batch_size)
        filter_options.offset = 0
        
        while True:
            try:
                batch_transactions = await self.get_transactions(filter_options)
                
                if not batch_transactions:
                    break
                
                yield batch_transactions
                
                # Check if we got fewer transactions than requested (end of data)
                if len(batch_transactions) < filter_options.limit:
                    break
                
                # Update offset for next batch
                filter_options.offset += filter_options.limit
                
            except Exception as e:
                logger.error(f"Error in transaction streaming: {e}")
                raise
    
    async def bulk_fetch_transactions(
        self,
        account_ids: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        batch_size: int = 100
    ) -> StitchBulkOperationResult:
        """
        Perform bulk transaction fetching for multiple accounts.
        
        Args:
            account_ids: List of account IDs to fetch transactions for
            start_date: Start date for transaction range
            end_date: End date for transaction range
            batch_size: Batch size for processing
            
        Returns:
            StitchBulkOperationResult with operation details
        """
        operation_id = f"bulk_fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.now()
        
        try:
            all_transactions = []
            failed_accounts = []
            
            # Process accounts in parallel batches
            account_batches = [
                account_ids[i:i + self.max_concurrent_requests]
                for i in range(0, len(account_ids), self.max_concurrent_requests)
            ]
            
            for batch in account_batches:
                batch_tasks = []
                
                for account_id in batch:
                    filter_options = TransactionFilter(
                        account_ids=[account_id],
                        start_date=start_date,
                        end_date=end_date,
                        limit=batch_size
                    )
                    
                    task = self.get_transactions(filter_options)
                    batch_tasks.append((account_id, task))
                
                # Execute batch tasks concurrently
                for account_id, task in batch_tasks:
                    try:
                        transactions = await task
                        all_transactions.extend(transactions)
                    except Exception as e:
                        failed_accounts.append({
                            'account_id': account_id,
                            'error': str(e),
                            'error_type': type(e).__name__
                        })
            
            completed_at = datetime.now()
            processing_duration = (completed_at - started_at).total_seconds()
            
            result = StitchBulkOperationResult(
                operation_id=operation_id,
                operation_type='bulk_fetch_transactions',
                status=StitchBulkOperationStatus.COMPLETED if not failed_accounts else StitchBulkOperationStatus.PARTIALLY_COMPLETED,
                total_items=len(account_ids),
                processed_items=len(account_ids) - len(failed_accounts),
                failed_items=len(failed_accounts),
                successful_transactions=[tx.id for tx in all_transactions],
                failed_transactions=failed_accounts,
                started_at=started_at,
                completed_at=completed_at,
                processing_duration=processing_duration,
                metadata={
                    'total_transactions_fetched': len(all_transactions),
                    'batch_size': batch_size,
                    'concurrent_requests': self.max_concurrent_requests
                }
            )
            
            logger.info(f"Bulk fetch completed: {result.processed_items}/{result.total_items} accounts processed")
            return result
            
        except Exception as e:
            logger.error(f"Bulk fetch operation failed: {e}")
            raise StitchBulkOperationError(
                f"Bulk transaction fetch failed: {str(e)}",
                operation_id=operation_id,
                operation_type='bulk_fetch_transactions',
                enterprise_context={
                    'tenant_id': self.auth_handler.tenant_id,
                    'operation_type': 'bulk_operation'
                }
            )
    
    async def initiate_account_linking(
        self,
        redirect_uri: str,
        scopes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Initiate account linking process for enterprise customers.
        
        Args:
            redirect_uri: URI to redirect after account linking
            scopes: List of permission scopes to request
            
        Returns:
            Account linking response with authorization URL
        """
        if scopes is None:
            scopes = ['accounts', 'transactions', 'balances']
        
        query = self._build_account_linking_query(redirect_uri, scopes)
        
        try:
            response = await self.graphql_client.execute_query(query, require_auth=False)
            
            request_data = response.get('userInitiateRequest', {})
            
            return {
                'authorization_url': request_data.get('authorizationRequestUrl'),
                'state': request_data.get('state'),
                'redirect_uri': redirect_uri,
                'scopes': scopes
            }
            
        except Exception as e:
            logger.error(f"Error initiating account linking: {e}")
            raise StitchAPIError(
                f"Failed to initiate account linking: {str(e)}",
                enterprise_context={
                    'tenant_id': self.auth_handler.tenant_id,
                    'operation_type': 'account_linking'
                }
            )
    
    def _parse_transaction_node(self, node: Dict[str, Any], account_id: str) -> StitchTransaction:
        """Parse GraphQL transaction node into StitchTransaction object"""
        amount_data = node.get('amount', {})
        counterparty_data = node.get('counterparty', {})
        balance_data = node.get('runningBalance', {})
        
        # Parse transaction date
        transaction_date = datetime.fromisoformat(node.get('date', datetime.now().isoformat()))
        
        transaction = StitchTransaction(
            id=node['id'],
            account_id=account_id,
            amount=Decimal(str(amount_data.get('amount', '0'))),
            currency=amount_data.get('currency', 'NGN'),
            transaction_type=StitchTransactionType(node.get('type', 'debit')),
            status=StitchTransactionStatus(node.get('status', 'processed')),
            date=transaction_date,
            description=node.get('description', ''),
            reference=node.get('reference', ''),
            counterparty_name=counterparty_data.get('name'),
            counterparty_account=counterparty_data.get('accountNumber'),
            counterparty_bank=counterparty_data.get('bank', {}).get('name'),
            counterparty_bank_code=counterparty_data.get('bank', {}).get('id'),
            balance_after=Decimal(str(balance_data.get('amount', '0'))),
            metadata=node.get('metadata', {})
        )
        
        return transaction
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[StitchTransaction]:
        """
        Get a specific transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            StitchTransaction object or None if not found
        """
        # Note: This would require a specific GraphQL query for single transaction
        # For now, we'll implement a basic version
        filter_options = TransactionFilter(limit=1000)  # Search in recent transactions
        transactions = await self.get_transactions(filter_options)
        
        for transaction in transactions:
            if transaction.id == transaction_id:
                return transaction
        
        return None
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get information about the GraphQL client configuration"""
        return {
            'endpoint': self.graphql_client.endpoint,
            'authentication': self.auth_handler.is_authenticated(),
            'max_batch_size': self.max_batch_size,
            'default_page_size': self.default_page_size,
            'max_concurrent_requests': self.max_concurrent_requests,
            'tenant_id': self.auth_handler.tenant_id,
            'organization_id': self.auth_handler.organization_id
        }
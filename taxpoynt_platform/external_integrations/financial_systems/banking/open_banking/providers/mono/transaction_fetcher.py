"""
Mono Transaction Fetcher
========================

Handles transaction data retrieval from Mono Open Banking API.
Provides comprehensive transaction history, filtering, and analysis
capabilities for Nigerian bank accounts.

Key Features:
- Paginated transaction retrieval
- Date range filtering
- Transaction categorization
- Duplicate detection
- Nigerian banking compliance
- Automated invoice generation triggers

API Endpoints:
- GET /v2/accounts/{account_id}/transactions - Get transaction history
- GET /v2/accounts/{account_id}/transactions/{transaction_id} - Get specific transaction
- GET /v2/accounts/{account_id}/income - Get income analysis
- GET /v2/accounts/{account_id}/balance - Get current balance

Architecture consistent with existing TaxPoynt data extraction patterns.
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from .models import (
    MonoTransaction,
    MonoTransactionsResponse,
    MonoTransactionQuery,
    MonoAccount,
    MonoIncome,
    MonoTransactionType
)
from .exceptions import (
    MonoConnectionError,
    MonoValidationError,
    MonoAccountError,
    MonoInsufficientDataError,
    MonoRateLimitError,
    map_mono_error
)


logger = logging.getLogger(__name__)


@dataclass
class TransactionBatch:
    """Container for a batch of transactions with metadata"""
    transactions: List[MonoTransaction]
    total_count: int
    page: int
    has_more: bool
    date_range: Tuple[date, date]
    account_id: str


@dataclass
class TransactionSummary:
    """Summary statistics for a set of transactions"""
    total_transactions: int
    total_credits: Decimal
    total_debits: Decimal
    net_flow: Decimal
    credit_count: int
    debit_count: int
    date_range: Tuple[date, date]
    categories: Dict[str, int]
    avg_transaction_amount: Decimal


class MonoTransactionFetcher:
    """
    Fetches and processes transaction data from Mono API.
    
    Handles pagination, filtering, and data processing for Nigerian
    banking transactions with FIRS compliance considerations.
    """
    
    def __init__(
        self,
        secret_key: str,
        base_url: str = "https://api.withmono.com",
        max_concurrent_requests: int = 3
    ):
        """
        Initialize transaction fetcher.
        
        Args:
            secret_key: Mono API secret key
            base_url: Mono API base URL
            max_concurrent_requests: Max concurrent API requests
        """
        self.secret_key = secret_key
        self.base_url = base_url
        self.max_concurrent_requests = max_concurrent_requests
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            headers={
                "mono-sec-key": self.secret_key,
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-Platform/1.0 (Mono-Transaction-Fetcher)"
            },
            timeout=60.0,  # Longer timeout for transaction requests
            limits=httpx.Limits(max_connections=max_concurrent_requests)
        )
        
        # Rate limiting tracking
        self.request_timestamps: List[datetime] = []
        self.rate_limit = 60  # Per minute
        
        # Transaction caching for duplicate detection
        self._transaction_cache: Dict[str, MonoTransaction] = {}
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()
    
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).total_seconds() < 60
        ]
        
        if len(self.request_timestamps) >= self.rate_limit:
            raise MonoRateLimitError("Transaction fetcher rate limit exceeded")
        
        self.request_timestamps.append(now)
    
    async def get_account_transactions(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[MonoTransactionType] = None,
        narration_filter: Optional[str] = None,
        limit: int = 50,
        page: int = 1
    ) -> TransactionBatch:
        """
        Get transactions for a specific account.
        
        Args:
            account_id: Mono account identifier
            start_date: Start date for transaction filtering
            end_date: End date for transaction filtering  
            transaction_type: Filter by credit/debit
            narration_filter: Filter by transaction description
            limit: Number of transactions per page (max 100)
            page: Page number for pagination
            
        Returns:
            TransactionBatch with transactions and metadata
            
        Raises:
            MonoAccountError: Account-related errors
            MonoValidationError: Invalid parameters
            MonoConnectionError: API connection issues
        """
        try:
            self._check_rate_limit()
            
            # Validate parameters
            if limit > 100:
                raise MonoValidationError("Limit cannot exceed 100 transactions per request")
            
            # Set default date range (FIRS compliance: 7 years max)
            if not start_date:
                start_date = date.today() - timedelta(days=365)  # 1 year default
            if not end_date:
                end_date = date.today()
            
            # Validate date range
            if start_date > end_date:
                raise MonoValidationError("Start date cannot be after end date")
            
            max_days_back = 2555  # 7 years for FIRS compliance
            if (date.today() - start_date).days > max_days_back:
                logger.warning(f"Start date exceeds {max_days_back} days, adjusting for compliance")
                start_date = date.today() - timedelta(days=max_days_back)
            
            # Build query parameters
            params = {
                "paginate": "true",
                "limit": str(limit),
                "page": str(page)
            }
            
            if start_date:
                params["start"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["end"] = end_date.strftime("%Y-%m-%d")
            if transaction_type:
                params["type"] = transaction_type.value
            if narration_filter:
                params["narration"] = narration_filter
            
            logger.info(f"Fetching transactions for account {account_id}, page {page}")
            
            # Make API request
            response = await self.client.get(
                f"{self.base_url}/v2/accounts/{account_id}/transactions",
                params=params
            )
            
            if response.status_code == 200:
                response_data = response.json()
                transactions_response = MonoTransactionsResponse(**response_data)
                
                # Cache transactions for duplicate detection
                for transaction in transactions_response.data:
                    self._transaction_cache[transaction.id] = transaction
                
                # Calculate metadata
                paging = transactions_response.paging
                total_count = paging.get("total", len(transactions_response.data))
                has_more = paging.get("next") is not None
                
                batch = TransactionBatch(
                    transactions=transactions_response.data,
                    total_count=total_count,
                    page=page,
                    has_more=has_more,
                    date_range=(start_date, end_date),
                    account_id=account_id
                )
                
                logger.info(f"Retrieved {len(transactions_response.data)} transactions for account {account_id}")
                return batch
                
            elif response.status_code == 404:
                raise MonoAccountError(f"Account not found: {account_id}", account_id=account_id)
            elif response.status_code == 403:
                error_data = response.json() if response.content else {}
                if "reauthorization" in error_data.get("message", "").lower():
                    from .exceptions import MonoReauthorizationRequiredError
                    raise MonoReauthorizationRequiredError(account_id)
                else:
                    raise MonoAccountError(f"Access denied for account: {account_id}", account_id=account_id)
            else:
                error_data = response.json() if response.content else {}
                raise map_mono_error(response.status_code, error_data, "Transaction fetch failed")
                
        except ValidationError as e:
            raise MonoValidationError(f"Response validation failed: {str(e)}")
        except httpx.RequestError as e:
            raise MonoConnectionError(f"Network request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching transactions: {str(e)}", exc_info=True)
            raise MonoConnectionError(f"Unexpected error: {str(e)}")
    
    async def get_all_account_transactions(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[MonoTransactionType] = None,
        max_transactions: Optional[int] = None
    ) -> AsyncGenerator[MonoTransaction, None]:
        """
        Get all transactions for an account using pagination.
        
        Args:
            account_id: Mono account identifier
            start_date: Start date for filtering
            end_date: End date for filtering
            transaction_type: Filter by transaction type
            max_transactions: Maximum number of transactions to retrieve
            
        Yields:
            MonoTransaction: Individual transaction records
        """
        page = 1
        retrieved_count = 0
        
        while True:
            # Check if we've reached the max limit
            if max_transactions and retrieved_count >= max_transactions:
                break
            
            # Calculate remaining transactions needed
            remaining = max_transactions - retrieved_count if max_transactions else None
            limit = min(100, remaining) if remaining else 100
            
            try:
                batch = await self.get_account_transactions(
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date,
                    transaction_type=transaction_type,
                    limit=limit,
                    page=page
                )
                
                # Yield transactions
                for transaction in batch.transactions:
                    if max_transactions and retrieved_count >= max_transactions:
                        return
                    yield transaction
                    retrieved_count += 1
                
                # Check if we have more pages
                if not batch.has_more or len(batch.transactions) == 0:
                    break
                
                page += 1
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except MonoInsufficientDataError:
                logger.info(f"No more transaction data available for account {account_id}")
                break
            except Exception as e:
                logger.error(f"Error in paginated transaction fetch: {str(e)}")
                raise
    
    async def get_transaction_summary(
        self,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> TransactionSummary:
        """
        Get transaction summary and statistics for an account.
        
        Args:
            account_id: Mono account identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            TransactionSummary with aggregated statistics
        """
        transactions: List[MonoTransaction] = []
        
        # Collect all transactions in the date range
        async for transaction in self.get_all_account_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        ):
            transactions.append(transaction)
        
        if not transactions:
            # Return empty summary
            return TransactionSummary(
                total_transactions=0,
                total_credits=Decimal("0"),
                total_debits=Decimal("0"),
                net_flow=Decimal("0"),
                credit_count=0,
                debit_count=0,
                date_range=(start_date or date.today(), end_date or date.today()),
                categories={},
                avg_transaction_amount=Decimal("0")
            )
        
        # Calculate statistics
        total_credits = Decimal("0")
        total_debits = Decimal("0")
        credit_count = 0
        debit_count = 0
        categories: Dict[str, int] = {}
        
        for transaction in transactions:
            amount = transaction.amount_naira
            
            if transaction.type == MonoTransactionType.CREDIT:
                total_credits += amount
                credit_count += 1
            else:
                total_debits += abs(amount)  # Debits might be negative
                debit_count += 1
            
            # Count categories
            category = transaction.category
            categories[category] = categories.get(category, 0) + 1
        
        net_flow = total_credits - total_debits
        total_amount = total_credits + total_debits
        avg_amount = total_amount / len(transactions) if transactions else Decimal("0")
        
        actual_start = min(t.date for t in transactions) if transactions else start_date
        actual_end = max(t.date for t in transactions) if transactions else end_date
        
        return TransactionSummary(
            total_transactions=len(transactions),
            total_credits=total_credits,
            total_debits=total_debits,
            net_flow=net_flow,
            credit_count=credit_count,
            debit_count=debit_count,
            date_range=(actual_start, actual_end),
            categories=categories,
            avg_transaction_amount=avg_amount
        )
    
    async def get_recent_transactions(
        self,
        account_id: str,
        days: int = 30,
        limit: int = 50
    ) -> List[MonoTransaction]:
        """
        Get recent transactions for quick analysis.
        
        Args:
            account_id: Mono account identifier
            days: Number of recent days to fetch
            limit: Maximum number of transactions
            
        Returns:
            List of recent MonoTransaction objects
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        batch = await self.get_account_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return batch.transactions
    
    async def get_income_analysis(self, account_id: str) -> Optional[MonoIncome]:
        """
        Get income analysis for an account (if supported by Mono).
        
        Args:
            account_id: Mono account identifier
            
        Returns:
            MonoIncome with income analysis or None if not available
        """
        try:
            self._check_rate_limit()
            
            response = await self.client.get(
                f"{self.base_url}/v2/accounts/{account_id}/income"
            )
            
            if response.status_code == 200:
                income_data = response.json()
                return MonoIncome(**income_data)
            elif response.status_code == 404:
                logger.info(f"Income analysis not available for account {account_id}")
                return None
            else:
                error_data = response.json() if response.content else {}
                logger.warning(f"Income analysis failed: {error_data.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching income analysis: {str(e)}")
            return None
    
    def detect_potential_invoicing_transactions(
        self,
        transactions: List[MonoTransaction],
        min_amount: Decimal = Decimal("1000"),  # Minimum NGN 1,000
        keywords: Optional[List[str]] = None
    ) -> List[MonoTransaction]:
        """
        Detect transactions that might require invoice generation.
        
        Args:
            transactions: List of transactions to analyze
            min_amount: Minimum transaction amount to consider
            keywords: Keywords in narration that suggest business transactions
            
        Returns:
            List of transactions that might need invoicing
        """
        if not keywords:
            keywords = [
                "payment", "invoice", "service", "consultation", "project",
                "contract", "deposit", "installment", "fee", "charge"
            ]
        
        potential_invoicing = []
        
        for transaction in transactions:
            # Only consider credit transactions (money received)
            if transaction.type != MonoTransactionType.CREDIT:
                continue
            
            # Check minimum amount
            if transaction.amount_naira < min_amount:
                continue
            
            # Check for business-related keywords in narration
            narration_lower = transaction.narration.lower()
            if any(keyword in narration_lower for keyword in keywords):
                potential_invoicing.append(transaction)
                continue
            
            # Check for round amounts (often indicate business transactions)
            amount = transaction.amount_naira
            if amount % 1000 == 0 or amount % 500 == 0:  # Round thousands or 500s
                potential_invoicing.append(transaction)
        
        return potential_invoicing
    
    async def get_balance(self, account_id: str) -> Optional[Decimal]:
        """
        Get current account balance.
        
        Args:
            account_id: Mono account identifier
            
        Returns:
            Account balance in Naira or None if not available
        """
        try:
            self._check_rate_limit()
            
            response = await self.client.get(
                f"{self.base_url}/v2/accounts/{account_id}/balance"
            )
            
            if response.status_code == 200:
                balance_data = response.json()
                balance_kobo = balance_data.get("balance", 0)
                return Decimal(balance_kobo) / 100  # Convert kobo to Naira
            else:
                logger.warning(f"Failed to get balance for account {account_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching account balance: {str(e)}")
            return None


# Export transaction fetcher
__all__ = [
    "MonoTransactionFetcher",
    "TransactionBatch", 
    "TransactionSummary"
]
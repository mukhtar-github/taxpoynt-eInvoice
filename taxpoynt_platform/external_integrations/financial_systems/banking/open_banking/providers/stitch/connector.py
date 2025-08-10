"""
Stitch Banking Connector
========================
Main connector orchestrating all Stitch Money operations.
Provides comprehensive banking integration with enterprise features including
transaction fetching, account management, and real-time webhook processing.

Key Features:
- Complete transaction and account management
- GraphQL-based API integration
- Enterprise webhook processing
- Comprehensive error handling and retry logic
- Banking compliance and audit logging
- Multi-account aggregation support
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal

from .auth import StitchAuthHandler
from .transaction_fetcher import StitchTransactionFetcher
from .webhook_handler import StitchWebhookHandler
from .exceptions import (
    StitchAPIError, StitchAuthenticationError, StitchConnectionError,
    StitchRateLimitError, StitchDataError, StitchComplianceError
)
from .models import (
    StitchAccount, StitchTransaction, StitchBalance, StitchAccountHolder,
    StitchWebhookEvent, StitchConnectionConfig, StitchBulkTransactionResponse,
    StitchAccountHierarchy, StitchComplianceReport
)

from ....base import BaseBankingConnector
from .......shared.logging import get_logger
from .......shared.exceptions import IntegrationError
from .......shared.config import BaseConfig


class StitchBankingConnector(BaseBankingConnector):
    """
    Main Stitch Money banking connector providing comprehensive banking integration.
    
    This connector orchestrates all Stitch operations including:
    - Account management and hierarchy
    - Transaction fetching and processing
    - Real-time webhook handling
    - Compliance reporting and audit
    """
    
    def __init__(self, config: StitchConnectionConfig):
        """
        Initialize Stitch banking connector.
        
        Args:
            config: Stitch connection configuration
        """
        super().__init__(config)
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize core components
        self.auth_handler = StitchAuthHandler(config)
        self.transaction_fetcher = StitchTransactionFetcher(config, self.auth_handler)
        self.webhook_handler = StitchWebhookHandler(config)
        
        # Connection state
        self._is_connected = False
        self._last_health_check = None
        self._connection_metrics = {
            'requests_made': 0,
            'requests_failed': 0,
            'last_request_time': None,
            'rate_limit_remaining': None
        }
        
        self.logger.info(
            f"Initialized Stitch connector for client: {config.client_id}"
        )
    
    async def connect(self) -> bool:
        """
        Establish connection to Stitch Money API.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            StitchConnectionError: If connection fails
        """
        try:
            self.logger.info("Connecting to Stitch Money API...")
            
            # Authenticate with Stitch
            await self.auth_handler.authenticate()
            
            # Verify connection with health check
            health_status = await self._perform_health_check()
            
            if health_status['healthy']:
                self._is_connected = True
                self._last_health_check = datetime.utcnow()
                
                self.logger.info(
                    f"Successfully connected to Stitch Money API. "
                    f"Health: {health_status}"
                )
                return True
            else:
                raise StitchConnectionError(
                    f"Health check failed: {health_status.get('error', 'Unknown error')}"
                )
                
        except StitchAuthenticationError:
            self.logger.error("Authentication failed during connection")
            raise
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            raise StitchConnectionError(f"Failed to connect to Stitch API: {str(e)}")
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Stitch Money API.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            self.logger.info("Disconnecting from Stitch Money API...")
            
            # Revoke tokens if possible
            await self.auth_handler.revoke_tokens()
            
            self._is_connected = False
            self._last_health_check = None
            
            self.logger.info("Successfully disconnected from Stitch Money API")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during disconnection: {str(e)}")
            return False
    
    async def get_accounts(
        self,
        account_holder_id: Optional[str] = None,
        include_hierarchy: bool = True
    ) -> List[StitchAccount]:
        """
        Retrieve banking accounts from Stitch.
        
        Args:
            account_holder_id: Optional filter by account holder
            include_hierarchy: Whether to include account hierarchy
            
        Returns:
            List of Stitch accounts
            
        Raises:
            StitchAPIError: If API request fails
        """
        await self._ensure_connected()
        
        try:
            self.logger.info(
                f"Fetching accounts for holder: {account_holder_id or 'all'}"
            )
            
            accounts = await self.transaction_fetcher.get_accounts(
                account_holder_id=account_holder_id,
                include_hierarchy=include_hierarchy
            )
            
            self._update_connection_metrics(success=True)
            
            self.logger.info(f"Retrieved {len(accounts)} accounts")
            return accounts
            
        except Exception as e:
            self._update_connection_metrics(success=False)
            self.logger.error(f"Failed to fetch accounts: {str(e)}")
            raise StitchAPIError(f"Account retrieval failed: {str(e)}")
    
    async def get_account_balances(
        self,
        account_ids: List[str]
    ) -> Dict[str, StitchBalance]:
        """
        Get current balances for specified accounts.
        
        Args:
            account_ids: List of account IDs
            
        Returns:
            Dictionary mapping account ID to balance
            
        Raises:
            StitchAPIError: If API request fails
        """
        await self._ensure_connected()
        
        try:
            self.logger.info(f"Fetching balances for {len(account_ids)} accounts")
            
            balances = await self.transaction_fetcher.get_account_balances(account_ids)
            
            self._update_connection_metrics(success=True)
            
            self.logger.info(f"Retrieved balances for {len(balances)} accounts")
            return balances
            
        except Exception as e:
            self._update_connection_metrics(success=False)
            self.logger.error(f"Failed to fetch balances: {str(e)}")
            raise StitchAPIError(f"Balance retrieval failed: {str(e)}")
    
    async def get_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> StitchBulkTransactionResponse:
        """
        Retrieve transactions for a specific account.
        
        Args:
            account_id: Account identifier
            start_date: Start date for transaction search
            end_date: End date for transaction search
            limit: Maximum number of transactions
            offset: Pagination offset
            
        Returns:
            Bulk transaction response
            
        Raises:
            StitchAPIError: If API request fails
        """
        await self._ensure_connected()
        
        try:
            self.logger.info(
                f"Fetching transactions for account {account_id} "
                f"from {start_date} to {end_date}"
            )
            
            response = await self.transaction_fetcher.get_transactions(
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset
            )
            
            self._update_connection_metrics(success=True)
            
            self.logger.info(
                f"Retrieved {len(response.transactions)} transactions "
                f"for account {account_id}"
            )
            return response
            
        except Exception as e:
            self._update_connection_metrics(success=False)
            self.logger.error(f"Failed to fetch transactions: {str(e)}")
            raise StitchAPIError(f"Transaction retrieval failed: {str(e)}")
    
    async def get_bulk_transactions(
        self,
        account_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        batch_size: int = 100
    ) -> Dict[str, StitchBulkTransactionResponse]:
        """
        Retrieve transactions for multiple accounts in bulk.
        
        Args:
            account_ids: List of account identifiers
            start_date: Start date for transaction search
            end_date: End date for transaction search
            batch_size: Size of each batch request
            
        Returns:
            Dictionary mapping account ID to transaction response
            
        Raises:
            StitchAPIError: If API request fails
        """
        await self._ensure_connected()
        
        try:
            self.logger.info(
                f"Fetching bulk transactions for {len(account_ids)} accounts "
                f"from {start_date} to {end_date}"
            )
            
            responses = await self.transaction_fetcher.get_bulk_transactions(
                account_ids=account_ids,
                start_date=start_date,
                end_date=end_date,
                batch_size=batch_size
            )
            
            self._update_connection_metrics(success=True)
            
            total_transactions = sum(
                len(response.transactions) for response in responses.values()
            )
            
            self.logger.info(
                f"Retrieved {total_transactions} total transactions "
                f"across {len(responses)} accounts"
            )
            return responses
            
        except Exception as e:
            self._update_connection_metrics(success=False)
            self.logger.error(f"Failed to fetch bulk transactions: {str(e)}")
            raise StitchAPIError(f"Bulk transaction retrieval failed: {str(e)}")
    
    async def process_webhook(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: Optional[str] = None
    ) -> StitchWebhookEvent:
        """
        Process incoming webhook from Stitch.
        
        Args:
            payload: Webhook payload data
            signature: Webhook signature for verification
            timestamp: Optional timestamp header
            
        Returns:
            Processed webhook event
            
        Raises:
            StitchAPIError: If webhook processing fails
        """
        try:
            self.logger.info(f"Processing Stitch webhook: {payload.get('type', 'unknown')}")
            
            event = await self.webhook_handler.process_webhook(
                payload=payload,
                signature=signature,
                timestamp=timestamp
            )
            
            self.logger.info(
                f"Successfully processed webhook event: {event.event_id} "
                f"of type: {event.event_type}"
            )
            return event
            
        except Exception as e:
            self.logger.error(f"Failed to process webhook: {str(e)}")
            raise StitchAPIError(f"Webhook processing failed: {str(e)}")
    
    async def get_account_hierarchy(
        self,
        root_account_id: str
    ) -> StitchAccountHierarchy:
        """
        Get complete account hierarchy for enterprise customers.
        
        Args:
            root_account_id: Root account identifier
            
        Returns:
            Account hierarchy structure
            
        Raises:
            StitchAPIError: If API request fails
        """
        await self._ensure_connected()
        
        try:
            self.logger.info(f"Fetching account hierarchy for root: {root_account_id}")
            
            hierarchy = await self.transaction_fetcher.get_account_hierarchy(
                root_account_id
            )
            
            self._update_connection_metrics(success=True)
            
            self.logger.info(
                f"Retrieved hierarchy with {len(hierarchy.child_accounts)} "
                f"child accounts"
            )
            return hierarchy
            
        except Exception as e:
            self._update_connection_metrics(success=False)
            self.logger.error(f"Failed to fetch account hierarchy: {str(e)}")
            raise StitchAPIError(f"Account hierarchy retrieval failed: {str(e)}")
    
    async def generate_compliance_report(
        self,
        account_ids: List[str],
        start_date: datetime,
        end_date: datetime,
        report_type: str = "transaction_summary"
    ) -> StitchComplianceReport:
        """
        Generate compliance report for specified accounts.
        
        Args:
            account_ids: List of account identifiers
            start_date: Report start date
            end_date: Report end date
            report_type: Type of compliance report
            
        Returns:
            Compliance report
            
        Raises:
            StitchComplianceError: If report generation fails
        """
        await self._ensure_connected()
        
        try:
            self.logger.info(
                f"Generating {report_type} compliance report for "
                f"{len(account_ids)} accounts"
            )
            
            report = await self.transaction_fetcher.generate_compliance_report(
                account_ids=account_ids,
                start_date=start_date,
                end_date=end_date,
                report_type=report_type
            )
            
            self._update_connection_metrics(success=True)
            
            self.logger.info(
                f"Generated compliance report: {report.report_id} "
                f"with {len(report.account_summaries)} account summaries"
            )
            return report
            
        except Exception as e:
            self._update_connection_metrics(success=False)
            self.logger.error(f"Failed to generate compliance report: {str(e)}")
            raise StitchComplianceError(f"Compliance report generation failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check.
        
        Returns:
            Health status information
        """
        try:
            health_status = await self._perform_health_check()
            
            # Include connection metrics
            health_status.update({
                'connection_metrics': self._connection_metrics.copy(),
                'last_health_check': self._last_health_check.isoformat() if self._last_health_check else None,
                'is_connected': self._is_connected
            })
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform basic health check against Stitch API.
        
        Returns:
            Health check results
        """
        try:
            # Test authentication
            auth_valid = await self.auth_handler.validate_token()
            
            if not auth_valid:
                return {
                    'healthy': False,
                    'error': 'Authentication token invalid',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Test basic API access
            await self.transaction_fetcher.test_api_access()
            
            return {
                'healthy': True,
                'timestamp': datetime.utcnow().isoformat(),
                'auth_status': 'valid',
                'api_access': 'ok'
            }
            
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _ensure_connected(self) -> None:
        """
        Ensure connection is established and healthy.
        
        Raises:
            StitchConnectionError: If not connected or unhealthy
        """
        if not self._is_connected:
            raise StitchConnectionError("Not connected to Stitch API")
        
        # Check if health check is stale
        if (self._last_health_check and 
            datetime.utcnow() - self._last_health_check > timedelta(minutes=30)):
            
            self.logger.info("Performing health check due to stale connection")
            health_status = await self._perform_health_check()
            
            if not health_status['healthy']:
                self._is_connected = False
                raise StitchConnectionError(
                    f"Connection unhealthy: {health_status.get('error', 'Unknown error')}"
                )
            
            self._last_health_check = datetime.utcnow()
    
    def _update_connection_metrics(self, success: bool) -> None:
        """
        Update connection performance metrics.
        
        Args:
            success: Whether the request was successful
        """
        self._connection_metrics['requests_made'] += 1
        self._connection_metrics['last_request_time'] = datetime.utcnow()
        
        if not success:
            self._connection_metrics['requests_failed'] += 1
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
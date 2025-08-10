"""
Banking System Integration Endpoints - API v1
==============================================
System Integrator endpoints for banking system integrations.
Covers: Open Banking (Mono, Stitch), Unified Banking, Transaction data collection
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse

from ......core_platform.authentication.role_manager import PlatformRole
from ......core_platform.messaging.message_router import ServiceRole, MessageRouter
from .....role_routing.models import HTTPRoutingContext
from .....role_routing.role_detector import HTTPRoleDetector
from .....role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class BankingEndpointsV1:
    """
    Banking System Integration Endpoints - Version 1
    ================================================
    Manages banking system integrations for System Integrators:
    
    **Available Banking Systems:**
    - **Open Banking Providers (3)**: Mono, Stitch, Unified Banking
    - **Transaction Data Collection**: Account transactions, balances, customer data
    - **Account Management**: Account linking, balance monitoring, transaction sync
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/banking", tags=["Banking Integrations V1"])
        
        # Define available banking systems
        self.banking_systems = {
            "open_banking": {
                "providers": ["mono", "stitch", "unified_banking"],
                "description": "Open Banking and transaction data providers",
                "features": ["transaction_data", "account_data", "balance_data", "customer_data"]
            }
        }
        
        self._setup_routes()
        logger.info("Banking Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup banking system integration routes"""
        
        # Banking System Overview
        self.router.add_api_route(
            "/available-systems",
            self.get_available_banking_systems,
            methods=["GET"],
            summary="Get available banking systems",
            description="List all banking systems available for integration",
            response_model=V1ResponseModel
        )
        
        # Open Banking Routes
        self.router.add_api_route(
            "/open-banking",
            self.list_open_banking_connections,
            methods=["GET"],
            summary="List Open Banking connections",
            description="Get all Open Banking connections (Mono, Stitch, etc.)",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/open-banking",
            self.create_open_banking_connection,
            methods=["POST"],
            summary="Create Open Banking connection",
            description="Create new Open Banking connection",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/open-banking/{connection_id}",
            self.get_open_banking_connection,
            methods=["GET"],
            summary="Get Open Banking connection",
            description="Get specific Open Banking connection details",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/open-banking/{connection_id}",
            self.update_open_banking_connection,
            methods=["PUT"],
            summary="Update Open Banking connection",
            description="Update Open Banking connection configuration",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/open-banking/{connection_id}",
            self.delete_open_banking_connection,
            methods=["DELETE"],
            summary="Delete Open Banking connection",
            description="Remove Open Banking connection",
            response_model=V1ResponseModel
        )
        
        # Banking Transaction Routes
        self.router.add_api_route(
            "/transactions",
            self.get_banking_transactions,
            methods=["GET"],
            summary="Get banking transactions",
            description="Retrieve transactions from banking systems",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/transactions/sync",
            self.sync_banking_transactions,
            methods=["POST"],
            summary="Sync banking transactions",
            description="Synchronize transactions from banking systems",
            response_model=V1ResponseModel
        )
        
        # Banking Account Management
        self.router.add_api_route(
            "/accounts",
            self.get_banking_accounts,
            methods=["GET"],
            summary="Get banking accounts",
            description="Retrieve connected banking accounts",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/accounts/{account_id}/balance",
            self.get_account_balance,
            methods=["GET"],
            summary="Get account balance",
            description="Get current balance for a banking account",
            response_model=V1ResponseModel
        )
        
        # Connection Health and Testing
        self.router.add_api_route(
            "/connections/{connection_id}/test",
            self.test_banking_connection,
            methods=["POST"],
            summary="Test banking system connection",
            description="Test connectivity and authentication for a banking system connection",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/health",
            self.get_banking_connection_health,
            methods=["GET"],
            summary="Get banking connection health",
            description="Get detailed health status of a banking system connection",
            response_model=V1ResponseModel
        )
    
    # Banking System Overview Endpoints
    async def get_available_banking_systems(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get all available banking systems"""
        try:            
            result = {
                "banking_systems": self.banking_systems,
                "totals": {
                    "open_banking_providers": len(self.banking_systems["open_banking"]["providers"]),
                    "total_banking_systems": len(self.banking_systems["open_banking"]["providers"])
                },
                "categories": ["open_banking"]
            }
            
            return self._create_v1_response(result, "available_banking_systems_retrieved")
        except Exception as e:
            logger.error(f"Error getting available banking systems in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get available banking systems")
    
    # Open Banking Endpoints
    async def list_open_banking_connections(self, 
                                          request: Request,
                                          context: HTTPRoutingContext = Depends(lambda: None)):
        """List Open Banking connections"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_open_banking_connections",
                payload={
                    "si_id": context.user_id,
                    "filters": dict(request.query_params),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "open_banking_connections_listed")
        except Exception as e:
            logger.error(f"Error listing open banking connections in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list open banking connections")
    
    async def create_open_banking_connection(self, 
                                           request: Request,
                                           context: HTTPRoutingContext = Depends(lambda: None)):
        """Create Open Banking connection"""
        try:
            body = await request.json()
            
            # Validate required fields
            required_fields = ["provider", "organization_id", "connection_config"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Validate provider
            if body["provider"] not in self.banking_systems["open_banking"]["providers"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid banking provider. Available: {', '.join(self.banking_systems['open_banking']['providers'])}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_open_banking_connection",
                payload={
                    "connection_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "open_banking_connection_created", status_code=201)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating open banking connection in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create open banking connection")
    
    async def get_open_banking_connection(self, connection_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get Open Banking connection"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_open_banking_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Open Banking connection not found")
            
            return self._create_v1_response(result, "open_banking_connection_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting open banking connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get open banking connection")
    
    async def update_open_banking_connection(self, connection_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Update Open Banking connection"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_open_banking_connection",
                payload={
                    "connection_id": connection_id,
                    "updates": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "open_banking_connection_updated")
        except Exception as e:
            logger.error(f"Error updating open banking connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update open banking connection")
    
    async def delete_open_banking_connection(self, connection_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Delete Open Banking connection"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="delete_open_banking_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "open_banking_connection_deleted")
        except Exception as e:
            logger.error(f"Error deleting open banking connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete open banking connection")
    
    # Banking Transaction Endpoints
    async def get_banking_transactions(self, 
                                     request: Request,
                                     connection_id: Optional[str] = Query(None, description="Filter by connection"),
                                     start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                     end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                     context: HTTPRoutingContext = Depends(lambda: None)):
        """Get banking transactions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_banking_transactions",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "connection_id": connection_id,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "banking_transactions_retrieved")
        except Exception as e:
            logger.error(f"Error getting banking transactions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get banking transactions")
    
    async def sync_banking_transactions(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Sync banking transactions"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="sync_banking_transactions",
                payload={
                    "sync_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "banking_transactions_sync_initiated")
        except Exception as e:
            logger.error(f"Error syncing banking transactions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to sync banking transactions")
    
    # Banking Account Management Endpoints
    async def get_banking_accounts(self, 
                                 request: Request,
                                 connection_id: Optional[str] = Query(None, description="Filter by connection"),
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Get banking accounts"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_banking_accounts",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "connection_id": connection_id
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "banking_accounts_retrieved")
        except Exception as e:
            logger.error(f"Error getting banking accounts in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get banking accounts")
    
    async def get_account_balance(self, account_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get account balance"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_account_balance",
                payload={
                    "account_id": account_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "account_balance_retrieved")
        except Exception as e:
            logger.error(f"Error getting account balance {account_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get account balance")
    
    # Connection Health Endpoints
    async def test_banking_connection(self, connection_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Test banking connection"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="test_banking_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "banking_connection_tested")
        except Exception as e:
            logger.error(f"Error testing banking connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to test banking connection")
    
    async def get_banking_connection_health(self, connection_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get banking connection health"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_banking_connection_health",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "banking_connection_health_retrieved")
        except Exception as e:
            logger.error(f"Error getting banking connection health {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get banking connection health")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> JSONResponse:
        """Create standardized v1 response format"""
        response_data = {
            "success": True,
            "action": action,
            "api_version": "v1",
            "timestamp": "2024-12-31T00:00:00Z",
            "data": data
        }
        
        return JSONResponse(content=response_data, status_code=status_code)


def create_banking_router(role_detector: HTTPRoleDetector,
                         permission_guard: APIPermissionGuard,
                         message_router: MessageRouter) -> APIRouter:
    """Factory function to create Banking Router"""
    banking_endpoints = BankingEndpointsV1(role_detector, permission_guard, message_router)
    return banking_endpoints.router
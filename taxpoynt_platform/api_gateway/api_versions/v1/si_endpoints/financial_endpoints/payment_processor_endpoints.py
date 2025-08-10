"""
Payment Processor Integration Endpoints - API v1
================================================
System Integrator endpoints for payment processor integrations.
Covers: Nigerian (Paystack, Moniepoint, OPay, PalmPay, Interswitch), 
        African (Flutterwave), Global (Stripe)
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


class PaymentProcessorEndpointsV1:
    """
    Payment Processor Integration Endpoints - Version 1
    ===================================================
    Manages payment processor integrations for System Integrators:
    
    **Available Payment Processors:**
    - **Nigerian Processors (5)**: Paystack, Moniepoint, OPay, PalmPay, Interswitch
    - **African Processors (1)**: Flutterwave (Pan-African, 34+ countries)
    - **Global Processors (1)**: Stripe (International card processing)
    - **Unified Payment Aggregator**: Multi-processor transaction collection
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/payments", tags=["Payment Processors V1"])
        
        # Define available payment processors based on actual implementation
        self.payment_processors = {
            "nigerian": {
                "processors": ["paystack", "moniepoint", "opay", "palmpay", "interswitch"],
                "description": "Nigerian payment processors for transaction data collection",
                "features": ["transaction_data", "payment_data", "customer_data", "webhook_data"]
            },
            "african": {
                "processors": ["flutterwave"],
                "description": "Pan-African payment processors",
                "features": ["transaction_data", "payment_data", "customer_data", "multi_country"]
            },
            "global": {
                "processors": ["stripe"],
                "description": "Global payment processors for international transactions",
                "features": ["transaction_data", "payment_data", "customer_data", "international"]
            }
        }
        
        self._setup_routes()
        logger.info("Payment Processor Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup payment processor integration routes"""
        
        # Payment System Overview
        self.router.add_api_route(
            "/available-processors",
            self.get_available_payment_processors,
            methods=["GET"],
            summary="Get available payment processors",
            description="List all payment processors available for integration",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/connections",
            self.list_all_payment_connections,
            methods=["GET"],
            summary="List all payment connections",
            description="Get all payment processor connections for the SI",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/connections/summary",
            self.get_payment_connections_summary,
            methods=["GET"],
            summary="Get payment connections summary",
            description="Get aggregated statistics of all payment processor connections",
            response_model=V1ResponseModel
        )
        
        # Nigerian Payment Processors
        for processor in self.payment_processors["nigerian"]["processors"]:
            self._setup_payment_processor_routes(processor, "nigerian")
        
        # African Payment Processors
        for processor in self.payment_processors["african"]["processors"]:
            self._setup_payment_processor_routes(processor, "african")
        
        # Global Payment Processors
        for processor in self.payment_processors["global"]["processors"]:
            self._setup_payment_processor_routes(processor, "global")
        
        # Unified Payment Routes
        self.router.add_api_route(
            "/unified/transactions",
            self.get_unified_payment_transactions,
            methods=["GET"],
            summary="Get unified payment transactions",
            description="Get transactions from all connected payment processors",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/unified/summary",
            self.get_unified_payment_summary,
            methods=["GET"],
            summary="Get unified payment summary",
            description="Get aggregated payment statistics across all processors",
            response_model=V1ResponseModel
        )
        
        # Payment Webhooks
        self.router.add_api_route(
            "/webhooks/register",
            self.register_payment_webhooks,
            methods=["POST"],
            summary="Register payment webhooks",
            description="Register webhook endpoints for payment notifications",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/webhooks/list",
            self.list_payment_webhooks,
            methods=["GET"],
            summary="List payment webhooks",
            description="List all registered payment webhook endpoints",
            response_model=V1ResponseModel
        )
        
        # Transaction Processing Routes
        self.router.add_api_route(
            "/transactions/process",
            self.process_payment_transactions,
            methods=["POST"],
            summary="Process payment transactions",
            description="Process transactions from payment processors for e-invoicing",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/transactions/bulk-import",
            self.bulk_import_payment_transactions,
            methods=["POST"],
            summary="Bulk import payment transactions",
            description="Import transactions in bulk from payment processors",
            response_model=V1ResponseModel
        )
        
        # Connection Health and Testing
        self.router.add_api_route(
            "/connections/{connection_id}/test",
            self.test_payment_connection,
            methods=["POST"],
            summary="Test payment processor connection",
            description="Test connectivity and authentication for a payment processor connection",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/health",
            self.get_payment_connection_health,
            methods=["GET"],
            summary="Get payment connection health",
            description="Get detailed health status of a payment processor connection",
            response_model=V1ResponseModel
        )
    
    def _setup_payment_processor_routes(self, processor: str, region: str):
        """Setup routes for a specific payment processor"""
        
        prefix = f"/{region}/{processor}"
        
        # Connection management
        self.router.add_api_route(
            f"{prefix}/connections",
            self._create_payment_list_handler(processor, region),
            methods=["GET"],
            summary=f"List {processor} connections",
            description=f"Get all {processor} payment processor connections",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            f"{prefix}/connections",
            self._create_payment_create_handler(processor, region),
            methods=["POST"],
            summary=f"Create {processor} connection",
            description=f"Create new {processor} payment processor connection",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            f"{prefix}/connections/{connection_id}",
            self._create_payment_get_handler(processor, region),
            methods=["GET"],
            summary=f"Get {processor} connection",
            description=f"Get specific {processor} connection details",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            f"{prefix}/connections/{connection_id}",
            self._create_payment_update_handler(processor, region),
            methods=["PUT"],
            summary=f"Update {processor} connection",
            description=f"Update {processor} connection configuration",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            f"{prefix}/connections/{connection_id}",
            self._create_payment_delete_handler(processor, region),
            methods=["DELETE"],
            summary=f"Delete {processor} connection",
            description=f"Remove {processor} connection",
            response_model=V1ResponseModel
        )
        
        # Transaction specific routes
        self.router.add_api_route(
            f"{prefix}/transactions",
            self._create_payment_transactions_handler(processor, region),
            methods=["GET"],
            summary=f"Get {processor} transactions",
            description=f"Retrieve transactions from {processor}",
            response_model=V1ResponseModel
        )
    
    # Dynamic handler creators for payment processors
    def _create_payment_list_handler(self, processor: str, region: str):
        async def list_connections(
            request: Request,
            organization_id: Optional[str] = Query(None, description="Filter by organization"),
            status: Optional[str] = Query(None, description="Filter by connection status"),
            context: HTTPRoutingContext = Depends(lambda: None)
        ):
            try:
                result = await self.message_router.route_message(
                    service_role=ServiceRole.SYSTEM_INTEGRATOR,
                    operation=f"list_{processor}_connections",
                    payload={
                        "si_id": context.user_id,
                        "processor": processor,
                        "region": region,
                        "filters": {
                            "organization_id": organization_id,
                            "status": status
                        },
                        "api_version": "v1"
                    }
                )
                
                return self._create_v1_response(result, f"{processor}_connections_listed")
            except Exception as e:
                logger.error(f"Error listing {processor} connections in v1: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list {processor} connections")
        
        return list_connections
    
    def _create_payment_create_handler(self, processor: str, region: str):
        async def create_connection(
            request: Request,
            context: HTTPRoutingContext = Depends(lambda: None)
        ):
            try:
                body = await request.json()
                
                # Validate required fields
                required_fields = ["organization_id", "connection_config"]
                missing_fields = [field for field in required_fields if field not in body]
                if missing_fields:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required fields: {', '.join(missing_fields)}"
                    )
                
                result = await self.message_router.route_message(
                    service_role=ServiceRole.SYSTEM_INTEGRATOR,
                    operation=f"create_{processor}_connection",
                    payload={
                        "connection_data": body,
                        "si_id": context.user_id,
                        "processor": processor,
                        "region": region,
                        "api_version": "v1"
                    }
                )
                
                return self._create_v1_response(result, f"{processor}_connection_created", status_code=201)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error creating {processor} connection in v1: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create {processor} connection")
        
        return create_connection
    
    def _create_payment_get_handler(self, processor: str, region: str):
        async def get_connection(
            connection_id: str,
            context: HTTPRoutingContext = Depends(lambda: None)
        ):
            try:
                result = await self.message_router.route_message(
                    service_role=ServiceRole.SYSTEM_INTEGRATOR,
                    operation=f"get_{processor}_connection",
                    payload={
                        "connection_id": connection_id,
                        "si_id": context.user_id,
                        "processor": processor,
                        "region": region,
                        "api_version": "v1"
                    }
                )
                
                if not result:
                    raise HTTPException(status_code=404, detail=f"{processor} connection not found")
                
                return self._create_v1_response(result, f"{processor}_connection_retrieved")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting {processor} connection {connection_id} in v1: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get {processor} connection")
        
        return get_connection
    
    def _create_payment_update_handler(self, processor: str, region: str):
        async def update_connection(
            connection_id: str,
            request: Request,
            context: HTTPRoutingContext = Depends(lambda: None)
        ):
            try:
                body = await request.json()
                
                result = await self.message_router.route_message(
                    service_role=ServiceRole.SYSTEM_INTEGRATOR,
                    operation=f"update_{processor}_connection",
                    payload={
                        "connection_id": connection_id,
                        "updates": body,
                        "si_id": context.user_id,
                        "processor": processor,
                        "region": region,
                        "api_version": "v1"
                    }
                )
                
                return self._create_v1_response(result, f"{processor}_connection_updated")
            except Exception as e:
                logger.error(f"Error updating {processor} connection {connection_id} in v1: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to update {processor} connection")
        
        return update_connection
    
    def _create_payment_delete_handler(self, processor: str, region: str):
        async def delete_connection(
            connection_id: str,
            context: HTTPRoutingContext = Depends(lambda: None)
        ):
            try:
                result = await self.message_router.route_message(
                    service_role=ServiceRole.SYSTEM_INTEGRATOR,
                    operation=f"delete_{processor}_connection",
                    payload={
                        "connection_id": connection_id,
                        "si_id": context.user_id,
                        "processor": processor,
                        "region": region,
                        "api_version": "v1"
                    }
                )
                
                return self._create_v1_response(result, f"{processor}_connection_deleted")
            except Exception as e:
                logger.error(f"Error deleting {processor} connection {connection_id} in v1: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to delete {processor} connection")
        
        return delete_connection
    
    def _create_payment_transactions_handler(self, processor: str, region: str):
        async def get_transactions(
            request: Request,
            connection_id: Optional[str] = Query(None, description="Filter by connection"),
            start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
            end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
            context: HTTPRoutingContext = Depends(lambda: None)
        ):
            try:
                result = await self.message_router.route_message(
                    service_role=ServiceRole.SYSTEM_INTEGRATOR,
                    operation=f"get_{processor}_transactions",
                    payload={
                        "si_id": context.user_id,
                        "processor": processor,
                        "region": region,
                        "filters": {
                            "connection_id": connection_id,
                            "start_date": start_date,
                            "end_date": end_date
                        },
                        "api_version": "v1"
                    }
                )
                
                return self._create_v1_response(result, f"{processor}_transactions_retrieved")
            except Exception as e:
                logger.error(f"Error getting {processor} transactions in v1: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get {processor} transactions")
        
        return get_transactions
    
    # Payment System Overview Endpoints
    async def get_available_payment_processors(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get all available payment processors"""
        try:
            # Calculate totals
            nigerian_count = len(self.payment_processors["nigerian"]["processors"])
            african_count = len(self.payment_processors["african"]["processors"])
            global_count = len(self.payment_processors["global"]["processors"])
            
            result = {
                "payment_processors": self.payment_processors,
                "totals": {
                    "nigerian_processors": nigerian_count,
                    "african_processors": african_count,
                    "global_processors": global_count,
                    "total_processors": nigerian_count + african_count + global_count
                },
                "regions": ["nigerian", "african", "global"]
            }
            
            return self._create_v1_response(result, "available_payment_processors_retrieved")
        except Exception as e:
            logger.error(f"Error getting available payment processors in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get available payment processors")
    
    async def list_all_payment_connections(self, 
                                         request: Request,
                                         context: HTTPRoutingContext = Depends(lambda: None)):
        """List all payment processor connections"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_all_payment_connections",
                payload={
                    "si_id": context.user_id,
                    "filters": dict(request.query_params),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "all_payment_connections_listed")
        except Exception as e:
            logger.error(f"Error listing all payment connections in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list all payment connections")
    
    async def get_payment_connections_summary(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get payment connections summary"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_payment_connections_summary",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "payment_connections_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting payment connections summary in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get payment connections summary")
    
    # Unified Payment Endpoints
    async def get_unified_payment_transactions(self, 
                                             request: Request,
                                             start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                             end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                             processor: Optional[str] = Query(None, description="Filter by processor"),
                                             context: HTTPRoutingContext = Depends(lambda: None)):
        """Get unified payment transactions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_unified_payment_transactions",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "start_date": start_date,
                        "end_date": end_date,
                        "processor": processor
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "unified_payment_transactions_retrieved")
        except Exception as e:
            logger.error(f"Error getting unified payment transactions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get unified payment transactions")
    
    async def get_unified_payment_summary(self, 
                                        period: Optional[str] = Query("30d", description="Summary period"),
                                        context: HTTPRoutingContext = Depends(lambda: None)):
        """Get unified payment summary"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_unified_payment_summary",
                payload={
                    "si_id": context.user_id,
                    "period": period,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "unified_payment_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting unified payment summary in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get unified payment summary")
    
    # Payment Webhook Endpoints
    async def register_payment_webhooks(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Register payment webhooks"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="register_payment_webhooks",
                payload={
                    "webhook_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "payment_webhooks_registered")
        except Exception as e:
            logger.error(f"Error registering payment webhooks in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to register payment webhooks")
    
    async def list_payment_webhooks(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """List payment webhooks"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_payment_webhooks",
                payload={
                    "si_id": context.user_id,
                    "filters": dict(request.query_params),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "payment_webhooks_listed")
        except Exception as e:
            logger.error(f"Error listing payment webhooks in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list payment webhooks")
    
    # Transaction Processing Endpoints
    async def process_payment_transactions(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Process payment transactions"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_payment_transactions",
                payload={
                    "processing_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "payment_transactions_processing_initiated")
        except Exception as e:
            logger.error(f"Error processing payment transactions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to process payment transactions")
    
    async def bulk_import_payment_transactions(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Bulk import payment transactions"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="bulk_import_payment_transactions",
                payload={
                    "import_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bulk_payment_import_initiated")
        except Exception as e:
            logger.error(f"Error bulk importing payment transactions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk import payment transactions")
    
    # Connection Health Endpoints
    async def test_payment_connection(self, connection_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Test payment processor connection"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="test_payment_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "payment_connection_tested")
        except Exception as e:
            logger.error(f"Error testing payment connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to test payment connection")
    
    async def get_payment_connection_health(self, connection_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get payment connection health"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_payment_connection_health",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "payment_connection_health_retrieved")
        except Exception as e:
            logger.error(f"Error getting payment connection health {connection_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get payment connection health")
    
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


def create_payment_processor_router(role_detector: HTTPRoleDetector,
                                   permission_guard: APIPermissionGuard,
                                   message_router: MessageRouter) -> APIRouter:
    """Factory function to create Payment Processor Router"""
    payment_endpoints = PaymentProcessorEndpointsV1(role_detector, permission_guard, message_router)
    return payment_endpoints.router
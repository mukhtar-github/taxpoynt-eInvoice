"""
SI Subscription Integration Examples

This module provides examples of how to integrate existing SI services
with the new subscription tier management system.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from .si_tier_manager import SITierManager, SIUsageType
from .si_tier_validator import SITierValidator, require_si_tier
from .si_usage_tracker import SIUsageTracker
from .si_subscription_guard import SISubscriptionGuard, SIAccessRequest, SIAccessDecision

logger = logging.getLogger(__name__)


class EnhancedERPIntegrationService:
    """
    Example of how to enhance existing ERP integration service
    with subscription tier management
    """
    
    def __init__(
        self,
        si_tier_manager: SITierManager,
        si_usage_tracker: SIUsageTracker,
        si_subscription_guard: SISubscriptionGuard
    ):
        self.si_tier_manager = si_tier_manager
        self.si_usage_tracker = si_usage_tracker
        self.si_subscription_guard = si_subscription_guard
        self._si_tier_validator = None  # Would be injected
    
    @require_si_tier("erp_basic_connection")
    async def connect_to_erp(
        self,
        organization_id: str,
        erp_type: str,
        connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Connect to ERP system with tier validation"""
        
        # Validate access
        access_request = SIAccessRequest(
            request_id=f"erp_connect_{int(datetime.now().timestamp())}",
            organization_id=organization_id,
            service_name="erp_integration",
            operation_type="erp_connect",
            requested_resources={"erp_connections": 1}
        )
        
        access_response = await self.si_subscription_guard.validate_si_access(access_request)
        
        if not access_response.allowed:
            return {
                "success": False,
                "error": access_response.reason,
                "decision": access_response.decision.value,
                "required_tier": access_response.required_tier
            }
        
        try:
            # Perform actual ERP connection
            connection_result = await self._perform_erp_connection(
                erp_type, connection_config
            )
            
            if connection_result["success"]:
                # Record successful connection usage
                await self.si_usage_tracker.record_si_usage(
                    organization_id,
                    SIUsageType.ERP_CONNECTIONS,
                    1,
                    metadata={
                        "erp_type": erp_type,
                        "connection_id": connection_result.get("connection_id")
                    }
                )
            
            return connection_result
            
        except Exception as e:
            logger.error(f"ERP connection failed for {organization_id}: {e}")
            return {
                "success": False,
                "error": f"Connection failed: {str(e)}"
            }
    
    @require_si_tier("erp_advanced_integration")
    async def sync_erp_data(
        self,
        organization_id: str,
        connection_id: str,
        data_types: List[str],
        sync_mode: str = "incremental"
    ) -> Dict[str, Any]:
        """Sync data from ERP with advanced tier requirement"""
        
        # Check if bulk sync requires higher tier
        if sync_mode == "bulk":
            access_request = SIAccessRequest(
                request_id=f"erp_bulk_sync_{int(datetime.now().timestamp())}",
                organization_id=organization_id,
                service_name="erp_integration",
                operation_type="erp_bulk_sync",
                requested_resources={"bulk_operations": 1, "api_calls": len(data_types) * 10}
            )
        else:
            access_request = SIAccessRequest(
                request_id=f"erp_sync_{int(datetime.now().timestamp())}",
                organization_id=organization_id,
                service_name="erp_integration", 
                operation_type="erp_sync_data",
                requested_resources={"api_calls": len(data_types)}
            )
        
        access_response = await self.si_subscription_guard.validate_si_access(access_request)
        
        if not access_response.allowed:
            return {
                "success": False,
                "error": access_response.reason,
                "recommended_action": access_response.recommended_actions[0] if access_response.recommended_actions else None
            }
        
        # Perform data sync
        sync_result = await self._perform_data_sync(
            connection_id, data_types, sync_mode
        )
        
        return sync_result
    
    async def get_erp_capabilities(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get ERP capabilities based on subscription tier"""
        
        tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
        
        if not tier_config:
            return {
                "error": "No valid subscription found",
                "capabilities": {}
            }
        
        capabilities = {
            "basic_connection": tier_config.features.basic_erp_integration,
            "advanced_integration": tier_config.features.advanced_erp_integration,
            "multi_erp_support": tier_config.features.multi_erp_support,
            "custom_connectors": tier_config.features.custom_erp_connectors,
            "real_time_sync": tier_config.features.real_time_data_sync,
            "custom_mappings": tier_config.features.custom_data_mappings
        }
        
        limits = {
            "max_connections": tier_config.limits.erp_connections,
            "api_calls_per_minute": tier_config.limits.api_calls_per_minute,
            "concurrent_sessions": tier_config.limits.concurrent_sessions
        }
        
        return {
            "tier": tier_config.tier.value,
            "capabilities": capabilities,
            "limits": limits
        }
    
    async def _perform_erp_connection(
        self,
        erp_type: str,
        connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate ERP connection logic"""
        return {
            "success": True,
            "connection_id": f"erp_{erp_type}_{int(datetime.now().timestamp())}",
            "erp_type": erp_type
        }
    
    async def _perform_data_sync(
        self,
        connection_id: str,
        data_types: List[str],
        sync_mode: str
    ) -> Dict[str, Any]:
        """Simulate data sync logic"""
        return {
            "success": True,
            "records_synced": len(data_types) * 100,
            "sync_mode": sync_mode
        }


class EnhancedDocumentProcessingService:
    """
    Example of how to enhance document processing service
    with subscription tier management
    """
    
    def __init__(
        self,
        si_tier_manager: SITierManager,
        si_usage_tracker: SIUsageTracker,
        si_subscription_guard: SISubscriptionGuard
    ):
        self.si_tier_manager = si_tier_manager
        self.si_usage_tracker = si_usage_tracker
        self.si_subscription_guard = si_subscription_guard
    
    async def process_invoice(
        self,
        organization_id: str,
        invoice_data: Dict[str, Any],
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process single invoice with tier validation"""
        
        access_request = SIAccessRequest(
            request_id=f"process_invoice_{int(datetime.now().timestamp())}",
            organization_id=organization_id,
            service_name="document_processing",
            operation_type="process_invoice",
            requested_resources={"invoices_processed": 1}
        )
        
        access_response = await self.si_subscription_guard.validate_si_access(access_request)
        
        if not access_response.allowed:
            return {
                "success": False,
                "error": access_response.reason,
                "decision": access_response.decision.value,
                "overage_cost": access_response.overage_cost
            }
        
        # Process invoice
        processing_result = await self._process_single_invoice(
            invoice_data, processing_options
        )
        
        # Record usage is handled by the decorator/guard
        
        return processing_result
    
    async def process_bulk_invoices(
        self,
        organization_id: str,
        invoice_batch: List[Dict[str, Any]],
        processing_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process bulk invoices with tier and usage validation"""
        
        batch_size = len(invoice_batch)
        
        # Check feasibility first
        feasibility = await self.si_subscription_guard.check_operation_feasibility(
            organization_id,
            "process_bulk_invoices",
            {"invoices_processed": batch_size, "bulk_operations": 1}
        )
        
        if not feasibility["feasible"]:
            return {
                "success": False,
                "error": feasibility["reason"],
                "total_overage_cost": feasibility.get("total_overage_cost", 0),
                "recommendations": feasibility.get("recommendations", [])
            }
        
        # Validate access
        access_request = SIAccessRequest(
            request_id=f"bulk_process_{int(datetime.now().timestamp())}",
            organization_id=organization_id,
            service_name="document_processing",
            operation_type="process_bulk_invoices",
            requested_resources={
                "invoices_processed": batch_size,
                "bulk_operations": 1
            }
        )
        
        access_response = await self.si_subscription_guard.validate_si_access(access_request)
        
        if not access_response.allowed:
            return {
                "success": False,
                "error": access_response.reason,
                "overage_cost": access_response.overage_cost
            }
        
        # Process bulk invoices
        processing_result = await self._process_invoice_batch(
            invoice_batch, processing_options
        )
        
        return processing_result
    
    async def get_processing_capabilities(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get processing capabilities based on tier"""
        
        tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
        
        if not tier_config:
            return {"error": "No valid subscription found"}
        
        capabilities = {
            "standard_processing": tier_config.features.standard_document_processing,
            "advanced_processing": tier_config.features.advanced_document_processing,
            "bulk_processing": tier_config.features.bulk_document_processing,
            "custom_templates": tier_config.features.custom_document_templates
        }
        
        # Get current usage
        current_usage = await self.si_usage_tracker.get_current_usage(
            organization_id, SIUsageType.INVOICES_PROCESSED
        )
        
        limits = {
            "monthly_limit": tier_config.limits.invoices_per_month,
            "current_usage": current_usage.get(SIUsageType.INVOICES_PROCESSED.value, 0),
            "bulk_operations_per_day": tier_config.limits.bulk_operations_per_day
        }
        
        return {
            "tier": tier_config.tier.value,
            "capabilities": capabilities,
            "limits": limits,
            "overage_rate": float(tier_config.overage_rate)
        }
    
    async def _process_single_invoice(
        self,
        invoice_data: Dict[str, Any],
        processing_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Simulate single invoice processing"""
        return {
            "success": True,
            "invoice_id": f"inv_{int(datetime.now().timestamp())}",
            "processing_time_ms": 1500,
            "validation_status": "passed"
        }
    
    async def _process_invoice_batch(
        self,
        invoice_batch: List[Dict[str, Any]],
        processing_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Simulate bulk invoice processing"""
        successful = len(invoice_batch)
        failed = 0
        
        return {
            "success": True,
            "batch_id": f"batch_{int(datetime.now().timestamp())}",
            "total_invoices": len(invoice_batch),
            "successful": successful,
            "failed": failed,
            "processing_time_ms": len(invoice_batch) * 800,
            "cost_per_invoice": 0.02
        }


class TierAwareAPIService:
    """
    Example of how to make API endpoints tier-aware
    """
    
    def __init__(
        self,
        si_tier_manager: SITierManager,
        si_tier_validator: SITierValidator,
        si_usage_tracker: SIUsageTracker
    ):
        self.si_tier_manager = si_tier_manager
        self.si_tier_validator = si_tier_validator
        self.si_usage_tracker = si_usage_tracker
    
    async def handle_api_request(
        self,
        organization_id: str,
        endpoint: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle API request with tier-based rate limiting"""
        
        # Validate API access based on endpoint
        validation = await self.si_tier_validator.validate_api_access(
            organization_id, endpoint
        )
        
        if not validation.allowed:
            return {
                "error": validation.reason,
                "status_code": 403,
                "required_tier": validation.required_tier,
                "current_tier": validation.current_tier
            }
        
        # Record API usage
        await self.si_usage_tracker.record_si_usage(
            organization_id,
            SIUsageType.API_CALLS,
            1,
            metadata={
                "endpoint": endpoint,
                "request_size": len(str(request_data))
            }
        )
        
        # Get rate limit info for response headers
        rate_limit_info = validation.metadata.get("rate_limit", 100)
        
        # Process the actual API request
        response_data = await self._process_api_request(endpoint, request_data)
        
        response_data["rate_limit_remaining"] = rate_limit_info
        
        return response_data
    
    async def _process_api_request(
        self,
        endpoint: str,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simulate API request processing"""
        return {
            "success": True,
            "data": {"processed": True},
            "processing_time_ms": 200
        }


# FastAPI Integration Examples

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Dependency injection setup (would be configured in main app)
async def get_si_tier_manager() -> SITierManager:
    # Return configured SI tier manager
    pass

async def get_si_subscription_guard() -> SISubscriptionGuard:
    # Return configured SI subscription guard
    pass

def get_organization_id(request: Request) -> str:
    # Extract organization ID from request (JWT, headers, etc.)
    return request.headers.get("X-Organization-ID", "")


@app.post("/api/v1/si/erp/connect")
async def connect_erp_endpoint(
    request_data: Dict[str, Any],
    organization_id: str = Depends(get_organization_id),
    si_guard: SISubscriptionGuard = Depends(get_si_subscription_guard)
):
    """FastAPI endpoint with SI subscription protection"""
    
    # Create access request
    access_request = SIAccessRequest(
        request_id=f"api_erp_connect_{int(datetime.now().timestamp())}",
        organization_id=organization_id,
        service_name="erp_integration",
        operation_type="erp_connect",
        requested_resources={"erp_connections": 1}
    )
    
    # Validate access
    access_response = await si_guard.validate_si_access(access_request)
    
    if not access_response.allowed:
        status_code = 403
        if access_response.decision == SIAccessDecision.SUBSCRIPTION_EXPIRED:
            status_code = 402
        elif access_response.decision == SIAccessDecision.USAGE_LIMIT_EXCEEDED:
            status_code = 429
        
        raise HTTPException(
            status_code=status_code,
            detail=access_response.reason,
            headers={
                "X-Required-Tier": access_response.required_tier or "",
                "X-Current-Tier": access_response.current_tier or "",
                "X-Overage-Cost": str(access_response.overage_cost or 0)
            }
        )
    
    # Process the request
    erp_service = EnhancedERPIntegrationService(None, None, si_guard)
    result = await erp_service._perform_erp_connection(
        request_data.get("erp_type", ""),
        request_data.get("config", {})
    )
    
    return JSONResponse(
        content=result,
        headers={
            "X-Tier": access_response.current_tier or "",
            "X-Usage-Remaining": str(access_response.usage_info.get("remaining", "unknown"))
        }
    )


@app.get("/api/v1/si/subscription/status")
async def get_subscription_status(
    organization_id: str = Depends(get_organization_id),
    si_guard: SISubscriptionGuard = Depends(get_si_subscription_guard)
):
    """Get comprehensive subscription status for organization"""
    
    access_summary = await si_guard.get_access_summary(organization_id)
    
    return JSONResponse(content=access_summary)


@app.get("/api/v1/si/tiers/comparison")
async def get_tier_comparison(
    si_tier_manager: SITierManager = Depends(get_si_tier_manager)
):
    """Get tier comparison for pricing page"""
    
    comparison = await si_tier_manager.get_si_tier_comparison()
    
    return JSONResponse(content=comparison)
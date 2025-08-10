"""
Hybrid Endpoints - API Version 1
================================
Version 1 of Hybrid endpoints for cross-role functionality and shared operations.

**Hybrid Role Context:**
Hybrid endpoints serve functionality that spans multiple roles or requires
coordination between System Integrators and Access Point Providers.

**Professional Structure:**
- Cross-Role Operations: Functionality requiring both SI and APP capabilities
- Shared Resources: Common resources accessed by multiple roles
- Orchestration: Complex workflows involving multiple role interactions
- Integration Monitoring: Cross-system health and performance monitoring
- Collaborative Workflows: Multi-role business process coordination
"""

from .cross_role_endpoints import create_cross_role_router
from .shared_resources_endpoints import create_shared_resources_router
from .orchestration_endpoints import create_orchestration_router
from .monitoring_endpoints import create_monitoring_router
from .main_router import create_hybrid_v1_router

__all__ = [
    "create_cross_role_router",
    "create_shared_resources_router",
    "create_orchestration_router",
    "create_monitoring_router",
    "create_hybrid_v1_router"
]
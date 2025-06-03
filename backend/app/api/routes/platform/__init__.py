"""
Platform-specific API routes for TaxPoynt eInvoice.

This module contains routes for platform features (formerly known as APP layer),
separated from system integration routes.
"""

from fastapi import APIRouter

# Import all platform route modules
from app.api.routes.platform.signatures import router as signatures_router
from app.api.routes.platform.signature_test import router as signature_test_router
from app.api.routes.platform.signature_events import router as signature_events_router

# Create the main platform router
router = APIRouter(prefix="/platform", tags=["platform"])

# Include all platform route modules
router.include_router(signatures_router)
router.include_router(signature_test_router)
router.include_router(signature_events_router)

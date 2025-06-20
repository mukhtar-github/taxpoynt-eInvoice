"""
Scheduled tasks package for TaxPoynt eInvoice.

This package contains scheduled tasks that run periodically to automate system operations.
"""
from app.tasks.irn_tasks import expire_outdated_irns, clean_up_validation_records
from app.tasks.hubspot_tasks import (
    process_hubspot_deal, 
    sync_hubspot_deals, 
    batch_process_hubspot_deals,
    hubspot_deal_processor_task
)

# Export task functions
__all__ = [
    "expire_outdated_irns", 
    "clean_up_validation_records",
    "process_hubspot_deal",
    "sync_hubspot_deals",
    "batch_process_hubspot_deals",
    "hubspot_deal_processor_task"
]

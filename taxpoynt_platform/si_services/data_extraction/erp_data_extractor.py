"""
ERP Data Extractor Service

This module provides core functionality for extracting invoice data from various ERP systems.
Supports multiple ERP platforms with pluggable adapter architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ERPType(Enum):
    """Supported ERP system types"""
    ODOO = "odoo"
    SAP = "sap"
    QUICKBOOKS = "quickbooks"
    SAGE = "sage"
    ORACLE = "oracle"
    CUSTOM = "custom"


class ExtractionStatus(Enum):
    """Status of data extraction operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ExtractionFilter:
    """Filter criteria for data extraction"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    company_ids: Optional[List[str]] = None
    invoice_types: Optional[List[str]] = None
    status_filter: Optional[List[str]] = None
    batch_size: int = 1000
    include_draft: bool = False
    include_cancelled: bool = False


@dataclass
class ExtractionResult:
    """Result of data extraction operation"""
    extraction_id: str
    status: ExtractionStatus
    total_records: int
    extracted_records: int
    failed_records: int
    start_time: datetime
    end_time: Optional[datetime]
    error_details: Optional[List[Dict]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class InvoiceData:
    """Standardized invoice data structure"""
    invoice_id: str
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime]
    customer_id: str
    customer_name: str
    customer_tin: Optional[str]
    currency: str
    subtotal: float
    tax_amount: float
    total_amount: float
    line_items: List[Dict[str, Any]]
    payment_terms: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ERPAdapter(ABC):
    """Abstract base class for ERP system adapters"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.connection_config = connection_config
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to ERP system"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to ERP system"""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test ERP system connectivity"""
        pass
    
    @abstractmethod
    async def extract_invoices(self, filters: ExtractionFilter) -> List[InvoiceData]:
        """Extract invoice data from ERP system"""
        pass
    
    @abstractmethod
    async def get_invoice_count(self, filters: ExtractionFilter) -> int:
        """Get count of invoices matching filters"""
        pass
    
    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Validate ERP system credentials"""
        pass


class OdooAdapter(ERPAdapter):
    """Odoo ERP system adapter"""
    
    async def connect(self) -> bool:
        try:
            # Implementation for Odoo connection
            # This would use xmlrpc or REST API
            logger.info("Connecting to Odoo ERP system")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            return False
    
    async def disconnect(self) -> None:
        self.is_connected = False
        logger.info("Disconnected from Odoo ERP system")
    
    async def test_connection(self) -> bool:
        if not self.is_connected:
            return await self.connect()
        return True
    
    async def extract_invoices(self, filters: ExtractionFilter) -> List[InvoiceData]:
        invoices = []
        try:
            # Implementation for Odoo invoice extraction
            # This would query Odoo's account.move model
            logger.info(f"Extracting invoices from Odoo with filters: {filters}")
            
            # Mock implementation - replace with actual Odoo API calls
            sample_invoice = InvoiceData(
                invoice_id="odoo_001",
                invoice_number="INV/2024/001",
                invoice_date=datetime.now(),
                due_date=datetime.now() + timedelta(days=30),
                customer_id="customer_001",
                customer_name="Test Customer",
                customer_tin="12345678901",
                currency="NGN",
                subtotal=100000.0,
                tax_amount=7500.0,
                total_amount=107500.0,
                line_items=[],
                status="posted",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            invoices.append(sample_invoice)
            
        except Exception as e:
            logger.error(f"Failed to extract invoices from Odoo: {e}")
            raise
        
        return invoices
    
    async def get_invoice_count(self, filters: ExtractionFilter) -> int:
        try:
            # Implementation for counting Odoo invoices
            return 1  # Mock count
        except Exception as e:
            logger.error(f"Failed to get invoice count from Odoo: {e}")
            return 0
    
    async def validate_credentials(self) -> bool:
        try:
            # Implementation for Odoo credential validation
            return True
        except Exception as e:
            logger.error(f"Failed to validate Odoo credentials: {e}")
            return False


class SAPAdapter(ERPAdapter):
    """SAP ERP system adapter"""
    
    async def connect(self) -> bool:
        try:
            logger.info("Connecting to SAP ERP system")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to SAP: {e}")
            return False
    
    async def disconnect(self) -> None:
        self.is_connected = False
        logger.info("Disconnected from SAP ERP system")
    
    async def test_connection(self) -> bool:
        if not self.is_connected:
            return await self.connect()
        return True
    
    async def extract_invoices(self, filters: ExtractionFilter) -> List[InvoiceData]:
        # Implementation for SAP invoice extraction
        return []
    
    async def get_invoice_count(self, filters: ExtractionFilter) -> int:
        return 0
    
    async def validate_credentials(self) -> bool:
        return True


class ERPDataExtractor:
    """Main service for extracting data from ERP systems"""
    
    def __init__(self):
        self.adapters: Dict[ERPType, ERPAdapter] = {}
        self.active_extractions: Dict[str, ExtractionResult] = {}
    
    def register_adapter(self, erp_type: ERPType, adapter: ERPAdapter) -> None:
        """Register an ERP adapter"""
        self.adapters[erp_type] = adapter
        logger.info(f"Registered adapter for {erp_type.value}")
    
    def get_adapter(self, erp_type: ERPType) -> Optional[ERPAdapter]:
        """Get registered adapter for ERP type"""
        return self.adapters.get(erp_type)
    
    @asynccontextmanager
    async def get_connection(self, erp_type: ERPType):
        """Context manager for ERP connections"""
        adapter = self.get_adapter(erp_type)
        if not adapter:
            raise ValueError(f"No adapter registered for {erp_type.value}")
        
        try:
            await adapter.connect()
            yield adapter
        finally:
            await adapter.disconnect()
    
    async def extract_data(
        self,
        erp_type: ERPType,
        filters: ExtractionFilter,
        extraction_id: Optional[str] = None
    ) -> ExtractionResult:
        """Extract invoice data from specified ERP system"""
        
        if extraction_id is None:
            extraction_id = f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = ExtractionResult(
            extraction_id=extraction_id,
            status=ExtractionStatus.PENDING,
            total_records=0,
            extracted_records=0,
            failed_records=0,
            start_time=datetime.now(),
            end_time=None
        )
        
        self.active_extractions[extraction_id] = result
        
        try:
            result.status = ExtractionStatus.IN_PROGRESS
            
            async with self.get_connection(erp_type) as adapter:
                # Get total count
                total_count = await adapter.get_invoice_count(filters)
                result.total_records = total_count
                
                # Extract invoices
                invoices = await adapter.extract_invoices(filters)
                result.extracted_records = len(invoices)
                result.failed_records = total_count - len(invoices)
                
                # Process extracted data
                await self._process_extracted_data(invoices, result)
                
                result.status = ExtractionStatus.COMPLETED
                
        except Exception as e:
            logger.error(f"Extraction failed for {extraction_id}: {e}")
            result.status = ExtractionStatus.FAILED
            result.error_details = [{"error": str(e), "timestamp": datetime.now()}]
        
        finally:
            result.end_time = datetime.now()
        
        return result
    
    async def _process_extracted_data(
        self,
        invoices: List[InvoiceData],
        result: ExtractionResult
    ) -> None:
        """Process and validate extracted invoice data"""
        try:
            # Data validation and transformation logic
            valid_invoices = []
            invalid_invoices = []
            
            for invoice in invoices:
                if await self._validate_invoice_data(invoice):
                    valid_invoices.append(invoice)
                else:
                    invalid_invoices.append(invoice)
            
            result.metadata = {
                "valid_invoices": len(valid_invoices),
                "invalid_invoices": len(invalid_invoices),
                "processing_time": (datetime.now() - result.start_time).total_seconds()
            }
            
            logger.info(f"Processed {len(valid_invoices)} valid invoices")
            
        except Exception as e:
            logger.error(f"Failed to process extracted data: {e}")
            raise
    
    async def _validate_invoice_data(self, invoice: InvoiceData) -> bool:
        """Validate individual invoice data"""
        try:
            # Basic validation rules
            if not invoice.invoice_number or not invoice.customer_id:
                return False
            
            if invoice.total_amount <= 0:
                return False
            
            if not invoice.invoice_date:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation failed for invoice {invoice.invoice_id}: {e}")
            return False
    
    async def get_extraction_status(self, extraction_id: str) -> Optional[ExtractionResult]:
        """Get status of an ongoing extraction"""
        return self.active_extractions.get(extraction_id)
    
    async def cancel_extraction(self, extraction_id: str) -> bool:
        """Cancel an ongoing extraction"""
        if extraction_id in self.active_extractions:
            result = self.active_extractions[extraction_id]
            if result.status == ExtractionStatus.IN_PROGRESS:
                result.status = ExtractionStatus.FAILED
                result.end_time = datetime.now()
                result.error_details = [{"error": "Extraction cancelled", "timestamp": datetime.now()}]
                return True
        return False
    
    def get_supported_erp_types(self) -> List[ERPType]:
        """Get list of supported ERP types"""
        return list(self.adapters.keys())


# Factory function for creating adapters
def create_adapter(erp_type: ERPType, connection_config: Dict[str, Any]) -> ERPAdapter:
    """Factory function to create ERP adapters"""
    adapter_classes = {
        ERPType.ODOO: OdooAdapter,
        ERPType.SAP: SAPAdapter,
        # Add more adapters as needed
    }
    
    adapter_class = adapter_classes.get(erp_type)
    if not adapter_class:
        raise ValueError(f"Unsupported ERP type: {erp_type.value}")
    
    return adapter_class(connection_config)


# Service instance
erp_data_extractor = ERPDataExtractor()
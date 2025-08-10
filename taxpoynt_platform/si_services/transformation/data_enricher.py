"""
Data Enricher Service

This service enriches incomplete or missing data in invoice records
by leveraging external data sources, defaults, and intelligent inference.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class EnrichmentSource(Enum):
    """Sources for data enrichment"""
    DATABASE_LOOKUP = "database_lookup"
    EXTERNAL_API = "external_api"
    DEFAULT_VALUES = "default_values"
    CALCULATED_VALUES = "calculated_values"
    HISTORICAL_DATA = "historical_data"
    INFERENCE_ENGINE = "inference_engine"


@dataclass
class EnrichmentRule:
    """Rule for data enrichment"""
    field_name: str
    source: EnrichmentSource
    priority: int
    lookup_key: Optional[str] = None
    default_value: Any = None
    calculation_function: Optional[str] = None
    external_api_endpoint: Optional[str] = None
    required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class EnrichmentResult:
    """Result of data enrichment operation"""
    original_data: Dict[str, Any]
    enriched_data: Dict[str, Any]
    enrichment_log: List[Dict[str, str]]
    success: bool
    errors: List[str]


class DatabaseLookupService:
    """Service for database lookups to enrich data"""
    
    def __init__(self, db_connection=None):
        self.db_connection = db_connection
    
    async def lookup_customer_data(self, tin: str) -> Optional[Dict[str, Any]]:
        """Lookup customer data by TIN"""
        if not self.db_connection:
            return None
        
        try:
            # Simulated database lookup
            query = """
            SELECT name, address, phone, email, business_type
            FROM customers 
            WHERE tin = %s
            """
            # Execute query and return results
            # This would be actual database query in production
            return {
                "name": "Sample Customer Name",
                "address": "Sample Address",
                "phone": "+234-XXX-XXXX",
                "email": "customer@example.com",
                "business_type": "Limited Company"
            }
        except Exception as e:
            logger.error(f"Database lookup error for TIN {tin}: {str(e)}")
            return None
    
    async def lookup_supplier_data(self, tin: str) -> Optional[Dict[str, Any]]:
        """Lookup supplier data by TIN"""
        if not self.db_connection:
            return None
        
        try:
            query = """
            SELECT name, address, phone, email, registration_number
            FROM suppliers 
            WHERE tin = %s
            """
            # Execute query and return results
            return {
                "name": "Sample Supplier Name",
                "address": "Sample Supplier Address",
                "phone": "+234-XXX-XXXX",
                "email": "supplier@example.com",
                "registration_number": "RC123456"
            }
        except Exception as e:
            logger.error(f"Database lookup error for supplier TIN {tin}: {str(e)}")
            return None
    
    async def lookup_product_data(self, product_code: str) -> Optional[Dict[str, Any]]:
        """Lookup product data by code"""
        if not self.db_connection:
            return None
        
        try:
            query = """
            SELECT name, description, unit_price, tax_rate, category
            FROM products 
            WHERE code = %s
            """
            return {
                "name": "Sample Product",
                "description": "Sample Product Description",
                "unit_price": 100.0,
                "tax_rate": 7.5,
                "category": "Goods"
            }
        except Exception as e:
            logger.error(f"Database lookup error for product {product_code}: {str(e)}")
            return None


class ExternalAPIService:
    """Service for external API enrichment"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def lookup_business_registry(self, tin: str) -> Optional[Dict[str, Any]]:
        """Lookup business information from external registry"""
        if not self.session:
            return None
        
        try:
            # This would be actual API call to business registry
            # url = f"https://api.cac.gov.ng/business/{tin}"
            # async with self.session.get(url) as response:
            #     if response.status == 200:
            #         return await response.json()
            
            # Simulated response
            return {
                "business_name": "Sample Business Ltd",
                "registration_status": "Active",
                "registration_date": "2020-01-01",
                "business_type": "Limited Liability Company",
                "address": "Sample Business Address"
            }
        except Exception as e:
            logger.error(f"External API lookup error for TIN {tin}: {str(e)}")
            return None
    
    async def lookup_currency_rates(self, base_currency: str, target_currency: str) -> Optional[float]:
        """Lookup current currency exchange rates"""
        if not self.session:
            return None
        
        try:
            # This would be actual API call to currency service
            # url = f"https://api.exchangerate.com/v1/latest/{base_currency}"
            # async with self.session.get(url) as response:
            #     if response.status == 200:
            #         data = await response.json()
            #         return data.get("rates", {}).get(target_currency)
            
            # Simulated response
            rates = {
                "USD": 415.0,  # NGN to USD
                "EUR": 450.0,  # NGN to EUR
                "GBP": 520.0   # NGN to GBP
            }
            return rates.get(target_currency, 1.0)
        except Exception as e:
            logger.error(f"Currency lookup error {base_currency} to {target_currency}: {str(e)}")
            return None


class CalculationEngine:
    """Engine for calculated value enrichment"""
    
    @staticmethod
    def calculate_tax_amount(base_amount: float, tax_rate: float) -> float:
        """Calculate tax amount from base amount and rate"""
        return (base_amount * tax_rate) / 100
    
    @staticmethod
    def calculate_total_amount(base_amount: float, tax_amount: float, discount: float = 0) -> float:
        """Calculate total amount"""
        return base_amount + tax_amount - discount
    
    @staticmethod
    def calculate_due_date(invoice_date: str, payment_terms_days: int = 30) -> str:
        """Calculate due date from invoice date and payment terms"""
        try:
            invoice_dt = datetime.strptime(invoice_date, "%Y-%m-%d")
            due_dt = invoice_dt + timedelta(days=payment_terms_days)
            return due_dt.strftime("%Y-%m-%d")
        except ValueError:
            return invoice_date
    
    @staticmethod
    def calculate_line_total(quantity: float, unit_price: float, tax_rate: float = 0) -> Dict[str, float]:
        """Calculate line item totals"""
        subtotal = quantity * unit_price
        tax_amount = CalculationEngine.calculate_tax_amount(subtotal, tax_rate)
        total = subtotal + tax_amount
        
        return {
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total": total
        }
    
    @staticmethod
    def infer_payment_terms(customer_type: str, invoice_amount: float) -> str:
        """Infer payment terms based on customer type and amount"""
        if customer_type == "government":
            return "Net 60"
        elif customer_type == "corporate" and invoice_amount > 1000000:
            return "Net 45"
        elif customer_type == "sme":
            return "Net 30"
        else:
            return "Net 15"


class InferenceEngine:
    """Engine for intelligent data inference"""
    
    @staticmethod
    def infer_business_type(business_name: str) -> str:
        """Infer business type from business name"""
        name_lower = business_name.lower()
        
        if "limited" in name_lower or "ltd" in name_lower:
            return "Limited Company"
        elif "plc" in name_lower:
            return "Public Limited Company"
        elif "enterprises" in name_lower or "ent" in name_lower:
            return "Enterprise"
        elif "nig" in name_lower or "nigeria" in name_lower:
            return "Nigerian Company"
        else:
            return "Business Entity"
    
    @staticmethod
    def infer_currency_from_country(country: str) -> str:
        """Infer currency from country"""
        currency_map = {
            "nigeria": "NGN",
            "united states": "USD",
            "usa": "USD",
            "united kingdom": "GBP",
            "uk": "GBP",
            "germany": "EUR",
            "france": "EUR",
            "italy": "EUR",
            "spain": "EUR"
        }
        return currency_map.get(country.lower(), "NGN")
    
    @staticmethod
    def infer_invoice_type(line_items: List[Dict[str, Any]]) -> str:
        """Infer invoice type from line items"""
        if not line_items:
            return "standard"
        
        # Check for service indicators
        services_count = 0
        goods_count = 0
        
        for item in line_items:
            description = item.get("description", "").lower()
            if any(keyword in description for keyword in ["service", "consultation", "fee", "charge"]):
                services_count += 1
            else:
                goods_count += 1
        
        if services_count > goods_count:
            return "service"
        elif goods_count > 0:
            return "goods"
        else:
            return "standard"


class DataEnricher:
    """Main service for data enrichment"""
    
    def __init__(self, db_connection=None):
        self.db_lookup = DatabaseLookupService(db_connection)
        self.calculation_engine = CalculationEngine()
        self.inference_engine = InferenceEngine()
        self.enrichment_rules: List[EnrichmentRule] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default enrichment rules"""
        self.enrichment_rules = [
            # Customer data enrichment
            EnrichmentRule(
                field_name="customer_name",
                source=EnrichmentSource.DATABASE_LOOKUP,
                priority=1,
                lookup_key="customer_tin",
                required=True
            ),
            EnrichmentRule(
                field_name="customer_address",
                source=EnrichmentSource.DATABASE_LOOKUP,
                priority=2,
                lookup_key="customer_tin"
            ),
            
            # Supplier data enrichment
            EnrichmentRule(
                field_name="supplier_name",
                source=EnrichmentSource.DATABASE_LOOKUP,
                priority=1,
                lookup_key="supplier_tin",
                required=True
            ),
            
            # Currency and amounts
            EnrichmentRule(
                field_name="currency_code",
                source=EnrichmentSource.DEFAULT_VALUES,
                priority=3,
                default_value="NGN"
            ),
            EnrichmentRule(
                field_name="tax_amount",
                source=EnrichmentSource.CALCULATED_VALUES,
                priority=2,
                calculation_function="calculate_tax_amount"
            ),
            EnrichmentRule(
                field_name="total_amount",
                source=EnrichmentSource.CALCULATED_VALUES,
                priority=2,
                calculation_function="calculate_total_amount"
            ),
            
            # Dates
            EnrichmentRule(
                field_name="due_date",
                source=EnrichmentSource.CALCULATED_VALUES,
                priority=3,
                calculation_function="calculate_due_date"
            ),
            
            # Inference
            EnrichmentRule(
                field_name="invoice_type",
                source=EnrichmentSource.INFERENCE_ENGINE,
                priority=4,
                calculation_function="infer_invoice_type"
            )
        ]
    
    def add_enrichment_rule(self, rule: EnrichmentRule):
        """Add custom enrichment rule"""
        self.enrichment_rules.append(rule)
        # Sort by priority
        self.enrichment_rules.sort(key=lambda x: x.priority)
    
    async def enrich_customer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich customer-related data"""
        enriched = data.copy()
        enrichment_log = []
        
        customer_tin = data.get("customer_tin")
        if customer_tin and not data.get("customer_name"):
            customer_data = await self.db_lookup.lookup_customer_data(customer_tin)
            if customer_data:
                enriched.update({
                    "customer_name": customer_data.get("name"),
                    "customer_address": customer_data.get("address"),
                    "customer_phone": customer_data.get("phone"),
                    "customer_email": customer_data.get("email")
                })
                enrichment_log.append({"field": "customer_data", "source": "database_lookup"})
        
        # External API enrichment
        async with ExternalAPIService() as api_service:
            if customer_tin:
                business_info = await api_service.lookup_business_registry(customer_tin)
                if business_info and not enriched.get("customer_business_type"):
                    enriched["customer_business_type"] = business_info.get("business_type")
                    enrichment_log.append({"field": "customer_business_type", "source": "external_api"})
        
        return enriched
    
    async def enrich_line_items(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich line item data"""
        enriched_items = []
        
        for item in line_items:
            enriched_item = item.copy()
            
            # Calculate missing totals
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            tax_rate = item.get("tax_rate", 7.5)  # Default VAT rate
            
            if quantity and unit_price:
                calculations = self.calculation_engine.calculate_line_total(
                    quantity, unit_price, tax_rate
                )
                
                if not item.get("subtotal"):
                    enriched_item["subtotal"] = calculations["subtotal"]
                if not item.get("tax_amount"):
                    enriched_item["tax_amount"] = calculations["tax_amount"]
                if not item.get("total"):
                    enriched_item["total"] = calculations["total"]
            
            # Lookup product data if product code exists
            product_code = item.get("product_code")
            if product_code and not item.get("description"):
                product_data = await self.db_lookup.lookup_product_data(product_code)
                if product_data:
                    enriched_item.update({
                        "description": product_data.get("description"),
                        "category": product_data.get("category")
                    })
            
            enriched_items.append(enriched_item)
        
        return enriched_items
    
    async def enrich_amounts(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich amount-related data"""
        enriched = data.copy()
        
        # Calculate missing tax amount
        if not data.get("tax_amount") and data.get("base_amount") and data.get("tax_rate"):
            enriched["tax_amount"] = self.calculation_engine.calculate_tax_amount(
                data["base_amount"], data["tax_rate"]
            )
        
        # Calculate missing total amount
        base_amount = enriched.get("base_amount", 0)
        tax_amount = enriched.get("tax_amount", 0)
        discount = enriched.get("discount_amount", 0)
        
        if not data.get("total_amount") and (base_amount or tax_amount):
            enriched["total_amount"] = self.calculation_engine.calculate_total_amount(
                base_amount, tax_amount, discount
            )
        
        return enriched
    
    async def enrich_dates(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich date-related data"""
        enriched = data.copy()
        
        # Calculate due date if missing
        if not data.get("due_date") and data.get("invoice_date"):
            payment_terms = data.get("payment_terms", "Net 30")
            # Extract days from payment terms
            days = 30  # default
            if "net" in payment_terms.lower():
                try:
                    days = int(payment_terms.lower().replace("net", "").strip())
                except ValueError:
                    pass
            
            enriched["due_date"] = self.calculation_engine.calculate_due_date(
                data["invoice_date"], days
            )
        
        return enriched
    
    async def apply_inference(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply intelligent inference to fill missing data"""
        enriched = data.copy()
        
        # Infer business type from name
        customer_name = data.get("customer_name", "")
        if customer_name and not data.get("customer_business_type"):
            enriched["customer_business_type"] = self.inference_engine.infer_business_type(customer_name)
        
        # Infer currency from country
        country = data.get("customer_address", {}).get("country", "Nigeria")
        if not data.get("currency_code"):
            enriched["currency_code"] = self.inference_engine.infer_currency_from_country(country)
        
        # Infer invoice type
        line_items = data.get("line_items", [])
        if not data.get("invoice_type"):
            enriched["invoice_type"] = self.inference_engine.infer_invoice_type(line_items)
        
        # Infer payment terms
        customer_type = enriched.get("customer_business_type", "").lower()
        total_amount = data.get("total_amount", 0)
        if not data.get("payment_terms"):
            enriched["payment_terms"] = self.calculation_engine.infer_payment_terms(
                customer_type, total_amount
            )
        
        return enriched
    
    async def enrich_data(self, data: Dict[str, Any]) -> EnrichmentResult:
        """Main method to enrich invoice data"""
        logger.info("Starting data enrichment process")
        
        enrichment_log = []
        errors = []
        enriched_data = data.copy()
        
        try:
            # Step 1: Enrich customer data
            enriched_data = await self.enrich_customer_data(enriched_data)
            enrichment_log.append({"step": "customer_enrichment", "status": "completed"})
            
            # Step 2: Enrich line items
            if "line_items" in enriched_data:
                enriched_data["line_items"] = await self.enrich_line_items(enriched_data["line_items"])
                enrichment_log.append({"step": "line_items_enrichment", "status": "completed"})
            
            # Step 3: Enrich amounts
            enriched_data = await self.enrich_amounts(enriched_data)
            enrichment_log.append({"step": "amounts_enrichment", "status": "completed"})
            
            # Step 4: Enrich dates
            enriched_data = await self.enrich_dates(enriched_data)
            enrichment_log.append({"step": "dates_enrichment", "status": "completed"})
            
            # Step 5: Apply inference
            enriched_data = await self.apply_inference(enriched_data)
            enrichment_log.append({"step": "inference", "status": "completed"})
            
            logger.info("Data enrichment completed successfully")
            
            return EnrichmentResult(
                original_data=data,
                enriched_data=enriched_data,
                enrichment_log=enrichment_log,
                success=True,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Data enrichment failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            return EnrichmentResult(
                original_data=data,
                enriched_data=enriched_data,
                enrichment_log=enrichment_log,
                success=False,
                errors=errors
            )
    
    def get_enrichment_summary(self, result: EnrichmentResult) -> Dict[str, Any]:
        """Get summary of enrichment operations"""
        original_fields = set(result.original_data.keys())
        enriched_fields = set(result.enriched_data.keys())
        
        added_fields = enriched_fields - original_fields
        modified_fields = []
        
        for field in original_fields:
            if (field in result.enriched_data and 
                result.original_data[field] != result.enriched_data[field]):
                modified_fields.append(field)
        
        return {
            "success": result.success,
            "total_fields_original": len(original_fields),
            "total_fields_enriched": len(enriched_fields),
            "fields_added": list(added_fields),
            "fields_modified": modified_fields,
            "enrichment_steps": len(result.enrichment_log),
            "errors": result.errors
        }